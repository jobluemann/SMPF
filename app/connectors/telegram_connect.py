# SMPF v1 — app/connectors/telegram_connect.py — 2026-08-28
"""Telegram Bot API connector — official, free, supports groups natively.

Unlike WhatsApp, Telegram actively encourages bots. No ban risk.
Bots can send messages to:
  - Individual users (by chat_id)
  - Groups (by group chat_id, usually negative numbers)
  - Channels (by channel username or chat_id)

To get a group chat_id:
  1. Add the bot to the group
  2. Send a message in the group
  3. Call GET /getUpdates and look for the chat.id field

Or use the web approach: https://web.telegram.org → open group →
URL shows something like #-1234567890 → chat_id is -1234567890.
"""
import json
import os
from typing import Optional

import requests

from app.config import TELEGRAM_BOT_TOKEN, DATA_DIR

API_BASE = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
CONNECTIONS_PATH = os.path.join(DATA_DIR, "telegram_connections.json")


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


def _api_call(method: str, payload: dict = None) -> dict:
    """Generic Telegram Bot API call."""
    url = f"{API_BASE}/{method}"
    try:
        if payload:
            resp = requests.post(url, json=payload, timeout=20)
        else:
            resp = requests.get(url, timeout=20)
        data = resp.json()
        if not data.get("ok"):
            return {"status": "error", "error": data.get("description", "Telegram API error")}
        return {"status": "ok", "result": data.get("result")}
    except Exception as exc:
        return {"status": "error", "error": f"{type(exc).__name__}: {exc}"}


# ─── Public API ────────────────────────────────────────────────────────────


def get_connection_status(local_user_id: str) -> dict:
    """Check if bot token is valid by calling getMe."""
    if not TELEGRAM_BOT_TOKEN:
        return {"status": "not_connected"}

    result = _api_call("getMe")
    if result.get("status") == "ok":
        bot = result["result"]
        connections = _load_connections()
        connections[local_user_id] = {
            "platform": "telegram",
            "status": "connected",
            "bot_id": bot.get("id"),
            "bot_username": bot.get("username"),
            "bot_name": bot.get("first_name"),
            "can_join_groups": bot.get("can_join_groups"),
        }
        _save_connections(connections)
        return {
            "status": "connected",
            "bot_username": bot.get("username"),
            "bot_name": bot.get("first_name"),
        }
    return {"status": "error", "error": result.get("error", "Token invalid")}


def send_message(chat_id: str, text: str, parse_mode: str = "HTML") -> dict:
    """Send a text message to a user, group, or channel.

    Args:
        chat_id: User ID, group ID (negative), or channel username (@channelname)
        text: Message text. Max 4096 characters.
        parse_mode: HTML or Markdown. Use HTML for bold, links, etc.
    """
    if not TELEGRAM_BOT_TOKEN:
        return {"status": "error", "error": "Telegram bot token not configured."}

    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
    }

    result = _api_call("sendMessage", payload)
    if result.get("status") == "error":
        return result

    msg = result.get("result", {})
    return {
        "status": "sent",
        "message_id": msg.get("message_id"),
        "chat_id": chat_id,
        "message_preview": text[:80],
    }


def send_photo(chat_id: str, photo_url: str, caption: str = "") -> dict:
    """Send a photo to a user, group, or channel."""
    if not TELEGRAM_BOT_TOKEN:
        return {"status": "error", "error": "Telegram bot token not configured."}

    payload = {
        "chat_id": chat_id,
        "photo": photo_url,
        "caption": caption,
        "parse_mode": "HTML",
    }

    result = _api_call("sendPhoto", payload)
    if result.get("status") == "error":
        return result

    return {
        "status": "sent",
        "message_id": result.get("result", {}).get("message_id"),
        "chat_id": chat_id,
    }


def get_updates(offset: int = 0, limit: int = 10) -> list:
    """Fetch recent messages sent to the bot.

    Useful for discovering group chat_ids: add bot to group,
    send a message, then call get_updates and read the chat.id.
    """
    if not TELEGRAM_BOT_TOKEN:
        return []

    payload = {"offset": offset, "limit": limit}
    result = _api_call("getUpdates", payload)
    if result.get("status") == "ok":
        return result.get("result", [])
    return []


def disconnect(local_user_id: str) -> dict:
    """Clear stored connection metadata."""
    connections = _load_connections()
    if local_user_id in connections:
        del connections[local_user_id]
        _save_connections(connections)
    return {"status": "disconnected"}

# Wrappers for client_wrapper compatibility

def post_text(local_user_id: str, text: str) -> dict:
    connections = _load_connections()
    user_conn = connections.get(local_user_id, {})
    chat_id = user_conn.get("chat_id")
    if not chat_id:
        return {"status": "error", "error": "No Telegram chat_id stored."}
    return send_message(str(chat_id), text)


def post_image(local_user_id: str, image_url: str, caption: str = "") -> dict:
    connections = _load_connections()
    user_conn = connections.get(local_user_id, {})
    chat_id = user_conn.get("chat_id")
    if not chat_id:
        return {"status": "error", "error": "No Telegram chat_id stored."}
    return send_photo(str(chat_id), image_url, caption)


def validate_connection(local_user_id: str) -> dict:
    """Validate Telegram bot token by calling /getMe."""
    if not TELEGRAM_BOT_TOKEN:
        return {"status": "not_configured", "platform": "telegram"}
    try:
        resp = requests.get(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe",
            timeout=10,
        )
        if resp.ok:
            data = resp.json()
            if data.get("ok"):
                return {"status": "ok", "platform": "telegram", "bot_name": data["result"]["username"]}
            return {"status": "error", "platform": "telegram", "error": data.get("description", "unknown")}
        return {"status": "error", "platform": "telegram", "error": f"HTTP {resp.status_code}"}
    except Exception as exc:
        return {"status": "error", "platform": "telegram", "error": str(exc)}

