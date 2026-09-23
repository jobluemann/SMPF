# SMPF v2 — app/connectors/x_connect.py — 2026-09-07
"""X connector — OAuth 1.0a for posting (permanent), OAuth 2.0 for connect flow."""
import base64
import hashlib
import json
import os
import secrets
from urllib.parse import urlencode

import requests
from requests_oauthlib import OAuth1
from PIL import Image

from app.config import (
    X_CLIENT_ID, X_CLIENT_SECRET, X_CALLBACK_URL, DATA_DIR,
    X_OAUTH1_CONSUMER_KEY, X_OAUTH1_CONSUMER_SECRET,
    X_OAUTH1_ACCESS_TOKEN, X_OAUTH1_ACCESS_TOKEN_SECRET,
)

AUTHORIZE_URL = "https://twitter.com/i/oauth2/authorize"
TOKEN_URL = "https://api.twitter.com/2/oauth2/token"
ME_URL = "https://api.twitter.com/2/users/me"

SCOPES = ["tweet.read", "users.read", "offline.access", "tweet.write"]

CONNECTIONS_PATH = os.path.join(DATA_DIR, "x_connections.json")


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
    """Build the URL the client visits to log in and approve access."""
    if not X_CLIENT_ID:
        raise RuntimeError("X_CLIENT_ID not set in .env")

    code_verifier, code_challenge = _generate_pkce_pair()

    params = {
        "response_type": "code",
        "client_id": X_CLIENT_ID,
        "redirect_uri": X_CALLBACK_URL,
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
    auth = None
    if X_CLIENT_SECRET:
        auth = (X_CLIENT_ID, X_CLIENT_SECRET)

    resp = requests.post(
        TOKEN_URL,
        auth=auth,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": X_CALLBACK_URL,
            "code_verifier": code_verifier,
            "client_id": X_CLIENT_ID,
        },
        timeout=20,
    )
    resp.raise_for_status()
    return resp.json()


def discover_identity(access_token: str) -> dict:
    resp = requests.get(
        ME_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=20,
    )
    resp.raise_for_status()
    data = resp.json().get("data", {})
    return {"user_id": data.get("id"), "username": data.get("username"), "name": data.get("name")}


def complete_connect_flow(local_user_id: str, code: str, code_verifier: str) -> dict:
    tokens = exchange_code_for_token(code, code_verifier)
    identity = discover_identity(tokens["access_token"])

    connections = _load_connections()
    connections[local_user_id] = {
        "platform": "x",
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
    if conn:
        return {"status": conn["status"], "identity": conn.get("identity"), "method": "oauth2"}
    # Fallback: check OAuth 1.0a env vars (permanent, never expires)
    if X_OAUTH1_CONSUMER_KEY and X_OAUTH1_ACCESS_TOKEN:
        return {"status": "connected", "identity": {"username": "jobluemann", "user_id": "1183789584511049728"}, "method": "oauth1"}
    return {"status": "not_connected"}


def disconnect(local_user_id: str) -> dict:
    connections = _load_connections()
    if local_user_id in connections:
        del connections[local_user_id]
        _save_connections(connections)
    return {"status": "disconnected"}


def _refresh_access_token(local_user_id: str) -> bool:
    connections = _load_connections()
    conn = connections.get(local_user_id)
    if not conn:
        return False
    refresh_token = conn.get("refresh_token")
    if not refresh_token:
        return False

    auth = None
    if X_CLIENT_SECRET:
        auth = (X_CLIENT_ID, X_CLIENT_SECRET)

    try:
        resp = requests.post(
            TOKEN_URL,
            auth=auth,
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": X_CLIENT_ID,
            },
            timeout=20,
        )
        resp.raise_for_status()
        tokens = resp.json()
        conn["access_token"] = tokens.get("access_token")
        if "refresh_token" in tokens:
            conn["refresh_token"] = tokens["refresh_token"]
        if "expires_in" in tokens:
            conn["expires_in_seconds"] = tokens["expires_in"]
        _save_connections(connections)
        return True
    except Exception:
        return False


# ─── Posting ───────────────────────────────────────────────────────────────

