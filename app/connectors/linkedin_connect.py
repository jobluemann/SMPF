# SMPF — app/connectors/linkedin_connect.py — 2026-09-20
"""LinkedIn connector — OAuth2 connect flow + member and organization (company page) posting.

App: LinkedIn developer app for SMPF. Required products:
  - Share on LinkedIn (w_member_social)
  - Sign In with LinkedIn using OpenID Connect (openid profile email)

Identity discovery prefers OpenID /v2/userinfo and falls back to legacy
/v2/me only if older scopes were granted. Posting uses organization URN if set, otherwise falls back to person URN.
Tokens are stored per local_user_id in data/linkedin_connections.json.
"""
import json
import os
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import requests

from app.config import (
    LINKEDIN_CLIENT_ID,
    LINKEDIN_CLIENT_SECRET,
    LINKEDIN_CALLBACK_URL,
    DATA_DIR,
    LINKEDIN_ORGANIZATION_URN,
)

AUTHORIZE_URL = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
API_BASE = "https://api.linkedin.com/v2"

# OpenID scopes are required for /v2/userinfo person discovery.
# w_member_social is required for member and organization (company page) posting.
SCOPES = os.getenv("LINKEDIN_SCOPES", "openid profile email w_member_social").split()

CONNECTIONS_PATH = os.path.join(DATA_DIR, "linkedin_connections.json")


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
    if not LINKEDIN_CLIENT_ID or not LINKEDIN_CLIENT_SECRET:
        raise RuntimeError("LINKEDIN_CLIENT_ID / LINKEDIN_CLIENT_SECRET not set in .env")

    params = {
        "response_type": "code",
        "client_id": LINKEDIN_CLIENT_ID,
        "redirect_uri": LINKEDIN_CALLBACK_URL,
        "state": state,
        "scope": " ".join(SCOPES),
    }
    return f"{AUTHORIZE_URL}?{urlencode(params)}"


def exchange_code_for_token(code: str) -> dict:
    resp = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": LINKEDIN_CALLBACK_URL,
            "client_id": LINKEDIN_CLIENT_ID,
            "client_secret": LINKEDIN_CLIENT_SECRET,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=20,
    )
    resp.raise_for_status()
    return resp.json()


def discover_identity(access_token: str) -> dict:
    """Identity via OpenID /v2/userinfo (preferred), fallback to /v2/me."""
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        resp = requests.get(f"{API_BASE}/userinfo", headers=headers, timeout=20)
        if resp.ok:
            data = resp.json()
            sub = data.get("sub")
            if sub:
                return {
                    "person_id": sub,
                    "person_urn": f"urn:li:person:{sub}",
                    "first_name": data.get("given_name"),
                    "last_name": data.get("family_name"),
                    "email": data.get("email"),
                    "identity_source": "userinfo",
                }
    except requests.RequestException:
        pass

    # Fallback: legacy /v2/me (only available if legacy scopes were granted).
    resp = requests.get(
        f"{API_BASE}/me",
        params={"projection": "(id,localizedFirstName,localizedLastName)"},
        headers=headers,
        timeout=20,
    )
    resp.raise_for_status()
    data = resp.json()
    return {
        "person_id": data.get("id"),
        "person_urn": f"urn:li:person:{data.get('id')}" if data.get("id") else None,
        "first_name": data.get("localizedFirstName"),
        "last_name": data.get("localizedLastName"),
        "identity_source": "v2me",
    }


def complete_connect_flow(local_user_id: str, code: str) -> dict:
    token = exchange_code_for_token(code)
    access_token = token["access_token"]
    expires_in = int(token.get("expires_in", 5184000))

    identity = {}
    identity_error = None
    try:
        identity = discover_identity(access_token)
    except Exception as exc:
        identity_error = f"{type(exc).__name__}: {exc}"

    connections = _load_connections()
    connections[local_user_id] = {
        "platform": "linkedin",
        "access_token": access_token,
        "expires_at": (datetime.now(timezone.utc) + timedelta(seconds=expires_in)).isoformat(),
        "scopes_granted": SCOPES,
        "identity": identity,
        "identity_error": identity_error,
        "status": "connected",
    }
    _save_connections(connections)

    result = {"status": "connected", "expires_in": expires_in}
    if identity:
        result["identity"] = identity
    if identity_error:
        result["identity_error"] = identity_error
    return result


def get_connection_status(local_user_id: str) -> dict:
    conn = _load_connections().get(local_user_id)
    if not conn or conn.get("status") != "connected":
        return {"status": "not_connected"}
    status = {"status": "connected", "platform": "linkedin"}
    if conn.get("identity"):
        status["identity"] = conn["identity"]
    if conn.get("identity_error"):
        status["identity_error"] = conn["identity_error"]
    return status


