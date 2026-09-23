# SMPF v5 — app/connectors/meta_connect.py — 2026-09-07
"""Facebook connector — standalone, separate from Instagram and Threads.

One Meta app credential (META_APP_ID/SECRET) is used for the OAuth login,
but this connector ONLY handles Facebook Pages. Instagram and Threads are
completely separate connectors with their own connect/disconnect.

REQUIREMENT: User must manage at least one Facebook Page.
Posting uses the Page Access Token (never the User Access Token).
"""
import json
import os
from typing import List
from urllib.parse import urlencode

import requests

from app.config import (
    META_APP_ID, META_APP_SECRET, META_CALLBACK_URL, META_GRAPH_VERSION, DATA_DIR,
)

GRAPH_BASE = f"https://graph.facebook.com/{META_GRAPH_VERSION}"
AUTHORIZE_URL = f"https://www.facebook.com/{META_GRAPH_VERSION}/dialog/oauth"

# pages_manage_posts is REQUIRED for posting to a Page.
# pages_show_list is needed to discover which Pages the user manages.
SCOPES = ["pages_show_list", "pages_manage_posts", "business_management", "instagram_basic", "instagram_content_publish"]

CONNECTIONS_PATH = os.path.join(DATA_DIR, "meta_connections.json")


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
    if not META_APP_ID or not META_APP_SECRET:
        raise RuntimeError("META_APP_ID / META_APP_SECRET not set in .env")

    params = {
        "client_id": META_APP_ID,
        "redirect_uri": META_CALLBACK_URL,
        "state": state,
        "scope": ",".join(SCOPES),
        "response_type": "code",
    }
    return f"{AUTHORIZE_URL}?{urlencode(params)}"


def exchange_code_for_token(code: str) -> dict:
    resp = requests.get(
        f"{GRAPH_BASE}/oauth/access_token",
        params={
            "client_id": META_APP_ID,
            "client_secret": META_APP_SECRET,
            "redirect_uri": META_CALLBACK_URL,
            "code": code,
        },
        timeout=20,
    )
    if resp.status_code == 400:
        try:
            err = resp.json()
            raise RuntimeError(f"Meta OAuth error: {err}")
        except ValueError:
            resp.raise_for_status()
    resp.raise_for_status()
    return resp.json()


def get_long_lived_token(short_lived_token: str) -> dict:
    resp = requests.get(
        f"{GRAPH_BASE}/oauth/access_token",
        params={
            "grant_type": "fb_exchange_token",
            "client_id": META_APP_ID,
            "client_secret": META_APP_SECRET,
            "fb_exchange_token": short_lived_token,
        },
        timeout=20,
    )
    resp.raise_for_status()
    return resp.json()


def discover_pages(access_token: str) -> List[dict]:
    """List Facebook Pages the user manages (with page access tokens)."""
    resp = requests.get(
        f"{GRAPH_BASE}/me/accounts",
        params={
            "access_token": access_token,
            "fields": "id,name,access_token",
        },
        timeout=20,
    )
    resp.raise_for_status()
    pages = resp.json().get("data", [])

    results = []
    for page in pages:
        results.append({
            "facebook_page_id": page.get("id"),
            "facebook_page_name": page.get("name"),
            "page_access_token": page.get("access_token"),
        })
    return results


def complete_connect_flow(local_user_id: str, code: str) -> dict:
    short_lived = exchange_code_for_token(code)
    long_lived = get_long_lived_token(short_lived["access_token"])
    access_token = long_lived["access_token"]

    pages = discover_pages(access_token)

    connections = _load_connections()
    connections[local_user_id] = {
        "platform": "facebook",
        "user_access_token": access_token,
        "expires_in_seconds": long_lived.get("expires_in"),
        "pages": pages,
        "status": "connected",
    }
    _save_connections(connections)

    return {
        "status": "connected",
        "pages_found": len(pages),
        "page_names": [p["facebook_page_name"] for p in pages],
    }


def get_connection_status(local_user_id: str) -> dict:
    connections = _load_connections()
    conn = connections.get(local_user_id)
    if not conn:
        return {"status": "not_connected"}
    pages = conn.get("pages", [])
    return {
        "status": conn["status"],
        "facebook_pages": [p.get("facebook_page_name") for p in pages],
        "page_count": len(pages),
    }


def disconnect(local_user_id: str) -> dict:
    connections = _load_connections()
    if local_user_id in connections:
        del connections[local_user_id]
        _save_connections(connections)
    return {"status": "disconnected"}


# ─── Posting ───────────────────────────────────────────────────────────────


def _get_first_page(local_user_id: str) -> dict:
    """Get the first connected Facebook Page with its token."""
    connections = _load_connections()
    conn = connections.get(local_user_id)
    if not conn:
        return {"error": "Facebook not connected."}
    pages = conn.get("pages", [])
    if not pages:
        return {"error": "No Facebook Pages found. Connect Facebook first."}
    page = pages[0]
    if not page.get("facebook_page_id") or not page.get("page_access_token"):
        return {"error": "Page token missing. Reconnect Facebook."}
    return page


def post_text(local_user_id: str, message: str) -> dict:
    """Post a text update to the first connected Facebook Page."""
    page = _get_first_page(local_user_id)
    if "error" in page:
        return {"status": "error", **page}

    try:
        resp = requests.post(
            f"{GRAPH_BASE}/{page['facebook_page_id']}/feed",
            data={"message": message, "access_token": page["page_access_token"]},
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        return {
            "status": "posted",
            "post_id": data.get("id"),
            "page_name": page["facebook_page_name"],
            "message_preview": message[:100],
        }
    except requests.HTTPError as exc:
        return {"status": "error", "error": f"Facebook API error: {exc.response.text[:300]}"}
    except Exception as exc:
        return {"status": "error", "error": f"Post failed: {type(exc).__name__}: {exc}"}


def post_image(local_user_id: str, image_path: str, caption: str = "") -> dict:
    """Post a photo (with optional caption) to the first connected Facebook Page.

    Uploads the image directly via multipart/form-data — no public URL needed.
    """
    page = _get_first_page(local_user_id)
    if "error" in page:
        return {"status": "error", **page}

    try:
        with open(image_path, "rb") as f:
            resp = requests.post(
                f"{GRAPH_BASE}/{page['facebook_page_id']}/photos",
                data={
                    "caption": caption,
                    "access_token": page["page_access_token"],
                },
                files={"source": f},
                timeout=30,
            )
        resp.raise_for_status()
        data = resp.json()
        return {
            "status": "posted",
            "post_id": data.get("id"),
            "page_name": page["facebook_page_name"],
            "caption_preview": caption[:100],
        }
    except requests.HTTPError as exc:
        return {"status": "error", "error": f"Facebook photo error: {exc.response.text[:300]}"}
    except Exception as exc:
        return {"status": "error", "error": f"Photo post failed: {type(exc).__name__}: {exc}"}


def validate_connection(local_user_id: str) -> dict:
    """Validate Facebook token by calling /me."""
    conn = _load_connections().get(local_user_id)
    if not conn or conn.get("status") != "connected":
        return {"status": "not_connected", "platform": "facebook"}
    try:
        resp = requests.get(
            "https://graph.facebook.com/me",
            params={"access_token": conn.get("user_access_token") or conn.get("access_token", "")},
            timeout=10,
        )
        if resp.ok:
            data = resp.json()
            return {"status": "ok", "platform": "facebook", "name": data.get("name")}
        return {"status": "error", "platform": "facebook", "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
    except Exception as exc:
        return {"status": "error", "platform": "facebook", "error": type(exc).__name__}

