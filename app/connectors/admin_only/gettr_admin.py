# SMPF v1 — app/connectors/admin_only/gettr_admin.py — 2026-08-24
"""Gettr login check — ADMIN ONLY. Not a client-facing connector.

Gettr has no public API. There is no OAuth login screen to hand to a
client the way every other connector in this project does. The only
way in is a real username and password, typed into a real browser.

Because of that, this file is kept structurally separate from
app/connectors/ (the client-facing ones):

  - It lives in app/connectors/admin_only/, not app/connectors/.
  - main.py never imports it. There is no /connectors/gettr/... route.
  - It only runs as a standalone script, on your machine, with your
    own GETTR_USERNAME / GETTR_PASSWORD from .env.
  - It is never offered to a client, ever, under any UI.

Even so, the same rule as every other connector applies: this checks
login only and stops. There is no post/publish call in this file.

Run standalone: python -m app.connectors.admin_only.gettr_admin
Requires: pip install playwright && playwright install chromium
"""
import asyncio

from app.config import GETTR_USERNAME, GETTR_PASSWORD

LOGIN_URL = "https://gettr.com/login"


async def check_login(headless: bool = True) -> dict:
    """Log in with the admin's own Gettr credentials and confirm it worked.

    Does not post anything, does not save a session file, does not
    return the password. Just answers: did this login succeed.
    """
    if not GETTR_USERNAME or not GETTR_PASSWORD:
        return {"ok": False, "error": "GETTR_USERNAME / GETTR_PASSWORD not set in .env"}

    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return {"ok": False, "error": "playwright not installed — pip install playwright && playwright install chromium"}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        page = await browser.new_page()

        try:
            await page.goto(LOGIN_URL, timeout=30000)
            await page.wait_for_timeout(2000)

            # Selectors are best-effort — Gettr's login form markup can
            # change without notice since there's no stable API contract
            # to rely on here. Re-check these against the live page if
            # this stops working.
            await page.fill('input[name="username"]', GETTR_USERNAME)
            await page.fill('input[name="password"]', GETTR_PASSWORD)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(4000)

            logged_in = "login" not in page.url
            return {"ok": logged_in, "final_url": page.url}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}
        finally:
            await browser.close()


if __name__ == "__main__":
    import json
    result = asyncio.run(check_login(headless=False))
    print(json.dumps(result, indent=2))
