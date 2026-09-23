# SMPF v1 — app/connectors/whatsapp_connect.py — 2026-08-27
"""WhatsApp Web automation connector — personal number, NO Business API.

⚠️  IMPORTANT WARNINGS:
  1. WhatsApp strictly forbids automation in its Terms of Service.
     Your personal number CAN be permanently banned.
  2. This is for authorised group messaging only — spam will get you banned fast.
  3. The phone with WhatsApp installed must stay online (connected to internet)
     while this connector runs — WhatsApp Web is a mirror of the phone app.
  4. QR code expires ~40 seconds. If it times out, click Connect again.

Architecture:
  - Uses Playwright to drive web.whatsapp.com (already in requirements.txt).
  - Session persisted via Playwright storage_state (cookies + localStorage).
  - First connect: show QR code → user scans with phone → session saved.
  - Posting: restore session → search group by name → type & send.
  - No background browser is kept open; browser launches per operation.

Expected files in DATA_DIR:
  whatsapp_connections.json   — connection metadata + saved groups
  whatsapp_session/           — Playwright storage_state.json
  whatsapp_qr.png             — QR screenshot during connect flow
"""
import json
import os
import random
import time
from typing import Optional

from app.config import DATA_DIR

# Playwright is already a project dependency (gettr_admin uses it).
try:
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
except ImportError as exc:
    raise ImportError(
        "Playwright not installed. Run: pip install playwright && playwright install chromium"
    ) from exc

CONNECTIONS_PATH = os.path.join(DATA_DIR, "whatsapp_connections.json")
SESSION_DIR = os.path.join(DATA_DIR, "whatsapp_session")
QR_PATH = os.path.join(DATA_DIR, "whatsapp_qr.png")

# WhatsApp Web URL
WA_URL = "https://web.whatsapp.com"

# ─── persistence helpers ───────────────────────────────────────────────────


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


def _session_path() -> str:
    os.makedirs(SESSION_DIR, exist_ok=True)
    return os.path.join(SESSION_DIR, "storage_state.json")


def _has_session() -> bool:
    return os.path.exists(_session_path())


# ─── browser helpers ───────────────────────────────────────────────────────


