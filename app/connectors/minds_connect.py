# SMPF v1 — app/connectors/minds_connect.py — 2026-08-24
"""Minds 'connect your account' flow.

Real OAuth2 API — Minds has a proper developer platform, confirmed
working in the earlier smma-os prototype's minds_publisher.py.

IMPORTANT — verify before going live: this requests NO scope at all
(an unscoped token, read-only by default in the pattern already
confirmed working). The earlier prototype's publish flow used
scope="post" for write access. That scope name should be re-confirmed
against Minds' current developer docs before this connector's flow is
ever extended to request posting access — don't copy "post" in from
memory without checking it's still current.

Same rule as every connector here: reaches CONNECTED and stops.
"""
import json
import os
from urllib.parse import urlencode

import requests

from app.config import MINDS_CLIENT_ID, MINDS_CLIENT_SECRET, MINDS_CALLBACK_URL, DATA_DIR

MINDS_API_BASE = "https://www.minds.com/api/v2"
AUTHORIZE_URL = f"{MINDS_API_BASE}/oauth/authorize"
TOKEN_URL = f"{MINDS_API_BASE}/oauth/token"
ME_URL = f"{MINDS_API_BASE}/channel/me"

CONNECTIONS_PATH = os.path.join(DATA_DIR, "minds_connections.json")


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
    """Build the URL the client visits to log in with Minds and approve access.

    No `scope` param is sent — deliberately minimal, see module docstring.
    """
    if not MINDS_CLIENT_ID or not MINDS_CLIENT_SECRET:
        raise RuntimeError("MINDS_CLIENT_ID / MINDS_CLIENT_SECRET not set in .env")

    params = {
        "client_id": MINDS_CLIENT_ID,
        "redirect_uri": MINDS_CALLBACK_URL,
        "response_type": "code",
        "state": state,
    }
    return f"{AUTHORIZE_URL}?{urlencode(params)}"


def exchange_code_for_token(code: str) -> dict:
    """Step 2: trade the authorization code for an access token."""
    resp = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "client_id": MINDS_CLIENT_ID,
            "client_secret": MINDS_CLIENT_SECRET,
            "redirect_uri": MINDS_CALLBACK_URL,
        },
        timeout=20,
    )
    resp.raise_for_status()
    return resp.json()  # {"access_token": ..., "refresh_token": ..., "expires_in": ...}


def discover_channel(access_token: str) -> dict:
    """Look up the connected account's Minds channel/username."""
    resp = requests.get(
        ME_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=20,
    )
    resp.raise_for_status()
    data = resp.json()
    channel = data.get("channel", data)  # some Minds endpoints nest under "channel"
    return {
        "username": channel.get("username"),
        "subscribers_count": channel.get("subscribers_count"),
    }


def complete_connect_flow(local_user_id: str, code: str) -> dict:
    """Full step 2: code -> token -> discover channel -> store."""
    tokens = exchange_code_for_token(code)
    channel = discover_channel(tokens["access_token"])

    connections = _load_connections()
    connections[local_user_id] = {
        "platform": "minds",
        "access_token": tokens.get("access_token"),
        "refresh_token": tokens.get("refresh_token"),
        "expires_in_seconds": tokens.get("expires_in"),
        "channel": channel,
        "status": "connected",
    }
    _save_connections(connections)

    return {"status": "connected", "username": channel.get("username")}


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
    """Validate Minds token by calling /api/v1/channel/info."""
    conn = _load_connections().get(local_user_id)
    if not conn or conn.get("status") != "connected":
        return {"status": "not_connected", "platform": "minds"}
    try:
        resp = requests.get(
            "https://www.minds.com/api/v1/channel/info",
            headers={"Authorization": f"Bearer {conn['access_token']}"},
            timeout=10,
        )
        if resp.ok:
            return {"status": "ok", "platform": "minds"}
        return {"status": "error", "platform": "minds", "error": f"HTTP {resp.status_code}"}
    except Exception as exc:
        return {"status": "error", "platform": "minds", "error": str(exc)}

