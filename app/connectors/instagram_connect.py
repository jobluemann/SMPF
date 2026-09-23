# SMPF v4 — app/connectors/instagram_connect.py — 2026-09-07
# Instagram connector — COMPLETELY SEPARATE from Facebook.
# Uses "Instagram API with Instagram Login" — own app, own credentials,
# own login page (instagram.com), own token endpoints.
"""Instagram connector — standalone, no Facebook required.

Different Meta product from meta_connect.py entirely:
"Instagram API with Instagram Login" (developers.facebook.com/docs/
instagram-platform/instagram-api-with-instagram-login).

REQUIREMENTS:
  1. Instagram account MUST be Business or Creator (personal = fails)
  2. App needs instagram_business_content_publish scope for posting
  3. Posting images requires a PUBLIC image_url (Instagram fetches it)

In Meta dev mode (unapproved app), only the app admin/developer can
authorize. That is fine for testing — clients need App Review later.
"""
import json
import os
from urllib.parse import urlencode

import requests

from app.config import (
    DATA_DIR,
    INSTAGRAM_APP_ID,
    INSTAGRAM_APP_SECRET,
    INSTAGRAM_CALLBACK_URL,
)

AUTHORIZE_URL = "https://www.instagram.com/oauth/authorize"
TOKEN_URL = "https://api.instagram.com/oauth/access_token"
LONG_LIVED_URL = "https://graph.instagram.com/access_token"
GRAPH_BASE = "https://graph.instagram.com/v21.0"
ME_URL = f"{GRAPH_BASE}/me"

# instagram_business_basic = read profile
# instagram_business_content_publish = post content
SCOPES = ["instagram_business_basic", "instagram_business_content_publish"]

CONNECTIONS_PATH = os.path.join(DATA_DIR, "instagram_connections.json")


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
    if not INSTAGRAM_APP_ID or not INSTAGRAM_APP_SECRET:
        raise RuntimeError("INSTAGRAM_APP_ID / INSTAGRAM_APP_SECRET not set in .env")

    params = {
        "client_id": INSTAGRAM_APP_ID,
        "redirect_uri": INSTAGRAM_CALLBACK_URL,
        "scope": ",".join(SCOPES),
        "response_type": "code",
        "state": state,
    }
    return f"{AUTHORIZE_URL}?{urlencode(params)}"


def exchange_code_for_token(code: str) -> dict:
    resp = requests.post(
        TOKEN_URL,
        data={
            "client_id": INSTAGRAM_APP_ID,
            "client_secret": INSTAGRAM_APP_SECRET,
            "grant_type": "authorization_code",
            "redirect_uri": INSTAGRAM_CALLBACK_URL,
            "code": code,
        },
        timeout=20,
    )
    if resp.status_code == 400:
        try:
            err = resp.json()
            error_msg = err.get("error_message", err.get("error", "Unknown error"))
            raise RuntimeError(f"Instagram OAuth error: {error_msg}")
        except (ValueError, KeyError):
            resp.raise_for_status()
    resp.raise_for_status()
    return resp.json()


def get_long_lived_token(short_lived_token: str) -> dict:
    resp = requests.get(
        LONG_LIVED_URL,
        params={
            "grant_type": "ig_exchange_token",
            "client_secret": INSTAGRAM_APP_SECRET,
            "access_token": short_lived_token,
        },
        timeout=20,
    )
    resp.raise_for_status()
    return resp.json()


def discover_identity(access_token: str) -> dict:
    resp = requests.get(
        ME_URL,
        params={"fields": "id,username,account_type", "access_token": access_token},
        timeout=20,
    )
    resp.raise_for_status()
    data = resp.json()
    return {
        "user_id": data.get("id"),
        "username": data.get("username"),
        "account_type": data.get("account_type"),
    }


def complete_connect_flow(local_user_id: str, code: str) -> dict:
    short_lived = exchange_code_for_token(code)
    long_lived = get_long_lived_token(short_lived["access_token"])
    access_token = long_lived["access_token"]

    identity = discover_identity(access_token)

    connections = _load_connections()
    connections[local_user_id] = {
        "platform": "instagram",
        "access_token": access_token,
        "expires_in_seconds": long_lived.get("expires_in"),
        "identity": identity,
        "status": "connected",
    }
    _save_connections(connections)

    return {
        "status": "connected",
        "username": identity.get("username"),
        "account_type": identity.get("account_type"),
    }


def get_connection_status(local_user_id: str) -> dict:
    connections = _load_connections()
    conn = connections.get(local_user_id)
    if not conn:
        return {"status": "not_connected"}
    return {
        "status": conn["status"],
        "identity": conn.get("identity"),
        "username": conn.get("identity", {}).get("username"),
    }


def disconnect(local_user_id: str) -> dict:
    connections = _load_connections()
    if local_user_id in connections:
        del connections[local_user_id]
        _save_connections(connections)
    return {"status": "disconnected"}


# ─── Posting ───────────────────────────────────────────────────────────────


def post_image(local_user_id: str, image_url: str, caption: str = "") -> dict:
    """Post a photo to Instagram.

    Instagram REQUIRES a public image_url — it fetches the image from that URL.
    Two steps: create media container → publish.

    Args:
        image_url: PUBLICLY accessible URL of the image (e.g. via Cloudflare tunnel)
        caption: Post caption (hashtags go here)
    """
    connections = _load_connections()
    conn = connections.get(local_user_id)
    if not conn:
        return {"status": "error", "error": "Instagram not connected."}

    token = conn.get("access_token")
    identity = conn.get("identity", {})
    ig_user_id = identity.get("user_id")
    username = identity.get("username", "unknown")

    if not token or not ig_user_id:
        return {"status": "error", "error": "Token or user ID missing. Reconnect Instagram."}

    try:
        # Step 1: Create media container
        resp = requests.post(
            f"{GRAPH_BASE}/{ig_user_id}/media",
            data={
                "image_url": image_url,
                "caption": caption,
                "access_token": token,
            },
            timeout=30,
        )
        resp.raise_for_status()
        container = resp.json()
        creation_id = container.get("id")

        if not creation_id:
            return {"status": "error", "error": f"No container ID returned: {container}"}

        # Step 2: Publish
        resp = requests.post(
            f"{GRAPH_BASE}/{ig_user_id}/media_publish",
            data={
                "creation_id": creation_id,
                "access_token": token,
            },
            timeout=30,
        )
        resp.raise_for_status()
        publish_data = resp.json()

        return {
            "status": "posted",
            "media_id": publish_data.get("id"),
            "username": username,
            "caption_preview": caption[:100],
        }

    except requests.HTTPError as exc:
        return {"status": "error", "error": f"Instagram API error: {exc.response.text[:300]}"}
    except Exception as exc:
        return {"status": "error", "error": f"Post failed: {type(exc).__name__}: {exc}"}


def validate_connection(local_user_id: str) -> dict:
    """Validate Instagram Login token by calling graph.instagram.com/me."""
    conn = _load_connections().get(local_user_id)
    if not conn or conn.get("status") != "connected":
        return {"status": "not_connected", "platform": "instagram"}
    try:
        resp = requests.get(
            "https://graph.instagram.com/me",
            params={"fields": "user_id,username", "access_token": conn.get("access_token", "")},
            timeout=10,
        )
        if resp.ok:
            return {"status": "ok", "platform": "instagram", "name": resp.json().get("username")}
        return {"status": "error", "platform": "instagram", "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
    except Exception as exc:
        return {"status": "error", "platform": "instagram", "error": type(exc).__name__}
