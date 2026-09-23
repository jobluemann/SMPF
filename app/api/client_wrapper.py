"""Multi-tenant client wrapper for SMPF connectors.

This layer sits between the API routes and the connector modules,
adding client_id scoping to all operations.

Each client gets their own connection state stored as:
  data/clients/{client_id}/{platform}_connections.json

This replaces the single "local_test_user" approach.
"""
import os, json, hashlib
from typing import Optional, Dict, Any

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
CLIENTS_DIR = os.path.join(DATA_DIR, "clients")


def _client_dir(client_id: str) -> str:
    """Return the data directory for a specific client."""
    # Sanitize client_id to prevent path traversal
    safe_id = hashlib.md5(client_id.encode()).hexdigest()[:16]
    d = os.path.join(CLIENTS_DIR, safe_id)
    os.makedirs(d, exist_ok=True)
    return d


def _client_path(client_id: str, filename: str) -> str:
    """Path to a client's connection/state file."""
    return os.path.join(_client_dir(client_id), filename)


def load_client_connections(client_id: str, platform: str) -> dict:
    """Load connection state for a client + platform."""
    path = _client_path(client_id, f"{platform}_connections.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_client_connections(client_id: str, platform: str, data: dict):
    """Save connection state for a client + platform."""
    path = _client_path(client_id, f"{platform}_connections.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def delete_client_connections(client_id: str, platform: str):
    """Remove connection state for a client + platform."""
    path = _client_path(client_id, f"{platform}_connections.json")
    if os.path.exists(path):
        os.remove(path)


def list_client_platforms(client_id: str) -> list:
    """List which platforms this client has connected."""
    d = _client_dir(client_id)
    platforms = []
    for f in os.listdir(d) if os.path.exists(d) else []:
        if f.endswith("_connections.json"):
            platforms.append(f.replace("_connections.json", ""))
    return platforms


# ─── Connector wrappers ──────────────────────────────────────────────────

from app.connectors import (
    x_connect, meta_connect, threads_connect, linkedin_connect,
    instagram_connect, telegram_connect, whatsapp_connect,
    youtube_connect, reddit_connect, minds_connect, vk_connect,
    whatsapp_business_connect,
)


# Map: connector module -> name
_CONNECTORS = {
    "x": x_connect,
    "facebook": meta_connect,
    "threads": threads_connect,
    "linkedin": linkedin_connect,
    "instagram": instagram_connect,
    "telegram": telegram_connect,
    "whatsapp": whatsapp_connect,
    "youtube": youtube_connect,
    "reddit": reddit_connect,
    "minds": minds_connect,
    "vk": vk_connect,
    "whatsapp_business": whatsapp_business_connect,
}


def _sync_to_module(client_id: str, platform: str):
    """Copy client's connection state into the module's in-memory dict.
    This is a compatibility bridge — connectors still read their own global dicts.
    """
    module = _CONNECTORS.get(platform)
    if not module:
        return
    client_data = load_client_connections(client_id, platform)
    # Write into the module's global connections dict
    if hasattr(module, "_save_connections"):
        all_conns = module._load_connections()
        all_conns[client_id] = client_data.get(client_id, client_data)
        module._save_connections(all_conns)
    elif hasattr(module, "CONNECTIONS_PATH"):
        # Direct file write for modules that read their own file
        path = module.CONNECTIONS_PATH
        try:
            with open(path, "r", encoding="utf-8") as f:
                all_conns = json.load(f)
        except Exception:
            all_conns = {}
        all_conns[client_id] = client_data.get(client_id, client_data)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(all_conns, f, indent=2)


def _sync_from_module(client_id: str, platform: str):
    """After a connector call, sync module state back to client's file."""
    module = _CONNECTORS.get(platform)
    if not module:
        return
    try:
        if hasattr(module, "_load_connections"):
            all_conns = module._load_connections()
            client_data = all_conns.get(client_id, {})
            save_client_connections(client_id, platform, {client_id: client_data})
    except Exception:
        pass


def get_connection_status(client_id: str, platform: str) -> dict:
    """Get connection status for a client's platform."""
    _sync_to_module(client_id, platform)
    module = _CONNECTORS.get(platform)
    if not module or not hasattr(module, "get_connection_status"):
        return {"status": "unknown"}
    try:
        result = module.get_connection_status(client_id)
        _sync_from_module(client_id, platform)
        return result
    except Exception as e:
        return {"status": "error", "error": str(e)}


def disconnect_platform(client_id: str, platform: str) -> dict:
    """Disconnect a client's platform."""
    module = _CONNECTORS.get(platform)
    if module and hasattr(module, "disconnect"):
        try:
            result = module.disconnect(client_id)
            _sync_from_module(client_id, platform)
            return result
        except Exception as e:
            return {"status": "error", "error": str(e)}
    delete_client_connections(client_id, platform)
    return {"status": "disconnected"}


def post_to_platforms(client_id: str, text: str, platforms: list, image_url: str = None) -> list:
    """Post text (+ optional image) to multiple platforms for a client.

    Returns list of result dicts per platform.
    """
    results = []
    for platform in platforms:
        _sync_to_module(client_id, platform)
        module = _CONNECTORS.get(platform)
        if not module:
            results.append({"platform": platform, "status": "error", "error": "Unknown platform"})
            continue

        try:
            if image_url:
                if platform in ["x", "facebook", "linkedin"]:
                    # These modules accept local file paths for images
                    result = module.post_image(client_id, image_url, caption=text)
                elif platform == "instagram":
                    # Instagram needs public URL
                    result = module.post_image(client_id, image_url, caption=text)
                elif platform == "threads":
                    result = module.post_image(client_id, image_url, text=text)
                else:
                    result = {"status": "error", "error": "Image posting not supported for this platform"}
            else:
                if platform == "instagram":
                    result = {"status": "error", "error": "Image required for Instagram"}
                else:
                    result = module.post_text(client_id, text)

            _sync_from_module(client_id, platform)
            results.append({"platform": platform, **result})
        except Exception as e:
            results.append({"platform": platform, "status": "error", "error": str(e)})

    return results


def upload_media(client_id: str, platform: str, media_path: str) -> dict:
    """Upload media for a client and return media_id."""
    _sync_to_module(client_id, platform)
    module = _CONNECTORS.get(platform)
    if module and hasattr(module, "upload_media"):
        try:
            result = module.upload_media(client_id, media_path)
            _sync_from_module(client_id, platform)
            return result
        except Exception as e:
            return {"status": "error", "error": str(e)}
    return {"status": "error", "error": "Upload not supported"}


# ─── OAuth helpers ─────────────────────────────────────────────────────────

_PENDING_OAUTH = {}  # Map: state -> {client_id, platform, code_verifier}


def start_oauth(client_id: str, platform: str) -> dict:
    """Start OAuth flow for a client. Returns URL to redirect user to."""
    module = _CONNECTORS.get(platform)
    if not module:
        return {"error": f"Unknown platform: {platform}"}

    # X uses PKCE
    if platform == "x" and hasattr(module, "get_authorize_url"):
        import secrets
        state = secrets.token_urlsafe(24)
        result = module.get_authorize_url(state)
        _PENDING_OAUTH[state] = {"client_id": client_id, "platform": "x", "code_verifier": result.get("code_verifier")}
        return {"authorize_url": result["authorize_url"], "state": state}

    # Others
    if hasattr(module, "get_authorize_url"):
        import secrets
        state = secrets.token_urlsafe(24)
        url = module.get_authorize_url(state)
        _PENDING_OAUTH[state] = {"client_id": client_id, "platform": platform}
        return {"authorize_url": url, "state": state}

    return {"error": "OAuth not supported for this platform"}


def complete_oauth(state: str, code: str) -> dict:
    """Complete OAuth callback."""
    pending = _PENDING_OAUTH.pop(state, None)
    if not pending:
        return {"error": "Invalid or expired state"}

    client_id = pending["client_id"]
    platform = pending["platform"]
    module = _CONNECTORS.get(platform)

    if not module:
        return {"error": f"Unknown platform: {platform}"}

    try:
        if platform == "x":
            result = module.complete_connect_flow(
                local_user_id=client_id,
                code=code,
                code_verifier=pending.get("code_verifier")
            )
        else:
            result = module.complete_connect_flow(
                local_user_id=client_id,
                code=code
            )

        _sync_from_module(client_id, platform)
        return {"status": "connected", **result}
    except Exception as e:
        return {"status": "error", "error": str(e)}