POST_TWEET_URL = "https://api.twitter.com/2/tweets"
UPLOAD_MEDIA_URL = "https://upload.twitter.com/1.1/media/upload.json"


def post_tweet(local_user_id: str, text: str, media_ids: list = None) -> dict:
    """Post a tweet to X.

    Priority: OAuth 1.0a (permanent, never expires) → OAuth 2.0 (fallback).
    OAuth 1.0a is configured via env vars; if present it is used automatically.
    """
    # ── OAuth 1.0a path (preferred — never expires) ──────────────────────
    if X_OAUTH1_CONSUMER_KEY and X_OAUTH1_ACCESS_TOKEN:
        auth = OAuth1(
            X_OAUTH1_CONSUMER_KEY,
            X_OAUTH1_CONSUMER_SECRET,
            X_OAUTH1_ACCESS_TOKEN,
            X_OAUTH1_ACCESS_TOKEN_SECRET,
        )
        payload = {"text": text}
        if media_ids:
            payload["media"] = {"media_ids": media_ids}
        try:
            resp = requests.post(
                POST_TWEET_URL,
                auth=auth,
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=20,
            )
            resp.raise_for_status()
            data = resp.json()
            return {
                "status": "posted",
                "tweet_id": data.get("data", {}).get("id"),
                "text_preview": text[:100],
            }
        except requests.HTTPError as exc:
            return {"status": "error", "error": f"X OAuth 1.0a error: {exc.response.text[:300]}"}
        except Exception as exc:
            return {"status": "error", "error": f"Post failed: {type(exc).__name__}: {exc}"}
    if X_OAUTH1_CONSUMER_KEY and X_OAUTH1_ACCESS_TOKEN:
        auth = OAuth1(
            X_OAUTH1_CONSUMER_KEY,
            X_OAUTH1_CONSUMER_SECRET,
            X_OAUTH1_ACCESS_TOKEN,
            X_OAUTH1_ACCESS_TOKEN_SECRET,
        )
        payload = {"status": text}
        if media_ids:
            payload["media_ids"] = ",".join(media_ids)
        try:
            resp = requests.post(
                "https://api.twitter.com/1.1/statuses/update.json",
                auth=auth,
                data=payload,
                timeout=20,
            )
            resp.raise_for_status()
            data = resp.json()
            return {
                "status": "posted",
                "tweet_id": data.get("id_str"),
                "text_preview": text[:100],
            }
        except requests.HTTPError as exc:
            return {"status": "error", "error": f"X OAuth 1.0a error: {exc.response.text[:300]}"}
        except Exception as exc:
            return {"status": "error", "error": f"Post failed: {type(exc).__name__}: {exc}"}

    # ── OAuth 2.0 fallback (short-lived token, may expire) ────────────────
    connections = _load_connections()
    conn = connections.get(local_user_id)
    if not conn:
        return {"status": "error", "error": "X not connected."}

    access_token = conn.get("access_token")
    if not access_token:
        return {"status": "error", "error": "No access token. Reconnect X."}

    payload = {"text": text}
    if media_ids:
        payload["media"] = {"media_ids": media_ids}

    try:
        resp = requests.post(
            POST_TWEET_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=20,
        )
        if resp.status_code == 401:
            if _refresh_access_token(local_user_id):
                access_token = _load_connections()[local_user_id]["access_token"]
                resp = requests.post(
                    POST_TWEET_URL,
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                    timeout=20,
                )
        if resp.status_code == 403:
            return {
                "status": "error",
                "error": "Forbidden — your X token lacks tweet.write scope. Disconnect and reconnect X to grant posting permission.",
            }
        resp.raise_for_status()
        data = resp.json()
        return {
            "status": "posted",
            "tweet_id": data.get("data", {}).get("id"),
            "text_preview": text[:100],
        }
    except requests.HTTPError as exc:
        return {"status": "error", "error": f"X API error: {exc.response.text[:300]}"}
    except Exception as exc:
        return {"status": "error", "error": f"Post failed: {type(exc).__name__}: {exc}"}


