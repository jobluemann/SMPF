# SMPF v1 — app/connectors/instagram_connect.py — 2026-08-24
"""Instagram 'connect your account' flow — DIRECT login, no Facebook needed.

This is a completely separate Meta product from meta_connect.py:
"Instagram API with Instagram Login" (developers.facebook.com/docs/
instagram-platform/instagram-api-with-instagram-login). Different app
credential, different login page (instagram.com, not facebook.com),
different token endpoints entirely.

Built specifically for accounts with real Instagram presence but no
Facebook account/Page — meta_connect.py requires a Facebook Page,
which doesn't work for that case at all.

Scope requested is instagram_business_basic only — read/discovery
level. NOT instagram_business_manage_comments or
instagram_business_manage_messages, which are write-level. Same rule
as every connector here: reaches CONNECTED and stops, no posting.

*** NOT YET LIVE-TESTED *** — built from Meta's documented endpoints
for this specific product, matches the exact scope name seen in your
own app's "Add required permissions" screen. High confidence, but
this sandbox can't reach instagram.com to prove it end to end — you're
the first real test.
"""
import json
import os
from urllib.parse import urlencode

import requests

from app.config import INSTAGRAM_APP_ID, INSTAGRAM_APP_SECRET, INSTAGRAM_CALLBACK_URL, DATA_DIR

AUTHORIZE_URL = "https://www.instagram.com/oauth/authorize"
TOKEN_URL = "https://api.instagram.com/oauth/access_token"
LONG_LIVED_URL = "https://graph.instagram.com/access_token"
ME_URL = "https://graph.instagram.com/v21.0/me"

# Read-only discovery scope only.
SCOPES = ["instagram_business_basic"]

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
    """Build the URL the client visits to log in with Instagram directly."""
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
    """Step 2a: trade the code for a short-lived access token."""
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
    resp.raise_for_status()
    return resp.json()  # {"access_token": ..., "user_id": ...}


def get_long_lived_token(short_lived_token: str) -> dict:
    """Instagram's short-lived tokens expire in ~1 hour. Exchange for a
    long-lived one (~60 days) so the client doesn't have to reconnect
    constantly."""
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
    """Look up the connected account's Instagram username."""
    resp = requests.get(
        ME_URL,
        params={"fields": "id,username", "access_token": access_token},
        timeout=20,
    )
    resp.raise_for_status()
    data = resp.json()
    return {"user_id": data.get("id"), "username": data.get("username")}


def complete_connect_flow(local_user_id: str, code: str) -> dict:
    """Full step 2: code -> short token -> long-lived token -> discover identity -> store."""
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

    return {"status": "connected", "username": identity.get("username")}


def get_connection_status(local_user_id: str) -> dict:
    connections = _load_connections()
    conn = connections.get(local_user_id)
    if not conn:
        return {"status": "not_connected"}
    return {"status": conn["status"], "identity": conn.get("identity")}


def disconnect(local_user_id: str) -> dict:
    connections = _load_connections()
    if local_user_id in connections:
        del connections[local_user_id]
        _save_connections(connections)
    return {"status": "disconnected"}
