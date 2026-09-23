# SMPF v3 — app/connectors/threads_connect.py — 2026-09-20
from __future__ import annotations

"""Threads connector — separate Threads app credentials.

Posting flow is two-step:
  1. POST /{threads-user-id}/threads           -> create media container
  2. POST /{threads-user-id}/threads_publish   -> publish creation_id

For image/video containers, Meta recommends waiting for processing before
publishing. This connector polls GET /{container-id}?fields=status,error_message
until FINISHED/ERROR/EXPIRED before calling threads_publish.

Token lifecycle:
  - short-lived token (1h) -> long-lived token (60d) via th_exchange_token
  - long-lived token refresh via th_refresh_token once it is >=24h old and
    before it expires. Refresh is attempted automatically when a stored token
    is inside the refresh window.
"""
import json
import os
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import requests

from app.config import THREADS_APP_ID, THREADS_APP_SECRET, THREADS_CALLBACK_URL, DATA_DIR

AUTHORIZE_URL = os.getenv("THREADS_AUTHORIZE_URL", "https://threads.net/oauth/authorize")
TOKEN_URL = os.getenv("THREADS_TOKEN_URL", "https://graph.threads.net/oauth/access_token")
LONG_LIVED_URL = os.getenv("THREADS_LONG_LIVED_URL", "https://graph.threads.net/access_token")
REFRESH_URL = os.getenv("THREADS_REFRESH_URL", "https://graph.threads.net/refresh_access_token")
GRAPH_BASE = os.getenv("THREADS_API_BASE", "https://graph.threads.net/v1.0").rstrip("/")

# threads_basic = read profile / required for refresh
# threads_content_publish = post content
SCOPES = os.getenv("THREADS_SCOPES", "threads_basic,threads_content_publish").split(",")

CONNECTIONS_PATH = os.path.join(DATA_DIR, "threads_connections.json")
REFRESH_WINDOW_DAYS = int(os.getenv("THREADS_REFRESH_WINDOW_DAYS", "7"))


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


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _iso_after(seconds: int | None) -> str | None:
    if not seconds:
        return None
    return (_utcnow() + timedelta(seconds=int(seconds))).isoformat()


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def get_authorize_url(state: str) -> str:
    if not THREADS_APP_ID or not THREADS_APP_SECRET:
        raise RuntimeError("THREADS_APP_ID / THREADS_APP_SECRET not set in .env")

    params = {
        "client_id": THREADS_APP_ID,
        "redirect_uri": THREADS_CALLBACK_URL,
        "scope": ",".join(SCOPES),
        "response_type": "code",
        "state": state,
    }
    return f"{AUTHORIZE_URL}?{urlencode(params)}"


def exchange_code_for_token(code: str) -> dict:
    resp = requests.post(
        TOKEN_URL,
        data={
            "client_id": THREADS_APP_ID,
            "client_secret": THREADS_APP_SECRET,
            "grant_type": "authorization_code",
            "redirect_uri": THREADS_CALLBACK_URL,
            "code": code,
        },
        timeout=20,
    )
    if not resp.ok:
        print("THREADS API ERROR:", resp.status_code, resp.url.split("?")[0], resp.text, flush=True)
    if not resp.ok:
        print("THREADS API ERROR:", resp.status_code, resp.url.split("?")[0], resp.text, flush=True)
    resp.raise_for_status()
    return resp.json()


def get_long_lived_token(short_lived_token: str) -> dict:
    resp = requests.get(
        LONG_LIVED_URL,
        params={
            "grant_type": "th_exchange_token",
            "client_secret": THREADS_APP_SECRET,
            "access_token": short_lived_token,
        },
        timeout=20,
    )
    if not resp.ok:
        print("THREADS API ERROR:", resp.status_code, resp.url.split("?")[0], resp.text, flush=True)
    if not resp.ok:
        print("THREADS API ERROR:", resp.status_code, resp.url.split("?")[0], resp.text, flush=True)
    resp.raise_for_status()
    return resp.json()


