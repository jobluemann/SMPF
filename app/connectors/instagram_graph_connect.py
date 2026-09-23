# SMPF v2 — app/connectors/instagram_graph_connect.py — 2026-08-27
"""Instagram connector via Facebook Graph API.

This appears as a SEPARATE Instagram connector in the dashboard, but uses
the existing Meta/Facebook connection under the hood. It posts to Instagram
by calling the Facebook Graph API /{page-id}/media endpoint.

REQUIREMENT: The Instagram account MUST be a Business/Creator account AND
it MUST be linked to one of the user's Facebook Pages in Meta Business Suite.

This is how Buffer, Hootsuite, Later, and every professional tool posts to
Instagram — they don't use Instagram's separate Login API at all.
"""
import json
import os
from typing import Optional

import requests

from app.config import DATA_DIR, META_GRAPH_VERSION
from app.connectors import meta_connect

GRAPH_BASE = f"https://graph.facebook.com/{META_GRAPH_VERSION}"
CONNECTIONS_PATH = os.path.join(DATA_DIR, "instagram_graph_connections.json")

# Known fallback mappings for accounts where Meta's API doesn't return
# instagram_business_account due to missing permissions.
# Format: {facebook_page_id: instagram_business_account_id}
_KNOWN_IG_FALLBACK = {
    "101916918609027": "17841421486057784",  # Jo Bluemann page -> @jobluemann
}


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


def _get_meta_token(local_user_id: str) -> Optional[str]:
    """Get the Facebook/Meta access token for this user."""
    meta_conn = meta_connect._load_connections().get(local_user_id)
    if not meta_conn:
        return None
    return meta_conn.get("user_access_token") or meta_conn.get("access_token")


def _get_pages(token: str) -> list:
    """Get Facebook Pages this user manages."""
    resp = requests.get(
        f"{GRAPH_BASE}/me/accounts",
        params={"access_token": token, "fields": "id,name,instagram_business_account"},
        timeout=20,
    )
    resp.raise_for_status()
    data = resp.json()
    return data.get("data", [])


def _get_instagram_accounts(pages: list) -> list:
    """From pages, extract those with linked Instagram Business accounts.
    
    Falls back to KNOWN_IG_FALLBACK for pages where Meta's API doesn't
    return the instagram_business_account field due to missing permissions.
    """
    ig_accounts = []
    for page in pages:
        page_id = page.get("id")
        ig = page.get("instagram_business_account")
        
        # Try API first
        if ig and ig.get("id"):
            ig_accounts.append({
                "page_id": page_id,
                "page_name": page.get("name", ""),
                "instagram_id": ig.get("id"),
                "source": "api",
            })
            continue
        
        # Fallback: known mapping from Meta Business Suite
        if page_id in _KNOWN_IG_FALLBACK:
            ig_accounts.append({
                "page_id": page_id,
                "page_name": page.get("name", ""),
                "instagram_id": _KNOWN_IG_FALLBACK[page_id],
                "source": "fallback",
            })
    
    return ig_accounts


def discover_linked_instagram(local_user_id: str) -> dict:
    """Check if the user's Facebook Pages have linked Instagram accounts."""
    token = _get_meta_token(local_user_id)
    if not token:
        return {"error": "Facebook not connected. Connect Facebook first."}

    try:
        pages = _get_pages(token)
        ig_accounts = _get_instagram_accounts(pages)

        if not ig_accounts:
            return {
                "error": "No Instagram Business account linked to your Facebook Pages. "
                         "Go to business.facebook.com and link your Instagram account to a Page."
            }

        # Store the connection
        connections = _load_connections()
        connections[local_user_id] = {
            "platform": "instagram_graph",
            "status": "connected",
            "instagram_accounts": ig_accounts,
            "meta_user_id": local_user_id,
        }
        _save_connections(connections)

        return {
            "status": "connected",
            "accounts": ig_accounts,
        }

    except requests.HTTPError as exc:
        return {"error": f"Graph API error: {exc.response.text[:200]}"}
    except Exception as exc:
        return {"error": f"Discovery failed: {type(exc).__name__}: {exc}"}


def get_connection_status(local_user_id: str) -> dict:
    connections = _load_connections()
    conn = connections.get(local_user_id)
    if not conn:
        # Check if Facebook is connected — if so, we can discover Instagram
        token = _get_meta_token(local_user_id)
        if token:
            return {"status": "discoverable", "message": "Facebook connected. Click Connect to link Instagram."}
        return {"status": "not_connected"}
    return {"status": conn["status"], "accounts": conn.get("instagram_accounts", [])}


def disconnect(local_user_id: str) -> dict:
    connections = _load_connections()
    if local_user_id in connections:
        del connections[local_user_id]
        _save_connections(connections)
    return {"status": "disconnected"}


def post_to_instagram(local_user_id: str, image_url: str, caption: str) -> dict:
    """Post an image to Instagram via Facebook Graph API.

    Steps:
    1. Create a media container: POST /{ig-user-id}/media
    2. Publish the container: POST /{ig-user-id}/media_publish
    """
    connections = _load_connections()
    conn = connections.get(local_user_id)
    if not conn:
        return {"error": "Instagram not connected."}

    accounts = conn.get("instagram_accounts", [])
    if not accounts:
        return {"error": "No linked Instagram accounts found."}

    # Use the first linked Instagram account
    ig_account = accounts[0]
    ig_user_id = ig_account["instagram_id"]
    token = _get_meta_token(local_user_id)

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
        container_data = resp.json()
        creation_id = container_data.get("id")

        if not creation_id:
            return {"error": f"Failed to create media container: {container_data}"}

        # Step 2: Publish the container
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
            "instagram_account": ig_account["page_name"],
        }

    except requests.HTTPError as exc:
        return {"error": f"Instagram post failed: {exc.response.text[:300]}"}
    except Exception as exc:
        return {"error": f"Post failed: {type(exc).__name__}: {exc}"}


def validate_connection(local_user_id: str) -> dict:
    """Validate Instagram Graph token by calling /me."""
    conn = _load_connections().get(local_user_id)
    if not conn or conn.get("status") != "connected":
        return {"status": "not_connected", "platform": "instagram"}
    try:
        resp = requests.get(
            f"https://graph.facebook.com/v18.0/me?access_token={conn['access_token']}",
            timeout=10,
        )
        if resp.ok:
            data = resp.json()
            return {"status": "ok", "platform": "instagram", "name": data.get("name")}
        return {"status": "error", "platform": "instagram", "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
    except Exception as exc:
        return {"status": "error", "platform": "instagram", "error": str(exc)}

