# SMPF v1 — app/connectors/x_oauth2_connect.py — 2026-08-24
"""X 'connect your account' flow — OAuth 2.0 with PKCE.

This is a SEPARATE flow from x_connect.py (which uses OAuth 1.0a).
Built specifically to test whether the callback/config problem is
particular to OAuth 1.0a, or applies to this X app more broadly.

X's OAuth 2.0 requires PKCE (Proof Key for Code Exchange) — a
code_verifier/code_challenge pair, not just a state token. This module
generates that pair and holds the verifier server-side between the
start and callback steps, same as the request token in the 1.0a flow.

Same rule as every connector here: reaches CONNECTED and stops. No
posting call anywhere in this file.
"""
import base64
import hashlib
import json
import os
import secrets
from urllib.parse import urlencode

import requests

from app.config import (
    X_OAUTH2_CLIENT_ID, X_OAUTH2_CLIENT_SECRET, X_OAUTH2_CALLBACK_URL, DATA_DIR,
)

AUTHORIZE_URL = "https://twitter.com/i/oauth2/authorize"
TOKEN_URL = "https://api.twitter.com/2/oauth2/token"
ME_URL = "https://api.twitter.com/2/users/me"

# offline.access gets a refresh token too, not just a short-lived
# access token — otherwise the client would have to reconnect
# constantly. tweet.read/users.read are the minimum for reading identity.
SCOPES = ["tweet.read", "users.read", "offline.access"]

CONNECTIONS_PATH = os.path.join(DATA_DIR, "x_oauth2_connections.json")


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


def _generate_pkce_pair() -> tuple:
    """Returns (code_verifier, code_challenge). S256 method, as X requires."""
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(64)).decode("utf-8").rstrip("=")
    digest = hashlib.sha256(code_verifier.encode("utf-8")).digest()
    code_challenge = base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")
    return code_verifier, code_challenge


def get_authorize_url(state: str) -> dict:
    """Build the URL the client visits to log in and approve access.

    Returns {"authorize_url": ..., "code_verifier": ...} — the verifier
    must be held onto (e.g. a short-lived server-side dict) until the
    callback step, same pattern as the OAuth 1.0a request token.
    """
    if not X_OAUTH2_CLIENT_ID:
        raise RuntimeError("X_OAUTH2_CLIENT_ID not set in .env")

    code_verifier, code_challenge = _generate_pkce_pair()

    params = {
        "response_type": "code",
        "client_id": X_OAUTH2_CLIENT_ID,
        "redirect_uri": X_OAUTH2_CALLBACK_URL,
        "scope": " ".join(SCOPES),
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    return {
        "authorize_url": f"{AUTHORIZE_URL}?{urlencode(params)}",
        "code_verifier": code_verifier,
    }


def exchange_code_for_token(code: str, code_verifier: str) -> dict:
    """Step 2: trade the authorization code for access + refresh tokens.

    This app is a confidential client (has a client secret), so token
    exchange uses HTTP Basic Auth — X rejects the request otherwise if
    the app is registered as confidential but the secret isn't sent
    this way.
    """
    auth = None
    if X_OAUTH2_CLIENT_SECRET:
        auth = (X_OAUTH2_CLIENT_ID, X_OAUTH2_CLIENT_SECRET)

    resp = requests.post(
        TOKEN_URL,
        auth=auth,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": X_OAUTH2_CALLBACK_URL,
            "code_verifier": code_verifier,
            "client_id": X_OAUTH2_CLIENT_ID,
        },
        timeout=20,
    )
    resp.raise_for_status()
    return resp.json()  # {"access_token": ..., "refresh_token": ..., "expires_in": ...}


def discover_identity(access_token: str) -> dict:
    """Look up the connected account's X username."""
    resp = requests.get(
        ME_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=20,
    )
    resp.raise_for_status()
    data = resp.json().get("data", {})
    return {"user_id": data.get("id"), "username": data.get("username"), "name": data.get("name")}


def complete_connect_flow(local_user_id: str, code: str, code_verifier: str) -> dict:
    """Full step 2: code -> tokens -> discover identity -> store."""
    tokens = exchange_code_for_token(code, code_verifier)
    identity = discover_identity(tokens["access_token"])

    connections = _load_connections()
    connections[local_user_id] = {
        "platform": "x_oauth2",
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
