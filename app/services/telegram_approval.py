"""Telegram bot for post approval notifications.

Requires TELEGRAM_BOT_TOKEN in .env.
Consultants register their chat ID via /start.
"""
import os, json, requests
from typing import Optional

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
BASE_URL = os.environ.get("PUBLIC_BASE_URL", "https://smpf.finwatchpro.net").rstrip("/")
WEBHOOK_PATH = "/api/telegram/approval-webhook"

# In-memory store for consultant chat IDs (persist to DB in production)
# Map: consultant_email -> chat_id
_consultant_chats = {}


def _api(method: str, payload: dict):
    if not BOT_TOKEN:
        print(f"[TELEGRAM FALLBACK] {method}: {json.dumps(payload)}")
        return True
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    try:
        r = requests.post(url, json=payload, timeout=30)
        r.raise_for_status()
        return r.json().get("ok", False)
    except Exception as exc:
        print(f"[TELEGRAM ERROR] {exc}")
        return False


def send_approval_request(
    chat_id: str,
    post_text: str,
    platforms: list,
    image_url: Optional[str],
    approval_token: str,
    client_name: str = "",
):
    """Send inline-keyboard approval message to consultant's Telegram."""
    platforms_str = ", ".join(platforms)
    caption = f"📢 *Post Approval Required*\n\n*Client:* {client_name or 'Unknown'}\n*Platforms:* {platforms_str}\n\n_{post_text or '(No text)'}_"

    buttons = [
        [
            {"text": "✅ Approve", "callback_data": f"approve:{approval_token}"},
            {"text": "❌ Reject", "callback_data": f"reject:{approval_token}"},
        ],
        [
            {"text": "🔍 Preview", "url": f"{BASE_URL}/preview/{approval_token}"},
        ],
    ]

    payload = {
        "chat_id": chat_id,
        "text": caption,
        "parse_mode": "Markdown",
        "reply_markup": {"inline_keyboard": buttons},
    }

    if image_url and image_url.startswith("http"):
        # Send photo with caption instead of text
        payload = {
            "chat_id": chat_id,
            "photo": image_url,
            "caption": caption,
            "parse_mode": "Markdown",
            "reply_markup": {"inline_keyboard": buttons},
        }
        return _api("sendPhoto", payload)

    return _api("sendMessage", payload)


def handle_callback(query: dict) -> str:
    """Process inline button press. Returns human-readable result."""
    data = query.get("data", "")
    chat_id = query.get("message", {}).get("chat", {}).get("id")
    msg_id = query.get("message", {}).get("message_id")

    if ":" not in data:
        return "Unknown action"

    action, token = data.split(":", 1)

    if action == "approve":
        # Hit our own API
        try:
            r = requests.get(
                f"{BASE_URL}/approve/{token}",
                timeout=30,
                allow_redirects=False,
            )
            if r.status_code in (200, 307, 302):
                _api("answerCallbackQuery", {"callback_query_id": query["id"], "text": "Approved! Posting now..."})
                _edit_message(chat_id, msg_id, "✅ *Approved* — post has been published.")
                return "approved"
        except Exception as exc:
            print(f"[TELEGRAM APPROVE ERROR] {exc}")
            _api("answerCallbackQuery", {"callback_query_id": query["id"], "text": "Error approving. Please use email link."})
            return "error"

    if action == "reject":
        _api("answerCallbackQuery", {"callback_query_id": query["id"], "text": "Rejected."})
        _edit_message(chat_id, msg_id, "❌ *Rejected* — post was not approved.")
        return "rejected"

    return "unknown"


def _edit_message(chat_id, msg_id, new_text):
    _api("editMessageText", {
        "chat_id": chat_id,
        "message_id": msg_id,
        "text": new_text,
        "parse_mode": "Markdown",
    })


def set_webhook():
    """Set webhook URL if running on a public server."""
    if not BOT_TOKEN:
        return False
    webhook_url = f"{BASE_URL}{WEBHOOK_PATH}"
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
    try:
        r = requests.post(url, json={"url": webhook_url}, timeout=30)
        return r.json().get("ok", False)
    except Exception as exc:
        print(f"[TELEGRAM WEBHOOK ERROR] {exc}")
        return False


def get_chat_id_for_email(email: str) -> Optional[str]:
    return _consultant_chats.get(email)


def register_chat(email: str, chat_id: str):
    _consultant_chats[email] = str(chat_id)