def _launch_browser(headless: bool = False, storage_state: Optional[str] = None):
    """Launch a persistent Playwright browser context with anti-detection.

    headless=False during QR scan so user can see the page (optional).
    headless=True during posting for background operation.
    """
    p = sync_playwright().start()
    browser = p.chromium.launch(
        headless=headless,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars",
            "--window-size=1280,720",
        ],
    )
    # Realistic viewport + locale to avoid bot detection
    context_kwargs = {
        "viewport": {"width": 1280, "height": 720},
        "user_agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        ),
        "locale": "en-US",
        "timezone_id": "America/New_York",
        "permissions": [],
    }
    if storage_state and os.path.exists(storage_state):
        context_kwargs["storage_state"] = storage_state
    context = browser.new_context(**context_kwargs)
    # Remove webdriver flag
    context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
    """)
    page = context.new_page()
    return p, browser, context, page


def _close_browser(p, browser, context, page):
    try:
        page.close()
    except Exception:
        pass
    try:
        context.close()
    except Exception:
        pass
    try:
        browser.close()
    except Exception:
        pass
    try:
        p.stop()
    except Exception:
        pass


# ─── human mimicry helpers ─────────────────────────────────────────────────

def _human_delay(min_sec: float = 0.5, max_sec: float = 2.5):
    """Pause for a random duration to simulate human reaction time."""
    time.sleep(random.uniform(min_sec, max_sec))


def _human_type(page, element, text: str, min_delay: int = 30, max_delay: int = 120):
    """Type text with variable speed like a human, not instant fill()."""
    element.click()
    _human_delay(0.2, 0.6)
    for char in text:
        element.type(char, delay=random.randint(min_delay, max_delay))


def _random_mouse_move(page):
    """Move mouse to a random screen position to simulate human jitter."""
    try:
        x = random.randint(200, 800)
        y = random.randint(200, 500)
        page.mouse.move(x, y)
        _human_delay(0.2, 0.5)
    except Exception:
        pass


# ─── QR connect flow ───────────────────────────────────────────────────────


def start_qr_flow() -> dict:
    """Launch WhatsApp Web, grab QR screenshot, return path to QR image.

    The caller must poll check_qr_status() until the user scans the code.
    """
    # Clean any old session so we get a fresh QR
    disconnect("local_test_user")

    p, browser, context, page = _launch_browser(headless=False)
    try:
        page.goto(WA_URL, wait_until="domcontentloaded")
        # Wait for QR canvas to appear (or the loading spinner to resolve)
        # The canvas usually has a specific aria-label or is the first canvas.
        qr_selector = "canvas[aria-label*='Scan']"
        try:
            page.wait_for_selector(qr_selector, timeout=15000)
        except PWTimeout:
            # Fallback: wait for any canvas
            page.wait_for_selector("canvas", timeout=10000)

        # Give a moment for QR to render fully
        time.sleep(2)

        # Screenshot the QR area (WhatsApp renders it as a square canvas)
        # We screenshot the whole page area around the QR for reliability
        qr_element = page.query_selector("canvas")
        if qr_element:
            qr_element.screenshot(path=QR_PATH)
        else:
            page.screenshot(path=QR_PATH)

        # Save the browser context to a temporary location so we can resume
        # checking login status without restarting the browser
        temp_session = os.path.join(SESSION_DIR, "temp_session.json")
        context.storage_state(path=temp_session)

        return {
            "qr_path": QR_PATH,
            "status": "qr_ready",
            "message": "Scan the QR code with your phone's WhatsApp app (Settings → Linked Devices → Link a Device).",
        }
    except Exception as exc:
        _close_browser(p, browser, context, page)
        return {"status": "error", "error": f"Failed to start QR flow: {exc}"}
    finally:
        # We intentionally do NOT close the browser here — the caller must
        # keep it alive while polling, or we restart with temp_session.
        # For simplicity, we close and rely on temp_session for resume.
        _close_browser(p, browser, context, page)


def check_qr_status() -> dict:
    """Check whether the user has scanned the QR code.

    Returns:
        {"status": "connected"}        — login succeeded, session saved
        {"status": "waiting"}          — still on QR screen
        {"status": "error", ...}       — something went wrong
    """
    temp_session = os.path.join(SESSION_DIR, "temp_session.json")
    if not os.path.exists(temp_session):
        return {"status": "error", "error": "No active QR flow. Click Connect first."}

    p, browser, context, page = _launch_browser(headless=True, storage_state=temp_session)
    try:
        page.goto(WA_URL, wait_until="domcontentloaded")

        # If logged in, the chat list appears within ~10s
        chat_list_selectors = [
            '[data-testid="chat-list"]',
            'div[aria-label="Chat list"]',
            '[data-testid="cell-frame-container"]',
            '#side',  # older ID for the left sidebar
        ]

        found_chat_list = False
        for sel in chat_list_selectors:
            try:
                page.wait_for_selector(sel, timeout=8000)
                found_chat_list = True
                break
            except PWTimeout:
                continue

        if not found_chat_list:
            # Still on QR page — check if QR still there
            qr_canvas = page.query_selector("canvas")
            if qr_canvas:
                return {"status": "waiting", "message": "QR code not scanned yet."}
            # Neither QR nor chat list — maybe loading or unexpected state
            return {"status": "waiting", "message": "Loading or unexpected state."}

        # Success! Save the real session
        context.storage_state(path=_session_path())
        os.remove(temp_session)  # clean up temp

        # Extract user info if possible (phone number in settings or header)
        # WhatsApp doesn't easily expose the phone number in DOM, so we store a generic identity
        connections = _load_connections()
        connections["local_test_user"] = {
            "platform": "whatsapp",
            "status": "connected",
            "connected_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "note": "Session active. Phone must stay online.",
        }
        _save_connections(connections)

        return {"status": "connected", "message": "WhatsApp Web session established."}

    except Exception as exc:
        return {"status": "error", "error": f"Status check failed: {exc}"}
    finally:
        _close_browser(p, browser, context, page)


# ─── messaging ─────────────────────────────────────────────────────────────


def send_message_to_group(group_name: str, message: str) -> dict:
    """Send a text message to a WhatsApp group by its displayed name.

    Args:
        group_name: Exact or partial name of the group chat as shown in WhatsApp.
        message: Text to send. Supports newlines via \\n.

    Returns:
        {"status": "sent", "group": ..., "message_preview": ...}
        {"status": "error", ...}
    """
    if not _has_session():
        return {"status": "error", "error": "WhatsApp not connected. Connect first."}

    p, browser, context, page = _launch_browser(headless=True, storage_state=_session_path())
    try:
        page.goto(WA_URL, wait_until="domcontentloaded")

        # Wait for chat list
        chat_list_selectors = [
            '[data-testid="chat-list"]',
            'div[aria-label="Chat list"]',
            '[data-testid="cell-frame-container"]',
            '#side',
        ]
        chat_list_found = False
        for sel in chat_list_selectors:
            try:
                page.wait_for_selector(sel, timeout=15000)
                chat_list_found = True
                break
            except PWTimeout:
                continue
        if not chat_list_found:
            return {"status": "error", "error": "Chat list not found. Session may be expired. Reconnect WhatsApp."}

        # Search for the group
        # Strategy: click search box, type group name, wait for results, click first match
        search_selectors = [
            '[data-testid="chat-list-search"]',
            'div[contenteditable="true"][title*="Search"]',
            'div[contenteditable="true"][aria-label*="Search"]',
        ]
        search_box = None
        for sel in search_selectors:
            search_box = page.query_selector(sel)
            if search_box:
                break

        if not search_box:
            # Try pressing Ctrl+K to open search (WhatsApp shortcut)
            page.keyboard.press("Control+k")
            time.sleep(1)
            for sel in search_selectors:
                search_box = page.query_selector(sel)
                if search_box:
                    break

        if not search_box:
            return {"status": "error", "error": "Could not find search box. WhatsApp UI may have changed."}

        # Human-like interaction: small delay, random mouse move, then click
        _human_delay(0.3, 0.8)
        _random_mouse_move(page)
        search_box.click()
        _human_delay(0.2, 0.5)
        # Type slowly like a human instead of instant fill()
        _human_type(page, search_box, group_name)
        _human_delay(1.5, 3.0)  # wait for search results to populate

        # Click the first chat result that matches the group name
        result_selectors = [
            f'[data-testid="cell-frame-title"]:has-text("{group_name}")',
            f'span[title="{group_name}"]',
            f'div[role="button"] span:has-text("{group_name}")',
        ]
        clicked = False
        for sel in result_selectors:
            try:
                _human_delay(0.2, 0.6)
                _random_mouse_move(page)
                page.click(sel, timeout=3000)
                clicked = True
                break
            except Exception:
                continue

        if not clicked:
            # Fallback: try pressing Enter to select first result
            _human_delay(0.3, 0.7)
            page.keyboard.press("Enter")
            _human_delay(0.5, 1.0)
            clicked = True

        if not clicked:
            return {"status": "error", "error": f"Group '{group_name}' not found in search results."}

        # Wait for chat to open (compose box appears)
        compose_selectors = [
            '[data-testid="conversation-compose-box-input"]',
            'div[contenteditable="true"][aria-label*="message"]',
            'div[contenteditable="true"][aria-label*="Type"]',
            'footer div[contenteditable="true"]',
        ]
        compose_box = None
        for sel in compose_selectors:
            try:
                page.wait_for_selector(sel, timeout=10000)
                compose_box = page.query_selector(sel)
                if compose_box:
                    break
            except PWTimeout:
                continue

        if not compose_box:
            return {"status": "error", "error": "Compose box not found. Chat may not have opened."}

        # Simulate "reading" the chat before typing
        _human_delay(1.0, 2.5)
        _random_mouse_move(page)

        # Type message with human-like speed (handle newlines)
        compose_box.click()
        _human_delay(0.2, 0.5)
        lines = message.split("\n")
        for i, line in enumerate(lines):
            if i > 0:
                page.keyboard.press("Shift+Enter")
                _human_delay(0.1, 0.3)
            _human_type(page, compose_box, line, min_delay=40, max_delay=180)

        # Pause before sending (like a human re-reading)
        _human_delay(0.8, 2.0)

        # Click send button or press Enter
        send_selectors = [
            '[data-testid="send"]',
            'span[data-icon="send"]',
            'button[aria-label="Send"]',
        ]
        sent = False
        for sel in send_selectors:
            try:
                _human_delay(0.2, 0.5)
                page.click(sel, timeout=3000)
                sent = True
                break
            except Exception:
                continue

        if not sent:
            page.keyboard.press("Enter")
            sent = True

        _human_delay(2.0, 3.5)  # wait for message to send

        return {
            "status": "sent",
            "group": group_name,
            "message_preview": message[:80] + ("..." if len(message) > 80 else ""),
        }

    except Exception as exc:
        return {"status": "error", "error": f"Send failed: {type(exc).__name__}: {exc}"}
    finally:
        _close_browser(p, browser, context, page)


# ─── status / disconnect / groups ──────────────────────────────────────────


def get_connection_status(local_user_id: str) -> dict:
    connections = _load_connections()
    conn = connections.get(local_user_id)
    if not conn:
        if _has_session():
            return {"status": "connected", "note": "Session file exists but no metadata. May need reconnect."}
        return {"status": "not_connected"}
    
    result = {
        "status": conn["status"],
        "connected_at": conn.get("connected_at"),
        "groups": conn.get("groups", []),
    }
    
    # Add heartbeat info if available
    last_seen = conn.get("last_seen")
    if last_seen:
        result["last_seen"] = last_seen
        # Calculate human-readable time ago
        try:
            from datetime import datetime, timezone
            last_dt = datetime.fromisoformat(last_seen.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            delta = now - last_dt
            if delta.days > 0:
                result["last_seen_human"] = f"{delta.days}d ago"
            elif delta.seconds >= 3600:
                result["last_seen_human"] = f"{delta.seconds // 3600}h ago"
            elif delta.seconds >= 60:
                result["last_seen_human"] = f"{delta.seconds // 60}m ago"
            else:
                result["last_seen_human"] = f"{delta.seconds}s ago"
        except Exception:
            result["last_seen_human"] = last_seen
    
    health = conn.get("health")
    if health:
        result["health"] = health  # "healthy", "stale", "dead"
    
    return result


def add_group(local_user_id: str, group_name: str) -> dict:
    """Save a WhatsApp group name for quick selection later."""
    connections = _load_connections()
    conn = connections.get(local_user_id)
    if not conn:
        return {"status": "error", "error": "WhatsApp not connected. Connect first."}

    groups = conn.get("groups", [])
    # Prevent duplicates
    if any(g["name"].lower() == group_name.lower() for g in groups):
        return {"status": "error", "error": f"Group '{group_name}' already saved."}

    group_id = f"g{int(time.time() * 1000)}"
    groups.append({
        "id": group_id,
        "name": group_name,
        "added_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    })
    conn["groups"] = groups
    _save_connections(connections)
    return {"status": "added", "group": groups[-1]}


def list_groups(local_user_id: str) -> list:
    """Return saved WhatsApp groups for this user."""
    connections = _load_connections()
    conn = connections.get(local_user_id)
    if not conn:
        return []
    return conn.get("groups", [])


def remove_group(local_user_id: str, group_id: str) -> dict:
    """Remove a saved WhatsApp group by its ID."""
    connections = _load_connections()
    conn = connections.get(local_user_id)
    if not conn:
        return {"status": "error", "error": "WhatsApp not connected."}

    groups = conn.get("groups", [])
    new_groups = [g for g in groups if g["id"] != group_id]
    if len(new_groups) == len(groups):
        return {"status": "error", "error": "Group not found."}

    conn["groups"] = new_groups
    _save_connections(connections)
    return {"status": "removed"}



def check_session_health(local_user_id: str, timeout_ms: int = 15000) -> dict:
    """Heartbeat pulse — check if the saved WhatsApp Web session is still alive.

    Opens WhatsApp Web headlessly, checks if chat list loads. Updates
    connection metadata with last_seen timestamp and health status.

    Returns:
        {"health": "healthy", "last_seen": "..."}  — session works
        {"health": "dead", "error": "..."}         — session expired/logged out
    """
    if not _has_session():
        return {"health": "dead", "error": "No session file. Connect first."}

    p, browser, context, page = _launch_browser(headless=True, storage_state=_session_path())
    try:
        page.goto(WA_URL, wait_until="domcontentloaded")

        chat_list_selectors = [
            '[data-testid="chat-list"]',
            'div[aria-label="Chat list"]',
            '[data-testid="cell-frame-container"]',
            '#side',
        ]

        found_chat_list = False
        for sel in chat_list_selectors:
            try:
                page.wait_for_selector(sel, timeout=timeout_ms)
                found_chat_list = True
                break
            except PWTimeout:
                continue

        now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        connections = _load_connections()
        conn = connections.get(local_user_id)
        if not conn:
            conn = {"platform": "whatsapp", "status": "connected"}
            connections[local_user_id] = conn

        if found_chat_list:
            conn["last_seen"] = now_iso
            conn["health"] = "healthy"
            _save_connections(connections)
            return {"health": "healthy", "last_seen": now_iso}

        # No chat list — session is dead (logged out or phone offline)
        conn["last_seen"] = now_iso
        conn["health"] = "dead"
        _save_connections(connections)

        # Auto-disconnect if dead so UI shows "not connected"
        disconnect(local_user_id)

        return {
            "health": "dead",
            "error": "Session expired or phone offline. Reconnect required.",
            "last_seen": now_iso,
        }

    except Exception as exc:
        return {"health": "dead", "error": f"Health check failed: {exc}"}
    finally:
        _close_browser(p, browser, context, page)


def disconnect(local_user_id: str) -> dict:
    connections = _load_connections()
    if local_user_id in connections:
        del connections[local_user_id]
        _save_connections(connections)

    # Remove session files
    for path in [_session_path(), QR_PATH, os.path.join(SESSION_DIR, "temp_session.json")]:
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass

    return {"status": "disconnected"}
