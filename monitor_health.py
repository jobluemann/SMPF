#!/usr/bin/env python3
"""SMPF Platform Health Monitor + Telegram Alerts.

Run this via cron every 15 minutes:
    */15 * * * * /opt/smpfx/venv/bin/python3 /opt/smpfx/monitor_health.py

Or trigger manually from command line.
"""
import os, sys, json, requests

# ─── Config ─────────────────────────────────────────────────────────────────
API_KEY = "smpf-siteground-bridge-2026-09-21"
BACKEND_URL = "https://smpf.finwatchpro.net"
TELEGRAM_BOT_TOKEN = "8801125744:AAGYHq6Uv3I7BuC7YPkpwas6D9MygpYWDMM"
ADMIN_CHAT_ID = os.getenv("SMPF_ADMIN_CHAT_ID", "")  # Set this to your Telegram chat ID

# Where to store last known good state
STATE_FILE = "/opt/smpfx/data/health_state.json"


def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_state(state: dict):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def fetch_health() -> dict:
    resp = requests.get(
        f"{BACKEND_URL}/api/client/health/platforms",
        headers={"X-SMPF-API-Key": API_KEY},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def send_telegram_alert(message: str):
    if not ADMIN_CHAT_ID:
        print("[WARN] No ADMIN_CHAT_ID set — cannot send Telegram alert.")
        print(f"Message would be:\n{message}")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": ADMIN_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
    }
    try:
        resp = requests.post(url, json=payload, timeout=15)
        resp.raise_for_status()
        print("[OK] Telegram alert sent")
    except Exception as exc:
        print(f"[ERROR] Failed to send Telegram alert: {exc}")


def main():
    print("=" * 60)
    print("SMPF Platform Health Check")
    print("=" * 60)

    try:
        health = fetch_health()
    except Exception as exc:
        msg = f"🚨 *SMPF Health Check Failed*\n\nCould not reach backend:\n```\n{exc}\n```"
        send_telegram_alert(msg)
        print(f"[ERROR] Health fetch failed: {exc}")
        sys.exit(1)

    checked_at = health.get("checked_at", "unknown")
    platforms = health.get("platforms", {})
    last_state = load_state()

    alerts = []
    summary = []

    for name, result in platforms.items():
        status = result.get("status", "unknown")
        summary.append(f"{name}: {status}")

        # Alert if status changed from ok to error/not_connected
        was_ok = last_state.get(name, {}).get("status") == "ok"
        is_bad = status in ("error", "not_connected", "expired")
        is_ok = status == "ok"

        if was_ok and is_bad:
            error = result.get("error", "unknown error")
            alerts.append(f"🔴 *{name.upper()}* went from ✅ OK to ❌ {status}\n   Error: `{error}`")
        elif not was_ok and is_ok:
            alerts.append(f"🟢 *{name.upper()}* recovered — now OK")

    # Save current state for next run
    save_state(platforms)

    print(f"Checked at: {checked_at}")
    print("Status: " + ", ".join(summary))

    if alerts:
        alert_msg = (
            f"🚨 *SMPF Platform Alert*\n"
            f"Checked: `{checked_at}`\n\n"
            + "\n\n".join(alerts)
            + "\n\n[Dashboard](https://smpf.finwatchpro.net/status)"
        )
        send_telegram_alert(alert_msg)
    else:
        print("[OK] No changes since last check")

    print("=" * 60)


if __name__ == "__main__":
    main()