def refresh_long_lived_token(long_lived_token: str) -> dict:
    """Refresh an unexpired long-lived token for another 60 days."""
    resp = requests.get(
        REFRESH_URL,
        params={
            "grant_type": "th_refresh_token",
            "access_token": long_lived_token,
        },
        timeout=20,
    )
    if not resp.ok:
        print("THREADS API ERROR:", resp.status_code, resp.url.split("?")[0], resp.text, flush=True)
    if not resp.ok:
        print("THREADS API ERROR:", resp.status_code, resp.url.split("?")[0], resp.text, flush=True)
    resp.raise_for_status()
    return resp.json()


def discover_profile(access_token: str) -> dict:
    resp = requests.get(
        f"{GRAPH_BASE}/me",
        params={"fields": "id,username,threads_biography", "access_token": access_token},
        timeout=20,
    )
    if not resp.ok:
        print("THREADS API ERROR:", resp.status_code, resp.url.split("?")[0], resp.text, flush=True)
    if not resp.ok:
        print("THREADS API ERROR:", resp.status_code, resp.url.split("?")[0], resp.text, flush=True)
    resp.raise_for_status()
    data = resp.json()
    return {"user_id": data.get("id"), "username": data.get("username")}


def _store_connection(local_user_id: str, access_token: str, expires_in: int | None, profile: dict | None, source: str) -> dict:
    connections = _load_connections()
    obtained_at = _utcnow()
    connections[local_user_id] = {
        "platform": "threads",
        "access_token": access_token,
        "token_type": "bearer",
        "obtained_at": obtained_at.isoformat(),
        "expires_in_seconds": expires_in,
        "expires_at": _iso_after(expires_in),
        "refreshable": True,
        "profile": profile or {},
        "status": "connected",
        "source": source,
    }
    _save_connections(connections)
    return connections[local_user_id]


def complete_connect_flow(local_user_id: str, code: str) -> dict:
    short_lived = exchange_code_for_token(code)
    long_lived = get_long_lived_token(short_lived["access_token"])
    access_token = long_lived["access_token"]
    expires_in = int(long_lived.get("expires_in", 5184000))
    profile = discover_profile(access_token)
    conn = _store_connection(local_user_id, access_token, expires_in, profile, source="oauth")
    return {"status": "connected", "username": profile.get("username"), "expires_at": conn.get("expires_at")}


def store_manual_token(local_user_id: str, access_token: str, expires_in: int | None = None) -> dict:
    """Store a token created via Meta's User Token Generator.

    Useful while the OAuth settings form is unavailable; the token is still
    stored in the same format and can be refreshed before expiry.
    """
    profile = discover_profile(access_token)
    conn = _store_connection(local_user_id, access_token, expires_in, profile, source="manual_token_generator")
    return {"status": "connected", "username": profile.get("username"), "expires_at": conn.get("expires_at")}


def _refresh_connection_if_needed(local_user_id: str, connections: dict | None = None) -> dict | None:
    connections = connections if connections is not None else _load_connections()
    conn = connections.get(local_user_id)
    if not conn or conn.get("status") != "connected":
        return conn

    token = conn.get("access_token")
    if not token:
        return conn

    expires_at = _parse_iso(conn.get("expires_at"))
    obtained_at = _parse_iso(conn.get("obtained_at"))
    now = _utcnow()

    # Do not refresh brand-new tokens; Meta requires tokens to be >=24h old.
    if obtained_at and now < obtained_at + timedelta(hours=24):
        return conn

    should_refresh = False
    if expires_at:
        should_refresh = now >= (expires_at - timedelta(days=REFRESH_WINDOW_DAYS))
    elif conn.get("source") == "manual_token_generator":
        # Manual tokens may not have captured expiry; refresh once old enough.
        should_refresh = True

    if not should_refresh:
        return conn

    try:
        refreshed = refresh_long_lived_token(token)
        new_token = refreshed.get("access_token")
        if not new_token:
            return conn
        expires_in = int(refreshed.get("expires_in", 5184000))
        conn["access_token"] = new_token
        conn["obtained_at"] = now.isoformat()
        conn["expires_in_seconds"] = expires_in
        conn["expires_at"] = _iso_after(expires_in)
        conn["last_refresh_at"] = now.isoformat()
        conn["refresh_error"] = None
        connections[local_user_id] = conn
        _save_connections(connections)
    except Exception as exc:
        conn["last_refresh_attempt_at"] = now.isoformat()
        conn["refresh_error"] = f"{type(exc).__name__}: {exc}"
        connections[local_user_id] = conn
        _save_connections(connections)
    return conn


