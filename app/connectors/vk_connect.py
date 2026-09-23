# SMPF v1 — app/connectors/vk_connect.py — 2026-08-24
"""VK (VKontakte) 'connect your account' flow.

*** VERIFY THIS AGAINST VK'S CURRENT DOCS BEFORE RELYING ON IT ***

VK has been migrating its login system to something called "VK ID"
(at id.vk.com), which several developer reports describe as requiring
PKCE (code_verifier / code_challenge) and an extra `device_id`
parameter that the older flow below doesn't use. Standard OAuth
libraries have been reported breaking against it.

This file is built against the older, more widely documented flow at
oauth.vk.com, which is simpler and still works for many existing VK
apps — but it was NOT verified live (this environment can't reach
vk.com), and it may not match what a newly registered VK app requires
in 2026. Check dev.vk.com's current docs and test this against a real
VK app before trusting it.

Scope requested is empty — no write access, deliberately, same rule
as every connector in this project: reaches CONNECTED and stops.
"""
import json
import os
from urllib.parse import urlencode

import requests

from app.config import VK_CLIENT_ID, VK_CLIENT_SECRET, VK_CALLBACK_URL, DATA_DIR

AUTHORIZE_URL = "https://oauth.vk.com/authorize"
TOKEN_URL = "https://oauth.vk.com/access_token"
USERS_URL = "https://api.vk.com/method/users.get"

# VK's API requires an explicit version on every call. Update this if
# VK deprecates the version below — check dev.vk.com for the current one.
VK_API_VERSION = "5.199"

CONNECTIONS_PATH = os.path.join(DATA_DIR, "vk_connections.json")


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
    """Build the URL the client visits to log in with VK and approve access.

    No scope requested — read-only default access only. VK's write
    scope for posting to a wall is "wall", which is deliberately not
    included here.
    """
    if not VK_CLIENT_ID or not VK_CLIENT_SECRET:
        raise RuntimeError("VK_CLIENT_ID / VK_CLIENT_SECRET not set in .env")

    params = {
        "client_id": VK_CLIENT_ID,
        "redirect_uri": VK_CALLBACK_URL,
        "response_type": "code",
        "state": state,
        "v": VK_API_VERSION,
    }
    return f"{AUTHORIZE_URL}?{urlencode(params)}"


def exchange_code_for_token(code: str) -> dict:
    """Step 2: trade the authorization code for an access token."""
    resp = requests.get(
        TOKEN_URL,
        params={
            "client_id": VK_CLIENT_ID,
            "client_secret": VK_CLIENT_SECRET,
            "redirect_uri": VK_CALLBACK_URL,
            "code": code,
        },
        timeout=20,
    )
    resp.raise_for_status()
    return resp.json()  # {"access_token": ..., "expires_in": ..., "user_id": ...}


def discover_identity(access_token: str, user_id) -> dict:
    """Look up the connected account's VK name."""
    resp = requests.get(
        USERS_URL,
        params={
            "user_ids": user_id,
            "access_token": access_token,
            "v": VK_API_VERSION,
        },
        timeout=20,
    )
    resp.raise_for_status()
    data = resp.json()

    if "error" in data:
        return {"error": data["error"].get("error_msg", "unknown VK API error")}

    users = data.get("response", [])
    if not users:
        return {}

    user = users[0]
    return {
        "user_id": user.get("id"),
        "first_name": user.get("first_name"),
        "last_name": user.get("last_name"),
    }


def complete_connect_flow(local_user_id: str, code: str) -> dict:
    """Full step 2: code -> token -> discover identity -> store."""
    tokens = exchange_code_for_token(code)
    identity = discover_identity(tokens["access_token"], tokens.get("user_id"))

    connections = _load_connections()
    connections[local_user_id] = {
        "platform": "vk",
        "access_token": tokens.get("access_token"),
        "expires_in_seconds": tokens.get("expires_in"),
        "identity": identity,
        "status": "connected",
    }
    _save_connections(connections)

    return {"status": "connected", "identity": identity}


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
    """Validate VK token by calling users.get."""
    conn = _load_connections().get(local_user_id)
    if not conn or conn.get("status") != "connected":
        return {"status": "not_connected", "platform": "vk"}
    try:
        resp = requests.get(
            f"https://api.vk.com/method/users.get?access_token={conn['access_token']}&v=5.131",
            timeout=10,
        )
        if resp.ok:
            data = resp.json()
            if "response" in data:
                return {"status": "ok", "platform": "vk", "username": data["response"][0].get("first_name", "")}
            return {"status": "error", "platform": "vk", "error": data.get("error", {}).get("error_msg", "unknown")}
        return {"status": "error", "platform": "vk", "error": f"HTTP {resp.status_code}"}
    except Exception as exc:
        return {"status": "error", "platform": "vk", "error": str(exc)}

