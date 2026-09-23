# SMPF v1 — app/integrations/google_drive.py — 2026-08-25
"""Google Drive integration — OAuth 2.0 connect + file upload.

Uses the same Google app credentials as YouTube (GOOGLE_CLIENT_ID etc),
but requests the Google Drive scope so files can be uploaded to the
user's Drive. This is a separate integration from YouTube because the
use-case is different: storing generated content (images, voice, PDFs)
instead of reading a channel.
"""
import json
import os
from typing import Optional
from urllib.parse import urlencode

import requests

from app.config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_CALLBACK_URL, DATA_DIR

# If a dedicated Drive callback is set, use it; otherwise fall back to the
# YouTube callback (they can share because the route path decides what happens).
DRIVE_CALLBACK_URL = os.getenv("GOOGLE_DRIVE_CALLBACK_URL", GOOGLE_CALLBACK_URL)

AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
DRIVE_UPLOAD_URL = "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart"
DRIVE_ABOUT_URL = "https://www.googleapis.com/drive/v3/about"

# drive.file = create/upload files the app itself created.
# drive.readonly.metadata = read file metadata (optional but useful).
SCOPES = [
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo.email",
]

CONNECTIONS_PATH = os.path.join(DATA_DIR, "google_drive_connections.json")


def _load_connections() -> dict:
    if os.path.exists(CONNECTIONS_PATH):
        try:
            with open(CONNECTIONS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_connections(connections: dict):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(CONNECTIONS_PATH, "w", encoding="utf-8") as f:
        json.dump(connections, f, indent=2)


def get_authorize_url(state: str) -> str:
    """Build the URL the client visits to approve Google Drive access."""
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise RuntimeError("GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET not set in .env")

    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": DRIVE_CALLBACK_URL,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    return f"{AUTHORIZE_URL}?{urlencode(params)}"


def exchange_code_for_token(code: str) -> dict:
    """Trade the authorization code for access + refresh tokens."""
    resp = requests.post(
        TOKEN_URL,
        data={
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": DRIVE_CALLBACK_URL,
            "code": code,
            "grant_type": "authorization_code",
        },
        timeout=20,
    )
    resp.raise_for_status()
    return resp.json()


def discover_user_info(access_token: str) -> Optional[dict]:
    """Fetch the connected user's basic profile."""
    resp = requests.get(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=20,
    )
    if resp.status_code != 200:
        return None
    data = resp.json()
    return {"email": data.get("email"), "name": data.get("name"), "picture": data.get("picture")}


def upload_file(access_token: str, file_path: str, mime_type: str, folder_id: Optional[str] = None) -> dict:
    """Upload a local file to Google Drive.

    Args:
        access_token: valid Drive access token.
        file_path: local path to the file.
        mime_type: e.g. image/png, audio/mpeg, application/pdf.
        folder_id: optional Drive folder ID to upload into.

    Returns:
        Drive file metadata dict including id, name, webViewLink.
    """
    from pathlib import Path

    file_name = Path(file_path).name
    file_size = Path(file_path).stat().st_size

    # For small files (< 5 MB) use simple multipart upload
    if file_size < 5 * 1024 * 1024:
        metadata = {"name": file_name}
        if folder_id:
            metadata["parents"] = [folder_id]

        with open(file_path, "rb") as f:
            files = {
                "metadata": ("metadata", json.dumps(metadata), "application/json; charset=UTF-8"),
                "file": (file_name, f, mime_type),
            }
            resp = requests.post(
                DRIVE_UPLOAD_URL,
                headers={"Authorization": f"Bearer {access_token}"},
                files=files,
                timeout=60,
            )
        resp.raise_for_status()
        return resp.json()

    # For larger files, resumable upload would be needed — not implemented here.
    raise NotImplementedError("Files >= 5 MB need resumable upload (not yet implemented).")


def complete_connect_flow(local_user_id: str, code: str) -> dict:
    """Full step 2: code -> tokens -> discover user -> store."""
    tokens = exchange_code_for_token(code)
    user_info = discover_user_info(tokens["access_token"])

    connections = _load_connections()
    connections[local_user_id] = {
        "platform": "google_drive",
        "access_token": tokens.get("access_token"),
        "refresh_token": tokens.get("refresh_token"),
        "expires_in_seconds": tokens.get("expires_in"),
        "user_info": user_info,
        "status": "connected",
    }
    _save_connections(connections)

    return {"status": "connected", "email": user_info.get("email") if user_info else None}


def get_connection_status(local_user_id: str) -> dict:
    connections = _load_connections()
    conn = connections.get(local_user_id)
    if not conn:
        return {"status": "not_connected"}
    return {"status": conn["status"], "user_info": conn.get("user_info")}


def disconnect(local_user_id: str) -> dict:
    connections = _load_connections()
    if local_user_id in connections:
        del connections[local_user_id]
        _save_connections(connections)
    return {"status": "disconnected"}
