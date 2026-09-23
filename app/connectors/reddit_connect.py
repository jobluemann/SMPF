# SMPF v1 — app/connectors/reddit_connect.py — 2026-08-24
"""Reddit 'connect your account' flow.

Reddit's OAuth is its own thing — token exchange needs HTTP Basic Auth
with the app credentials (not just POST body params like everywhere
else), and every API call needs a real descriptive User-Agent header or
Reddit throttles you hard. Both are handled here.

Scope requested is "identity" only — enough to know who connected.
NOT "submit" (posting) or "read" beyond what identity needs. Same rule
as every connector in this project: reaches CONNECTED and stops.
"""
import json
import os
from base64 import b64encode
from urllib.parse import urlencode

import requests

from app.config import (
    REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_CALLBACK_URL,
    REDDIT_USER_AGENT, DATA_DIR,
)

AUTHORIZE_URL = "https://www.reddit.com/api/v1/authorize"
TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
ME_URL = "https://oauth.reddit.com/api/v1/me"

# identity = who is this. NOT submit (post text/link) or the other
# write scopes. Deliberately minimal for a connect-only flow.
SCOPES = ["identity"]

CONNECTIONS_PATH = os.path.join(DATA_DIR, "reddit_connections.json")


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
    """Build the URL the client visits to log in with Reddit and approve access.

    duration=permanent asks Reddit for a refresh token too, not just a
    1-hour access token — otherwise the client would have to reconnect
    every hour.
    """
    if not REDDIT_CLIENT_ID or not REDDIT_CLIENT_SECRET:
        raise RuntimeError("REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET not set in .env")

    params = {
        "client_id": REDDIT_CLIENT_ID,
        "response_type": "code",
        "state": state,
        "redirect_uri": REDDIT_CALLBACK_URL,
        "duration": "permanent",
        "scope": " ".join(SCOPES),
    }
    return f"{AUTHORIZE_URL}?{urlencode(params)}"


def exchange_code_for_token(code: str) -> dict:
    """Step 2: trade the authorization code for access + refresh tokens.

    Reddit requires HTTP Basic Auth here (client_id:client_secret as the
    Authorization header) — putting them in the POST body like every
    other provider in this project does NOT work for Reddit specifically.
    """
    auth_header = b64encode(f"{REDDIT_CLIENT_ID}:{REDDIT_CLIENT_SECRET}".encode()).decode()

    resp = requests.post(
        TOKEN_URL,
        headers={
            "Authorization": f"Basic {auth_header}",
            "User-Agent": REDDIT_USER_AGENT,
        },
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDDIT_CALLBACK_URL,
        },
        timeout=20,
    )
    resp.raise_for_status()
    return resp.json()  # {"access_token": ..., "refresh_token": ..., "expires_in": ...}


def discover_identity(access_token: str) -> dict:
    """Look up the connected account's Reddit username."""
    resp = requests.get(
        ME_URL,
        headers={
            "Authorization": f"Bearer {access_token}",
            "User-Agent": REDDIT_USER_AGENT,
        },
        timeout=20,
    )
    resp.raise_for_status()
    data = resp.json()
    return {
        "username": data.get("name"),
        "link_karma": data.get("link_karma"),
        "comment_karma": data.get("comment_karma"),
    }


def complete_connect_flow(local_user_id: str, code: str) -> dict:
    """Full step 2: code -> tokens -> discover username -> store."""
    tokens = exchange_code_for_token(code)
    identity = discover_identity(tokens["access_token"])

    connections = _load_connections()
    connections[local_user_id] = {
        "platform": "reddit",
        "access_token": tokens.get("access_token"),
        "refresh_token": tokens.get("refresh_token"),
        "expires_in_seconds": tokens.get("expires_in"),
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

def validate_connection(local_user_id: str) -> dict:
    """Validate Reddit token by calling /api/v1/me."""
    conn = _load_connections().get(local_user_id)
    if not conn or conn.get("status") != "connected":
        return {"status": "not_connected", "platform": "reddit"}
    try:
        resp = requests.get(
            "https://oauth.reddit.com/api/v1/me",
            headers={"Authorization": f"Bearer {conn['access_token']}", "User-Agent": "SMPF/1.0"},
            timeout=10,
        )
        if resp.ok:
            data = resp.json()
            return {"status": "ok", "platform": "reddit", "username": data.get("name")}
        return {"status": "error", "platform": "reddit", "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
    except Exception as exc:
        return {"status": "error", "platform": "reddit", "error": str(exc)}

