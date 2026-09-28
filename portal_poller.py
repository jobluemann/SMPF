#!/usr/bin/env python3
"""
finwatchpro -> SMPF posting job (runs on the Oracle VM every 2 minutes via cron).

Asks the website for posts that are due, posts them with the backend's own
connectors, and reports the result back. Kept deliberately light for the free tier.

Settings in /opt/smpfx/.env:
    PORTAL_URL=https://finwatchpro.net
    PORTAL_BRIDGE_KEY=<same value as BRIDGE_KEY in the website's config.php>

Test the link without posting anything:
    ./venv/bin/python portal_poller.py --check
"""
import fcntl
import os
import re
import sys
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
load_dotenv(os.path.join(HERE, ".env"))

PORTAL = os.getenv("PORTAL_URL", "").rstrip("/")
KEY = os.getenv("PORTAL_BRIDGE_KEY", "")
USER = "local_test_user"  # the backend still only knows the owner's accounts
HEADERS = {"X-Bridge-Key": KEY, "User-Agent": "smpf-poller"}
SECRET_RE = re.compile(r"(client_secret|access_token|refresh_token|token|key)=[^&\s\"']+", re.I)


def log(msg):
    print(f"{datetime.now(timezone.utc):%Y-%m-%d %H:%M:%S} {msg}", flush=True)


def clean(text):
    return SECRET_RE.sub(r"\1=***", str(text))[:250]


def ok_result(r):
    if not isinstance(r, dict):
        return bool(r), ""
    status = str(r.get("status", "")).lower()
    if r.get("error") or status in ("error", "failed", "not_connected"):
        return False, clean(r.get("error") or status)
    return True, ""


def post_one(platform, text, media_url, media_kind, fmt):
    """Returns (posted: bool, note: str)."""
    from app.connectors import (x_connect, meta_connect, threads_connect, linkedin_connect,
                                instagram_connect, telegram_connect)
    if fmt in ("reel", "story") and platform in ("facebook", "instagram"):
        return False, "Reels and Stories are not supported yet"
    image = media_url if media_kind == "image" else None
    if platform == "x":
        return ok_result(x_connect.post_tweet(USER, text))
    if platform == "facebook":
        return ok_result(meta_connect.post_text(USER, text))
    if platform == "threads":
        return ok_result(threads_connect.post_image(USER, image, text) if image else threads_connect.post_text(USER, text))
    if platform == "linkedin":
        return ok_result(linkedin_connect.post_text(USER, text))
    if platform == "instagram":
        if not image:
            return False, "Instagram needs a picture"
        if not image.lower().endswith((".jpg", ".jpeg")):
            return False, "Instagram needs a JPG picture"
        return ok_result(instagram_connect.post_image(USER, image, text))
    if platform == "telegram":
        return ok_result(telegram_connect.send_message(USER, text))
    return False, "This platform is not connected yet"


def main():
    if not PORTAL or not KEY:
        log("PORTAL_URL or PORTAL_BRIDGE_KEY missing in .env")
        return 1
    if "--check" in sys.argv:
        r = requests.get(f"{PORTAL}/api/due.php", params={"peek": 1}, headers=HEADERS, timeout=20)
        log(f"Link check: HTTP {r.status_code} {r.text[:200]}")
        return 0 if r.ok else 1

    lock = open(os.path.join(HERE, "data", ".poller.lock"), "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return 0  # previous run still busy

    r = requests.get(f"{PORTAL}/api/due.php", headers=HEADERS, timeout=30)
    r.raise_for_status()
    posts = r.json().get("posts", [])
    for p in posts:
        results = {}
        for platform in p.get("platforms", []):
            text = (p.get("variants") or {}).get(platform, "")
            try:
                done, note = post_one(platform, text, p.get("media_url"), p.get("media_kind"), p.get("format", "post"))
            except Exception as exc:  # never let one platform stop the others
                done, note = False, clean(f"{type(exc).__name__}: {exc}")
            results[platform] = {"status": "posted" if done else "failed", "note": note}
            log(f"post {p['id']} {platform}: {'posted' if done else 'FAILED ' + note}")
        requests.post(f"{PORTAL}/api/report.php", json={"id": p["id"], "results": results}, headers=HEADERS, timeout=30)
    return 0


if __name__ == "__main__":
    sys.exit(main())
