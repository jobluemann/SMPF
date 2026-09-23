# SMPF v1 — app/connectors/whatsapp_business_connect.py — 2026-08-28
"""WhatsApp Business API connector — official Meta Business Platform.

This is NOT for groups. The Business API only supports:
  - 1:1 messaging to individuals
  - Broadcast messages using pre-approved templates
  - Messaging within a 24-hour window (or templates outside it)

Requirements:
  - WhatsApp Business Account ID
  - Phone Number ID (registered and verified in Meta Console)
  - Permanent Access Token with whatsapp_business_messaging scope

Groups are NOT supported by this API. For groups, use the web automation
connector (whatsapp_connect.py) instead.
"""
import json
import os
from typing import Optional

import requests

from app.config import (
    WHATSAPP_BUSINESS_PHONE_NUMBER_ID,
    WHATSAPP_BUSINESS_ACCOUNT_ID,
    WHATSAPP_BUSINESS_TOKEN,
    WHATSAPP_BUSINESS_API_VERSION,
    DATA_DIR,
)

API_BASE = f"https://graph.facebook.com/{WHATSAPP_BUSINESS_API_VERSION}"
CONNECTIONS_PATH = os.path.join(DATA_DIR, "whatsapp_business_connections.json")


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


def _has_credentials() -> bool:
    return bool(WHATSAPP_BUSINESS_PHONE_NUMBER_ID and WHATSAPP_BUSINESS_TOKEN)


def _api_post(endpoint: str, payload: dict) -> dict:
    """Generic POST to the WhatsApp Business API."""
    url = f"{API_BASE}/{endpoint}"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_BUSINESS_TOKEN}",
        "Content-Type": "application/json",
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=20)
    if resp.status_code >= 400:
        try:
            err = resp.json()
            return {"status": "error", "error": f"WhatsApp API {resp.status_code}: {err}"}
        except Exception:
            return {"status": "error", "error": f"WhatsApp API {resp.status_code}: {resp.text[:200]}"}
    return resp.json()


# ─── Public API ────────────────────────────────────────────────────────────


def get_connection_status(local_user_id: str) -> dict:
    """Return status based on whether credentials are configured."""
    if not _has_credentials():
        return {"status": "not_connected"}

    # Try a lightweight API call to verify token validity
    # Query the phone number info
    try:
        resp = requests.get(
            f"{API_BASE}/{WHATSAPP_BUSINESS_PHONE_NUMBER_ID}",
            headers={"Authorization": f"Bearer {WHATSAPP_BUSINESS_TOKEN}"},
            params={"fields": "id,display_phone_number,verified_name"},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            # Store connection metadata
            connections = _load_connections()
            connections[local_user_id] = {
                "platform": "whatsapp_business",
                "status": "connected",
                "phone_number": data.get("display_phone_number"),
                "verified_name": data.get("verified_name"),
                "phone_number_id": WHATSAPP_BUSINESS_PHONE_NUMBER_ID,
                "account_id": WHATSAPP_BUSINESS_ACCOUNT_ID,
            }
            _save_connections(connections)
            return {
                "status": "connected",
                "phone_number": data.get("display_phone_number"),
                "verified_name": data.get("verified_name"),
            }
        else:
            return {"status": "error", "error": f"Token invalid or expired. API returned {resp.status_code}."}
    except Exception as exc:
        return {"status": "error", "error": f"Connection check failed: {exc}"}


def send_text_message(to_number: str, message: str) -> dict:
    """Send a text message to an individual phone number.

    Args:
        to_number: Full international format, e.g. "27123456789"
        message: Text body. Max 4096 characters.

    Note:
        This only works if the recipient has messaged you first
        (24-hour conversation window), OR if you have an open
        conversation with them.
    """
    if not _has_credentials():
        return {"status": "error", "error": "WhatsApp Business API not configured."}

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_number,
        "type": "text",
        "text": {"body": message},
    }

    result = _api_post(f"{WHATSAPP_BUSINESS_PHONE_NUMBER_ID}/messages", payload)
    if result.get("status") == "error":
        return result

    return {
        "status": "sent",
        "message_id": result.get("messages", [{}])[0].get("id"),
        "to": to_number,
        "message_preview": message[:80],
    }


def send_template_message(to_number: str, template_name: str, language_code: str = "en") -> dict:
    """Send a pre-approved template message.

    Templates are required when messaging someone outside the 24h window
    or for first contact. They must be created and approved in the
    Meta Business Manager first.

    Args:
        to_number: Full international format, e.g. "27123456789"
        template_name: Name of the approved template (e.g. "hello_world")
        language_code: ISO language code, default "en"
    """
    if not _has_credentials():
        return {"status": "error", "error": "WhatsApp Business API not configured."}

    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": language_code},
        },
    }

    result = _api_post(f"{WHATSAPP_BUSINESS_PHONE_NUMBER_ID}/messages", payload)
    if result.get("status") == "error":
        return result

    return {
        "status": "sent",
        "message_id": result.get("messages", [{}])[0].get("id"),
        "to": to_number,
        "template": template_name,
    }


def disconnect(local_user_id: str) -> dict:
    """Clear stored connection metadata."""
    connections = _load_connections()
    if local_user_id in connections:
        del connections[local_user_id]
        _save_connections(connections)
    return {"status": "disconnected"}
