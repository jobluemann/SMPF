# SMPF v1 — app/connectors/youtube_connect.py — 2026-08-24
"""YouTube 'connect your account' flow.

Uses Google's general OAuth 2.0 — same app credential pattern as
Facebook/Instagram. The client logs in on Google's own page.

Requested scope is read-only (youtube.readonly) on purpose. The upload
scope (youtube.upload) is NOT requested, so a connected account here
literally cannot be used to publish a video even by mistake — that
scope gets added later, deliberately, when publishing is actually
being built. Same rule as every other connector in this project: this
file only reaches CONNECTED and stops.
"""
import json
import os
from typing import Optional
from urllib.parse import urlencode

import requests

from app.config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_CALLBACK_URL, DATA_DIR

AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
CHANNELS_URL = "https://www.googleapis.com/youtube/v3/channels"

# Read-only, deliberately. youtube.upload is a separate, later decision.
SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]

CONNECTIONS_PATH = os.path.join(DATA_DIR, "youtube_connections.json")


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
    """Build the URL the client visits to log in with Google and approve access.

    access_type=offline + prompt=consent ensures Google actually issues a
    refresh token (without prompt=consent, a returning user sometimes
    gets no refresh token on repeat authorizations).
    """
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise RuntimeError("GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET not set in .env")

    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_CALLBACK_URL,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    return f"{AUTHORIZE_URL}?{urlencode(params)}"


def exchange_code_for_token(code: str) -> dict:
    """Step 2: trade the authorization code for access + refresh tokens."""
    resp = requests.post(
        TOKEN_URL,
        data={
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": GOOGLE_CALLBACK_URL,
            "code": code,
            "grant_type": "authorization_code",
        },
        timeout=20,
    )
    resp.raise_for_status()
    return resp.json()  # {"access_token": ..., "refresh_token": ..., "expires_in": ...}


def discover_channel(access_token: str) -> Optional[dict]:
    """Look up the connected Google account's own YouTube channel, if it has one."""
    resp = requests.get(
        CHANNELS_URL,
        params={"part": "snippet,statistics", "mine": "true"},
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=20,
    )
    resp.raise_for_status()
    items = resp.json().get("items", [])
    if not items:
        return None

    channel = items[0]
    snippet = channel.get("snippet", {})
    stats = channel.get("statistics", {})
    return {
        "channel_id": channel.get("id"),
        "title": snippet.get("title"),
        "subscriber_count": stats.get("subscriberCount"),
    }


def complete_connect_flow(local_user_id: str, code: str) -> dict:
    """Full step 2: code -> tokens -> discover channel -> store."""
    tokens = exchange_code_for_token(code)
    channel = discover_channel(tokens["access_token"])

    connections = _load_connections()
    connections[local_user_id] = {
        "platform": "youtube",
        "access_token": tokens.get("access_token"),
        "refresh_token": tokens.get("refresh_token"),
        "expires_in_seconds": tokens.get("expires_in"),
        "channel": channel,
        "status": "connected",
    }
    _save_connections(connections)

    return {"status": "connected", "channel_found": channel is not None}


def get_connection_status(local_user_id: str) -> dict:
    connections = _load_connections()
    conn = connections.get(local_user_id)
    if not conn:
        return {"status": "not_connected"}
    return {"status": conn["status"], "channel": conn.get("channel")}


def disconnect(local_user_id: str) -> dict:
    connections = _load_connections()
    if local_user_id in connections:
        del connections[local_user_id]
        _save_connections(connections)
    return {"status": "disconnected"}

def validate_connection(local_user_id: str) -> dict:
    """Validate YouTube token by calling channels.list."""
    conn = _load_connections().get(local_user_id)
    if not conn or conn.get("status") != "connected":
        return {"status": "not_connected", "platform": "youtube"}
    try:
        resp = requests.get(
            f"https://www.googleapis.com/youtube/v3/channels?part=snippet&mine=true&access_token={conn['access_token']}",
            timeout=10,
        )
        if resp.ok:
            data = resp.json()
            items = data.get("items", [])
            name = items[0]["snippet"]["title"] if items else "unknown"
            return {"status": "ok", "platform": "youtube", "channel": name}
        return {"status": "error", "platform": "youtube", "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
    except Exception as exc:
        return {"status": "error", "platform": "youtube", "error": str(exc)}