def _prepare_image_for_x(media_path: str) -> str:
    """Resize / compress an image so it looks good on X and stays under 5 MB."""
    try:
        img = Image.open(media_path)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.thumbnail((1200, 1200), Image.LANCZOS)
        tmp_path = os.path.join(DATA_DIR, f"tmp_x_resized_{secrets.token_hex(6)}.jpg")
        img.save(tmp_path, "JPEG", quality=85)
        return tmp_path
    except Exception:
        return media_path


def upload_media(local_user_id: str, media_path: str) -> dict:
    """Upload an image or video to X via v1.1 media/upload."""
    prepared_path = _prepare_image_for_x(media_path)

    try:
        with open(prepared_path, "rb") as f:
            if X_OAUTH1_CONSUMER_KEY and X_OAUTH1_ACCESS_TOKEN:
                auth = OAuth1(
                    X_OAUTH1_CONSUMER_KEY,
                    X_OAUTH1_CONSUMER_SECRET,
                    X_OAUTH1_ACCESS_TOKEN,
                    X_OAUTH1_ACCESS_TOKEN_SECRET,
                )
                resp = requests.post(
                    UPLOAD_MEDIA_URL,
                    auth=auth,
                    files={"media": f},
                    timeout=30,
                )
            else:
                connections = _load_connections()
                conn = connections.get(local_user_id)
                if not conn:
                    return {"status": "error", "error": "X not connected."}
                access_token = conn.get("access_token")
                if not access_token:
                    return {"status": "error", "error": "No access token. Reconnect X."}
                resp = requests.post(
                    UPLOAD_MEDIA_URL,
                    headers={"Authorization": f"Bearer {access_token}"},
                    files={"media": f},
                    timeout=30,
                )
        resp.raise_for_status()
        data = resp.json()
        return {"status": "ok", "media_id": data.get("media_id_string")}
    except requests.HTTPError as exc:
        return {"status": "error", "error": f"X media upload error: {exc.response.text[:300]}"}
    except Exception as exc:
        return {"status": "error", "error": f"Media upload failed: {type(exc).__name__}: {exc}"}
    finally:
        if prepared_path != media_path and os.path.exists(prepared_path):
            try:
                os.remove(prepared_path)
            except Exception:
                pass

# Wrapper for client_wrapper compatibility
def post_text(local_user_id: str, text: str) -> dict:
    return post_tweet(local_user_id, text)


def validate_connection(local_user_id: str) -> dict:
    """Validate X token by calling verify_credentials (OAuth 1.0a) or /2/users/me (OAuth 2.0)."""
    connections = _load_connections()
    conn = connections.get(local_user_id)
    if conn and conn.get("status") == "connected" and conn.get("access_token"):
        # OAuth 2.0 token
        try:
            resp = requests.get(
                f"{API_BASE}/2/users/me",
                headers={"Authorization": f"Bearer {conn['access_token']}"},
                timeout=10,
            )
            if resp.ok:
                data = resp.json()
                return {"status": "ok", "platform": "x", "username": data["data"]["username"]}
            return {"status": "error", "platform": "x", "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
        except Exception as exc:
            return {"status": "error", "platform": "x", "error": str(exc)}
    # OAuth 1.0a fallback
    if X_OAUTH1_CONSUMER_KEY and X_OAUTH1_ACCESS_TOKEN:
        try:
            auth = OAuth1(
                X_OAUTH1_CONSUMER_KEY, X_OAUTH1_CONSUMER_SECRET,
                X_OAUTH1_ACCESS_TOKEN, X_OAUTH1_ACCESS_TOKEN_SECRET
            )
            resp = requests.get(
                "https://api.twitter.com/1.1/account/verify_credentials.json",
                auth=auth, timeout=10,
            )
            if resp.ok:
                data = resp.json()
                return {"status": "ok", "platform": "x", "username": data["screen_name"]}
            return {"status": "error", "platform": "x", "error": f"HTTP {resp.status_code}"}
        except Exception as exc:
            return {"status": "error", "platform": "x", "error": str(exc)}
    return {"status": "not_connected", "platform": "x"}