def disconnect(local_user_id: str) -> dict:
    connections = _load_connections()
    if local_user_id in connections:
        del connections[local_user_id]
        _save_connections(connections)
    return {"status": "disconnected"}


def _headers(local_user_id: str) -> dict:
    conn = _load_connections().get(local_user_id)
    if not conn or conn.get("status") != "connected":
        raise RuntimeError("LinkedIn not connected for this user")
    return {
        "Authorization": f"Bearer {conn['access_token']}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }


def _author_urn(local_user_id: str) -> str:
    conn = _load_connections().get(local_user_id) or {}
    identity = conn.get("identity") or {}
    person_urn = identity.get("person_urn")
    if not person_urn:
        raise RuntimeError(
            "No LinkedIn person URN stored — enable Sign In with LinkedIn "
            "using OpenID Connect and reconnect."
        )
    return person_urn


def post_text(local_user_id: str, text: str) -> dict:
    payload = {
        "author": _author_urn(local_user_id),
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }
    try:
        resp = requests.post(
            f"{API_BASE}/ugcPosts",
            headers=_headers(local_user_id),
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        return {"status": "posted", "post_urn": resp.headers.get("x-restli-id")}
    except requests.HTTPError as exc:
        return {"status": "error", "error": f"LinkedIn API error: {exc.response.text[:300]}"}
    except Exception as exc:
        return {"status": "error", "error": f"Post failed: {type(exc).__name__}: {exc}"}


def register_image_upload(local_user_id: str) -> dict:
    payload = {
        "registerUploadRequest": {
            "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
            "owner": _author_urn(local_user_id),
            "serviceRelationships": [
                {
                    "relationshipType": "OWNER",
                    "identifier": "urn:li:userGeneratedContent",
                }
            ],
        }
    }
    resp = requests.post(
        f"{API_BASE}/assets?action=registerUpload",
        headers=_headers(local_user_id),
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    upload_url = data["value"]["uploadMechanism"][
        "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"
    ]["uploadUrl"]
    asset_urn = data["value"]["asset"]
    return {"upload_url": upload_url, "asset_urn": asset_urn}


def upload_image_binary(local_user_id: str, upload_url: str, image_path: str) -> None:
    with open(image_path, "rb") as f:
        image_data = f.read()
    resp = requests.put(
        upload_url,
        data=image_data,
        headers={
            "Authorization": _headers(local_user_id)["Authorization"],
            "Content-Type": "application/octet-stream",
        },
        timeout=60,
    )
    resp.raise_for_status()


def post_image(local_user_id: str, image_path: str, caption: str = "") -> dict:
    try:
        reg = register_image_upload(local_user_id)
        upload_image_binary(local_user_id, reg["upload_url"], image_path)

        payload = {
            "author": _author_urn(local_user_id),
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": caption},
                    "shareMediaCategory": "IMAGE",
                    "media": [
                        {
                            "status": "READY",
                            "description": {"text": caption},
                            "media": reg["asset_urn"],
                            "title": {"text": caption[:200]},
                        }
                    ],
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
        }
        resp = requests.post(
            f"{API_BASE}/ugcPosts",
            headers=_headers(local_user_id),
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        return {"status": "posted", "post_urn": resp.headers.get("x-restli-id")}
    except requests.HTTPError as exc:
        return {"status": "error", "error": f"LinkedIn image error: {exc.response.text[:300]}"}
    except Exception as exc:
        return {"status": "error", "error": f"Image post failed: {type(exc).__name__}: {exc}"}


def validate_connection(local_user_id: str) -> dict:
    """Validate LinkedIn token by calling /v2/userinfo."""
    conn = _load_connections().get(local_user_id)
    if not conn or conn.get("status") != "connected":
        return {"status": "not_connected", "platform": "linkedin"}
    access_token = conn.get("access_token")
    if not access_token:
        return {"status": "error", "platform": "linkedin", "error": "no access_token"}
    try:
        resp = requests.get(
            f"{API_BASE}/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        if resp.ok:
            data = resp.json()
            return {"status": "ok", "platform": "linkedin", "name": data.get("name")}
        # If userinfo fails, try legacy /v2/me
        resp2 = requests.get(
            f"{API_BASE}/me?projection=(id,localizedFirstName,localizedLastName)",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        if resp2.ok:
            data = resp2.json()
            name = f"{data.get('localizedFirstName','')} {data.get('localizedLastName','')}".strip()
            return {"status": "ok", "platform": "linkedin", "name": name or "LinkedIn User"}
        return {"status": "error", "platform": "linkedin", "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
    except Exception as exc:
        return {"status": "error", "platform": "linkedin", "error": str(exc)}