def refresh_expiring_connections(days: int = REFRESH_WINDOW_DAYS) -> dict:
    """Refresh all stored Threads connections inside the expiry window.

    Intended for a daily cron/scheduler job.
    """
    global REFRESH_WINDOW_DAYS
    old_window = REFRESH_WINDOW_DAYS
    REFRESH_WINDOW_DAYS = days
    results = {}
    try:
        connections = _load_connections()
        for user_id in list(connections.keys()):
            before = (connections.get(user_id) or {}).get("access_token")
            conn = _refresh_connection_if_needed(user_id, connections)
            after = (conn or {}).get("access_token")
            results[user_id] = {
                "status": (conn or {}).get("status", "missing"),
                "refreshed": bool(before and after and before != after),
                "expires_at": (conn or {}).get("expires_at"),
                "refresh_error": (conn or {}).get("refresh_error"),
            }
        return results
    finally:
        REFRESH_WINDOW_DAYS = old_window


def get_connection_status(local_user_id: str) -> dict:
    connections = _load_connections()
    conn = _refresh_connection_if_needed(local_user_id, connections)
    if not conn:
        return {"status": "not_connected"}
    return {
        "status": conn.get("status", "not_connected"),
        "profile": conn.get("profile"),
        "username": conn.get("profile", {}).get("username"),
        "expires_at": conn.get("expires_at"),
        "refresh_error": conn.get("refresh_error"),
    }


def disconnect(local_user_id: str) -> dict:
    connections = _load_connections()
    if local_user_id in connections:
        del connections[local_user_id]
        _save_connections(connections)
    return {"status": "disconnected"}


# ─── Posting ───────────────────────────────────────────────────────────────


def _get_connection(local_user_id: str) -> dict:
    conn = _refresh_connection_if_needed(local_user_id)
    if not conn:
        return {"error": "Threads not connected."}
    token = conn.get("access_token")
    profile = conn.get("profile", {})
    user_id = profile.get("user_id")
    if not token:
        return {"error": "Token missing. Reconnect Threads."}
    return {"token": token, "user_id": user_id or "me", "username": profile.get("username", "unknown")}


def get_container_status(local_user_id: str, creation_id: str) -> dict:
    c = _get_connection(local_user_id)
    if "error" in c:
        return {"status": "error", **c}
    try:
        resp = requests.get(
            f"{GRAPH_BASE}/{creation_id}",
            params={"fields": "status,error_message", "access_token": c["token"]},
            timeout=20,
        )
        if not resp.ok:
            print("THREADS API ERROR:", resp.status_code, resp.url.split("?")[0], resp.text, flush=True)
        if not resp.ok:
            print("THREADS API ERROR:", resp.status_code, resp.url.split("?")[0], resp.text, flush=True)
        resp.raise_for_status()
        return resp.json()
    except requests.HTTPError as exc:
        return {"status": "error", "error": f"Threads status error: {exc.response.text[:300]}"}
    except Exception as exc:
        return {"status": "error", "error": f"Status check failed: {type(exc).__name__}: {exc}"}


def wait_for_container(local_user_id: str, creation_id: str, timeout_seconds: int = 180, poll_seconds: int = 20, initial_delay: int = 5) -> dict:
    """Wait until a media container is FINISHED before publishing."""
    deadline = time.time() + timeout_seconds
    time.sleep(max(0, initial_delay))
    last = {}
    while time.time() < deadline:
        last = get_container_status(local_user_id, creation_id)
        status = last.get("status")
        if status == "FINISHED":
            return {"status": "ready", "container": last}
        if status == "PUBLISHED":
            return {"status": "published", "container": last}
        if status in {"ERROR", "EXPIRED"}:
            return {"status": "error", "container": last, "error": last.get("error_message") or status}
        time.sleep(max(1, poll_seconds))
    return {"status": "timeout", "container": last, "error": "Container still not ready after wait window"}


def _publish_container(c: dict, creation_id: str) -> dict:
    resp = requests.post(
        f"{GRAPH_BASE}/{c['user_id']}/threads_publish",
        data={"creation_id": creation_id, "access_token": c["token"]},
        timeout=30,
    )
    if not resp.ok:
        print("THREADS API ERROR:", resp.status_code, resp.url.split("?")[0], resp.text, flush=True)
    if not resp.ok:
        print("THREADS API ERROR:", resp.status_code, resp.url.split("?")[0], resp.text, flush=True)
    resp.raise_for_status()
    return resp.json()


def post_text(local_user_id: str, text: str) -> dict:
    """Post a text-only thread."""
    c = _get_connection(local_user_id)
    if "error" in c:
        return {"status": "error", **c}

    try:
        resp = requests.post(
            f"{GRAPH_BASE}/{c['user_id']}/threads",
            data={
                "media_type": "TEXT",
                "text": text,
                "access_token": c["token"],
            },
            timeout=20,
        )
        if not resp.ok:
            print("THREADS API ERROR:", resp.status_code, resp.url.split("?")[0], resp.text, flush=True)
        if not resp.ok:
            print("THREADS API ERROR:", resp.status_code, resp.url.split("?")[0], resp.text, flush=True)
        resp.raise_for_status()
        creation_id = resp.json().get("id")
        if not creation_id:
            return {"status": "error", "error": f"No container ID: {resp.text[:300]}"}

        data = _publish_container(c, creation_id)
        return {
            "status": "posted",
            "thread_id": data.get("id"),
            "username": c["username"],
            "text_preview": text[:100],
        }
    except requests.HTTPError as exc:
        return {"status": "error", "error": f"Threads API error: {exc.response.text[:300]}"}
    except Exception as exc:
        return {"status": "error", "error": f"Post failed: {type(exc).__name__}: {exc}"}


def post_image(local_user_id: str, image_url: str, text: str = "", wait: bool = True) -> dict:
    """Post an image thread with optional text.

    Args:
        image_url: PUBLICLY accessible URL (Threads fetches it server-side)
        text: Optional caption/text
        wait: Poll container status until FINISHED before publishing
    """
    c = _get_connection(local_user_id)
    if "error" in c:
        return {"status": "error", **c}

    try:
        resp = requests.post(
            f"{GRAPH_BASE}/{c['user_id']}/threads",
            data={
                "media_type": "IMAGE",
                "image_url": image_url,
                "text": text,
                "access_token": c["token"],
            },
            timeout=30,
        )
        if not resp.ok:
            print("THREADS API ERROR:", resp.status_code, resp.url.split("?")[0], resp.text, flush=True)
        if not resp.ok:
            print("THREADS API ERROR:", resp.status_code, resp.url.split("?")[0], resp.text, flush=True)
        resp.raise_for_status()
        creation_id = resp.json().get("id")
        if not creation_id:
            return {"status": "error", "error": f"No container ID: {resp.text[:300]}"}

        if wait:
            ready = wait_for_container(local_user_id, creation_id)
            if ready.get("status") == "published":
                return {"status": "posted", "thread_id": ready.get("container", {}).get("id"), "username": c["username"], "text_preview": text[:100]}
            if ready.get("status") != "ready":
                return {"status": "error", "error": ready.get("error", "Container not ready"), "container": ready.get("container")}

        data = _publish_container(c, creation_id)
        return {
            "status": "posted",
            "thread_id": data.get("id"),
            "username": c["username"],
            "text_preview": text[:100],
        }
    except requests.HTTPError as exc:
        return {"status": "error", "error": f"Threads API error: {exc.response.text[:300]}"}
    except Exception as exc:
        return {"status": "error", "error": f"Post failed: {type(exc).__name__}: {exc}"}


def validate_connection(local_user_id: str) -> dict:
    """Validate Threads token by calling /me."""
    conn = _load_connections().get(local_user_id)
    if not conn or conn.get("status") != "connected":
        return {"status": "not_connected", "platform": "threads"}
    try:
        resp = requests.get(
            f"https://graph.threads.net/v1.0/me?access_token={conn['access_token']}",
            timeout=10,
        )
        if resp.ok:
            data = resp.json()
            return {"status": "ok", "platform": "threads", "username": data.get("username")}
        return {"status": "error", "platform": "threads", "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
    except Exception as exc:
        return {"status": "error", "platform": "threads", "error": str(exc)}

