# SMPF v15 — main.py — 2026-08-28
# Added: WhatsApp Business API connector routes.
import glob
import json
import os
import secrets
import time
from datetime import datetime, timezone

import requests
import json
import os
import secrets
import time
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Query, Depends, Form, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session

from app.providers import groq_client, openrouter_client, groq_tts, image_gen
from app.api.client_api import router as client_router
from app.connectors import (
    x_connect, meta_connect, youtube_connect, reddit_connect,
    threads_connect, minds_connect, vk_connect, instagram_connect,
    linkedin_connect, instagram_graph_connect, whatsapp_connect, telegram_connect,
    whatsapp_business_connect,
)
from app.integrations import google_drive
from app.portal.database import get_db, init_db
from app.portal.models import User, PostQueue
from app.portal import auth as portal_auth
from app.config import SECRET_KEY, DATA_DIR, PUBLIC_BASE_URL
from app.services.approval_service import (
    create_queued_post, get_post_by_token, approve_post, reject_post,
    mark_posted, build_approval_url, build_reject_url, build_preview_url,
)
from app.services.email_service import send_approval_request, send_approved_confirmation, send_rejected_notice
from app.services import telegram_approval

app = FastAPI(title="SMPF — Social Media Platform Framework")

app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Client-facing API (called by SiteGround frontend)
app.include_router(client_router)
templates = Jinja2Templates(directory="frontend/templates")
init_db()
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# ─── Helpers ───────────────────────────────────────────────────────────────


def get_current_user(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return db.query(User).filter(User.id == user_id).first()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ─── Pending OAuth state storage (in-memory; fine for single-user local dev) ─
_pending = {
    "x": {},
    "meta": {},
    "youtube": {},
    "reddit": {},
    "threads": {},
    "minds": {},
    "vk": {},
    "instagram": {},
    "linkedin": {},
    "google_drive": {},
}

# ─── Health check (lightweight — for ping services) ────────────────────────

@app.get("/health")
def health_check():
    """Lightweight health check for uptime monitors. Returns instantly."""
    return {"status": "ok", "service": "smpf-backend", "timestamp": _now_iso()}


# ─── Page routes ───────────────────────────────────────────────────────────


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request, "landing.html", {})


@app.get("/register", response_class=HTMLResponse)
def register_form(request: Request):
    return templates.TemplateResponse(request, "register.html", {"error": None})


@app.post("/register")
def register_submit(
    request: Request,
    company_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    email = email.strip().lower()
    is_valid, error_msg = portal_auth.validate_work_email(email)
    if not is_valid:
        return templates.TemplateResponse(request, "register.html", {"error": error_msg})

    is_strong, error_msg = portal_auth.validate_password_strength(password)
    if not is_strong:
        return templates.TemplateResponse(request, "register.html", {"error": error_msg})

    if db.query(User).filter(User.email == email).first():
        return templates.TemplateResponse(
            request, "register.html", {"error": "An account with that email already exists."}
        )

    pw_hash, salt = portal_auth.hash_password(password)
    user = User(email=email, company_name=company_name, password_hash=pw_hash, password_salt=salt)
    db.add(user)
    db.commit()

    return RedirectResponse("/login", status_code=303)


@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse(request, "login.html", {"error": None})


@app.post("/login")
def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    email = email.strip().lower()
    user = db.query(User).filter(User.email == email).first()
    generic_error = "Incorrect email or password."

    if not user:
        return templates.TemplateResponse(request, "login.html", {"error": generic_error})

    if portal_auth.is_locked_out(user):
        return templates.TemplateResponse(
            request,
            "login.html",
            {"error": f"Account locked after too many failed attempts. Try again in {portal_auth.LOCKOUT_MINUTES} minutes."},
        )

    if not portal_auth.verify_password(password, user.password_hash, user.password_salt):
        portal_auth.record_failed_login(user, db)
        return templates.TemplateResponse(request, "login.html", {"error": generic_error})

    portal_auth.reset_failed_logins(user, db)
    request.session["user_id"] = user.id
    return RedirectResponse("/dashboard", status_code=303)


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, user: User = Depends(get_current_user)):
    if not user:
        return RedirectResponse("/login", status_code=303)

    connectors = [
        ("X (Twitter)", "x", x_connect.get_connection_status("local_test_user")["status"]),
        ("Facebook", "meta", meta_connect.get_connection_status("local_test_user")["status"]),
        ("Instagram", "instagram", instagram_connect.get_connection_status("local_test_user")["status"]),
        ("Threads", "threads", threads_connect.get_connection_status("local_test_user")["status"]),
        ("YouTube", "youtube", youtube_connect.get_connection_status("local_test_user")["status"]),
        ("Reddit", "reddit", reddit_connect.get_connection_status("local_test_user")["status"]),
        ("Minds", "minds", minds_connect.get_connection_status("local_test_user")["status"]),
        ("VK", "vk", vk_connect.get_connection_status("local_test_user")["status"]),
        ("LinkedIn", "linkedin", linkedin_connect.get_connection_status("local_test_user")["status"]),
        ("Google Drive", "google_drive", google_drive.get_connection_status("local_test_user")["status"]),
        ("WhatsApp", "whatsapp", whatsapp_connect.get_connection_status("local_test_user")["status"]),
        ("Telegram", "telegram", telegram_connect.get_connection_status("local_test_user")["status"]),
        ("WhatsApp Business", "whatsapp_business", whatsapp_business_connect.get_connection_status("local_test_user")["status"]),
    ]

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {"user_email": user.email, "connectors": connectors},
    )


@app.get("/status", response_class=HTMLResponse)


@app.get("/status", response_class=HTMLResponse)
def platform_status_page(request: Request):
    """Public status page showing real-time platform health + post stats + token expiries."""
    from app.connectors import (
        x_connect, meta_connect, instagram_graph_connect,
        threads_connect, linkedin_connect, telegram_connect,
        youtube_connect, reddit_connect, minds_connect, vk_connect,
    )
    validators = {
        "x": x_connect, "facebook": meta_connect, "instagram": instagram_connect,
        "threads": threads_connect, "linkedin": linkedin_connect, "youtube": youtube_connect,
        "reddit": reddit_connect, "minds": minds_connect, "vk": vk_connect, "telegram": telegram_connect,
    }
    platforms = {}
    for name, module in validators.items():
        try:
            if hasattr(module, "validate_connection"):
                platforms[name] = module.validate_connection("local_test_user")
            else:
                platforms[name] = {"status": "unknown", "platform": name}
        except Exception as exc:
            platforms[name] = {"status": "error", "platform": name, "error": str(exc)}
    
    # Post stats
    import datetime, json, glob
    from collections import Counter
    data_dir = "/opt/smpfx/data"
    post_stats = {"success": {}, "failed": {}, "last_success": {}, "last_failure": {}, "total": 0}
    log_file = os.path.join(data_dir, "post_log.jsonl")
    if os.path.exists(log_file):
        success = Counter(); failed = Counter()
        last_success = {}; last_failure = {}
        cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=30)
        with open(log_file) as fp:
            for line in fp:
                line = line.strip()
                if not line: continue
                try:
                    entry = json.loads(line)
                    entry_time = datetime.datetime.fromisoformat(entry["time"])
                    if entry_time < cutoff: continue
                except: continue
                for r in entry.get("results", []):
                    post_stats["total"] += 1
                    platform = r.get("platform", "unknown")
                    ts = entry.get("time", "")
                    if r.get("status") == "posted":
                        success[platform] += 1
                        if platform not in last_success or ts > last_success[platform]:
                            last_success[platform] = ts
                    else:
                        failed[platform] += 1
                        if platform not in last_failure or ts > last_failure[platform]:
                            last_failure[platform] = ts
        post_stats["success"] = dict(success)
        post_stats["failed"] = dict(failed)
        post_stats["last_success"] = last_success
        post_stats["last_failure"] = last_failure
    
    # Token expiries
    token_expiries = {}
    for f in sorted(glob.glob(os.path.join(data_dir, "*_connections.json"))):
        platform = os.path.basename(f).replace("_connections.json", "")
        try:
            with open(f) as fp:
                data = json.load(fp)
        except: continue
        for user_id, conn in data.items():
            if not conn: continue
            if conn.get("status") == "connected":
                expires = conn.get("expires_at")
                token_expiries[platform] = {"expires_at": expires[:19] if expires else None, "identity": conn.get("identity", {})}
    
    checked_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    return templates.TemplateResponse(
        request, "status.html",
        {"platforms": platforms, "checked_at": checked_at, "post_stats": post_stats, "token_expiries": token_expiries}
    )

def status_page():
    instagram_status = instagram_connect.get_connection_status("local_test_user")
    instagram_line = ""
    if instagram_status["status"] == "connected" and instagram_status.get("identity"):
        i = instagram_status["identity"]
        instagram_line = f"<li>@{i.get('username', '')}</li>"

    return f"""
    <h1>Status</h1>
    <p>Instagram connection (direct fallback): <b>{instagram_status['status']}</b></p>
    <ul>{instagram_line}</ul>
    <p><a href="/connectors/instagram/start">Connect / reconnect Instagram (direct)</a></p>
    """


# ─── Generic OAuth connector helpers ───────────────────────────────────────


def _oauth_start(connector_module, pending_key: str):
    """Generic OAuth start handler."""
    try:
        state = secrets.token_urlsafe(24)
        # X uses PKCE and returns a dict with authorize_url + code_verifier
        if pending_key == "x":
            result = connector_module.get_authorize_url(state)
            _pending[pending_key]["state"] = state
            _pending[pending_key]["code_verifier"] = result["code_verifier"]
            return RedirectResponse(result["authorize_url"])
        else:
            url = connector_module.get_authorize_url(state)
            _pending[pending_key]["state"] = state
            return RedirectResponse(url)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"{type(exc).__name__}: {exc}")


def _oauth_callback(connector_module, pending_key: str, code: str, state: str, extra_args: dict = None):
    """Generic OAuth callback handler."""
    if state != _pending[pending_key].get("state"):
        raise HTTPException(status_code=400, detail="State mismatch. Start again.")

    try:
        kwargs = {"local_user_id": "local_test_user", "code": code}
        if extra_args:
            kwargs.update(extra_args)
        result = connector_module.complete_connect_flow(**kwargs)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"{type(exc).__name__}: {exc}")
    finally:
        _pending[pending_key].clear()

    return RedirectResponse("/dashboard", status_code=303)


# ─── X ─────────────────────────────────────────────────────────────────────

@app.get("/connectors/x/start")
def x_connect_start():
    return _oauth_start(x_connect, "x")


@app.get("/connectors/x/callback")
def x_connect_callback(code: str = Query(...), state: str = Query(...)):
    return _oauth_callback(
        x_connect, "x", code, state,
        extra_args={"code_verifier": _pending["x"].get("code_verifier")}
    )


@app.post("/connectors/x/disconnect")
def x_disconnect():
    x_connect.disconnect("local_test_user")
    return RedirectResponse("/dashboard", status_code=303)


# ─── LinkedIn ───────────────────────────────────────────────────────────────

@app.get("/connectors/linkedin/start")
def linkedin_connect_start():
    return _oauth_start(linkedin_connect, "linkedin")


@app.get("/connectors/linkedin/callback")
def linkedin_connect_callback(code: str = Query(...), state: str = Query(...)):
    return _oauth_callback(linkedin_connect, "linkedin", code, state)


@app.post("/connectors/linkedin/disconnect")
def linkedin_disconnect():
    linkedin_connect.disconnect("local_test_user")
    return RedirectResponse("/dashboard", status_code=303)


# ─── Meta (Facebook + Instagram unified) ────────────────────────────────────

@app.get("/connectors/meta/start")
def meta_connect_start():
    return _oauth_start(meta_connect, "meta")


@app.get("/connectors/meta/callback")
def meta_connect_callback(code: str = Query(...), state: str = Query(...)):
    return _oauth_callback(meta_connect, "meta", code, state)


@app.post("/connectors/meta/disconnect")
def meta_disconnect():
    meta_connect.disconnect("local_test_user")
    return RedirectResponse("/dashboard", status_code=303)


# ─── YouTube ───────────────────────────────────────────────────────────────

@app.get("/connectors/youtube/start")
def youtube_connect_start():
    return _oauth_start(youtube_connect, "youtube")


@app.get("/connectors/youtube/callback")
def youtube_connect_callback(code: str = Query(...), state: str = Query(...)):
    return _oauth_callback(youtube_connect, "youtube", code, state)


@app.post("/connectors/youtube/disconnect")
def youtube_disconnect():
    youtube_connect.disconnect("local_test_user")
    return RedirectResponse("/dashboard", status_code=303)


# ─── Reddit ────────────────────────────────────────────────────────────────

@app.get("/connectors/reddit/start")
def reddit_connect_start():
    return _oauth_start(reddit_connect, "reddit")


@app.get("/connectors/reddit/callback")
def reddit_connect_callback(code: str = Query(...), state: str = Query(...)):
    return _oauth_callback(reddit_connect, "reddit", code, state)


@app.post("/connectors/reddit/disconnect")
def reddit_disconnect():
    reddit_connect.disconnect("local_test_user")
    return RedirectResponse("/dashboard", status_code=303)


# ─── Threads ───────────────────────────────────────────────────────────────

@app.get("/connectors/threads/start")
def threads_connect_start():
    return _oauth_start(threads_connect, "threads")


@app.get("/connectors/threads/callback")
def threads_connect_callback(code: str = Query(...), state: str = Query(...)):
    return _oauth_callback(threads_connect, "threads", code, state)


@app.post("/connectors/threads/disconnect")
def threads_disconnect():
    threads_connect.disconnect("local_test_user")
    return RedirectResponse("/dashboard", status_code=303)


# ─── Minds ─────────────────────────────────────────────────────────────────

@app.get("/connectors/minds/start")
def minds_connect_start():
    return _oauth_start(minds_connect, "minds")


@app.get("/connectors/minds/callback")
def minds_connect_callback(code: str = Query(...), state: str = Query(...)):
    return _oauth_callback(minds_connect, "minds", code, state)


@app.post("/connectors/minds/disconnect")
def minds_disconnect():
    minds_connect.disconnect("local_test_user")
    return RedirectResponse("/dashboard", status_code=303)


# ─── VK ────────────────────────────────────────────────────────────────────

@app.get("/connectors/vk/start")
def vk_connect_start():
    return _oauth_start(vk_connect, "vk")


@app.get("/connectors/vk/callback")
def vk_connect_callback(code: str = Query(...), state: str = Query(...)):
    return _oauth_callback(vk_connect, "vk", code, state)


@app.post("/connectors/vk/disconnect")
def vk_disconnect():
    vk_connect.disconnect("local_test_user")
    return RedirectResponse("/dashboard", status_code=303)


# ─── Instagram (direct login — fallback only) ──────────────────────────────

@app.get("/connectors/instagram/start")
def instagram_connect_start():
    try:
        state = secrets.token_urlsafe(24)
        url = instagram_connect.get_authorize_url(state)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"{type(exc).__name__}: {exc}. Check app developer settings.",
        )

    _pending["instagram"]["state"] = state
    return RedirectResponse(url)


@app.get("/connectors/instagram/callback")
def instagram_connect_callback(code: str = Query(...), state: str = Query(...)):
    if state != _pending["instagram"].get("state"):
        raise HTTPException(status_code=400, detail="State mismatch. Start again at /connectors/instagram/start")

    try:
        result = instagram_connect.complete_connect_flow(local_user_id="local_test_user", code=code)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"{type(exc).__name__}: {exc}. Check app developer settings.",
        )

    _pending["instagram"].clear()
    return RedirectResponse("/dashboard", status_code=303)


@app.post("/connectors/instagram/disconnect")
def instagram_disconnect():
    instagram_connect.disconnect("local_test_user")
    return RedirectResponse("/dashboard", status_code=303)


# ─── Instagram Graph (via Facebook API) ────────────────────────────────────

@app.get("/connectors/instagram-graph/start")
def instagram_graph_connect_start():
    """Connect Instagram by discovering linked accounts via Facebook Graph API."""
    result = instagram_graph_connect.discover_linked_instagram("local_test_user")
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return RedirectResponse("/dashboard", status_code=303)


@app.post("/connectors/instagram-graph/disconnect")
def instagram_graph_disconnect():
    instagram_connect.disconnect("local_test_user")
    return RedirectResponse("/dashboard", status_code=303)


# ─── Google Drive ──────────────────────────────────────────────────────────

@app.get("/connectors/google_drive/start")
def google_drive_connect_start():
    return _oauth_start(google_drive, "google_drive")


@app.get("/connectors/google_drive/callback")
def google_drive_connect_callback(code: str = Query(...), state: str = Query(...)):
    return _oauth_callback(google_drive, "google_drive", code, state)


@app.post("/connectors/google_drive/disconnect")
def google_drive_disconnect():
    google_drive.disconnect("local_test_user")
    return RedirectResponse("/dashboard", status_code=303)


@app.post("/api/google-drive/upload")
def google_drive_upload(file_path: str = Form(...), folder_id: str = Form(None)):
    """Upload a local file to the connected Google Drive account."""
    status = google_drive.get_connection_status("local_test_user")
    if status["status"] != "connected":
        raise HTTPException(status_code=400, detail="Google Drive not connected.")

    conn = google_drive._load_connections().get("local_test_user", {})
    access_token = conn.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="No access token found.")

    import mimetypes
    mime_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"

    try:
        result = google_drive.upload_file(access_token, file_path, mime_type, folder_id)
        return {"status": "uploaded", "file_id": result.get("id"), "file_name": result.get("name")}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ─── WhatsApp ──────────────────────────────────────────────────────────────

@app.get("/connectors/whatsapp/start", response_class=HTMLResponse)
def whatsapp_connect_start(request: Request):
    """Start WhatsApp Web QR flow. Returns page with QR code to scan."""
    result = whatsapp_connect.start_qr_flow()
    if result.get("status") == "error":
        raise HTTPException(status_code=502, detail=result["error"])
    return templates.TemplateResponse(request, "whatsapp_qr.html", {"timestamp": int(time.time())})


@app.get("/connectors/whatsapp/status-poll")
def whatsapp_status_poll():
    """AJAX endpoint polled by whatsapp_qr.html to check if QR was scanned."""
    return whatsapp_connect.check_qr_status()


@app.post("/connectors/whatsapp/disconnect")
def whatsapp_disconnect():
    whatsapp_connect.disconnect("local_test_user")
    return RedirectResponse("/dashboard", status_code=303)


# ─── WhatsApp Groups API ───────────────────────────────────────────────────

@app.get("/api/whatsapp/groups")
def api_whatsapp_groups():
    """List saved WhatsApp groups for the current user."""
    return {"groups": whatsapp_connect.list_groups("local_test_user")}


@app.post("/api/whatsapp/groups")
async def api_whatsapp_add_group(request: Request):
    """Add a WhatsApp group name to the saved list."""
    body = await request.json()
    name = body.get("name", "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="name is required")
    result = whatsapp_connect.add_group("local_test_user", name)
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.delete("/api/whatsapp/groups/{group_id}")
def api_whatsapp_remove_group(group_id: str):
    """Remove a saved WhatsApp group by ID."""
    result = whatsapp_connect.remove_group("local_test_user", group_id)
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result["error"])
    return result


# ─── Telegram ──────────────────────────────────────────────────────────────

@app.get("/connectors/telegram/start")
def telegram_connect_start():
    """Telegram uses a bot token — no OAuth flow. Just verify the token."""
    result = telegram_connect.get_connection_status("local_test_user")
    if result.get("status") == "connected":
        return RedirectResponse("/dashboard", status_code=303)
    raise HTTPException(status_code=400, detail=result.get("error", "Telegram token invalid or missing."))


@app.post("/connectors/telegram/disconnect")
def telegram_disconnect():
    telegram_connect.disconnect("local_test_user")
    return RedirectResponse("/dashboard", status_code=303)


@app.get("/api/telegram/updates")
def api_telegram_updates():
    """Fetch recent updates to help discover chat IDs."""
    updates = telegram_connect.get_updates()
    chats = []
    seen = set()
    for upd in updates:
        msg = upd.get("message") or upd.get("channel_post") or upd.get("edited_message")
        if not msg:
            continue
        chat = msg.get("chat", {})
        cid = chat.get("id")
        if cid and cid not in seen:
            seen.add(cid)
            chats.append({
                "chat_id": cid,
                "title": chat.get("title") or chat.get("first_name", "Unknown"),
                "type": chat.get("type"),
                "username": chat.get("username"),
            })
    return {"chats": chats}


@app.post("/api/telegram/send")
async def api_telegram_send(request: Request):
    """Standalone Telegram send endpoint."""
    body = await request.json()
    chat_id = body.get("chat_id", "")
    text = body.get("text", "")
    if not chat_id or not text:
        raise HTTPException(status_code=400, detail="chat_id and text are required")
    result = telegram_connect.send_message(str(chat_id), text)
    if result.get("status") != "sent":
        raise HTTPException(status_code=502, detail=result.get("error", "Send failed"))
    return result


# ─── WhatsApp Business ─────────────────────────────────────────────────────

@app.get("/connectors/whatsapp_business/start")
def whatsapp_business_connect_start():
    """WhatsApp Business has no OAuth — it uses the token in .env."""
    result = whatsapp_business_connect.get_connection_status("local_test_user")
    if result.get("status") == "connected":
        return RedirectResponse("/dashboard", status_code=303)
    raise HTTPException(status_code=400, detail=result.get("error", "WhatsApp Business API not configured. Add credentials to .env."))


@app.get("/connectors/whatsapp-business/status")
def whatsapp_business_status():
    """Check WhatsApp Business API connection status."""
    return whatsapp_business_connect.get_connection_status("local_test_user")


@app.post("/connectors/whatsapp-business/disconnect")
def whatsapp_business_disconnect():
    """Disconnect WhatsApp Business API."""
    whatsapp_business_connect.disconnect("local_test_user")
    return RedirectResponse("/dashboard", status_code=303)


@app.post("/api/whatsapp-business/send")
async def api_whatsapp_business_send(request: Request):
    """Send a WhatsApp Business message to a phone number."""
    body = await request.json()
    to_number = body.get("to_number", "")
    message = body.get("message", "")
    if not to_number or not message:
        raise HTTPException(status_code=400, detail="to_number and message are required")
    result = whatsapp_business_connect.send_text_message(to_number, message)
    if result.get("status") != "sent":
        raise HTTPException(status_code=502, detail=result.get("error", "Send failed"))
    return result


# ─── Unified Posting API ───────────────────────────────────────────────────


def _resolve_image_local(image_url: str) -> str:
    """Download a remote image to a local temp file, or return local path as-is."""
    if not image_url.startswith("http"):
        if os.path.exists(image_url):
            return image_url
        # Maybe it's a filename in generated_images
        candidate = os.path.join(DATA_DIR, "generated_images", image_url)
        if os.path.exists(candidate):
            return candidate
        return None
    try:
        img_resp = requests.get(image_url, timeout=30)
        img_resp.raise_for_status()
        ext = os.path.splitext(image_url.split("?")[0])[1] or ".png"
        local_path = os.path.join(DATA_DIR, f"tmp_post_media_{int(time.time())}{ext}")
        with open(local_path, "wb") as f:
            f.write(img_resp.content)
        return local_path
    except Exception:
        return None


def _make_public_image_url(image_ref: str) -> str:
    """Return a publicly accessible URL for an image.

    - If already an http(s) URL → return as-is.
    - If a local file in data/generated_images/ → serve via PUBLIC_BASE_URL.
    - Otherwise return None.
    """
    if image_ref.startswith("http"):
        return image_ref
    # Try as filename in generated_images
    candidate = image_ref
    if not os.path.exists(candidate):
        candidate = os.path.join(DATA_DIR, "generated_images", image_ref)
    if os.path.exists(candidate):
        filename = os.path.basename(candidate)
        return f"{PUBLIC_BASE_URL.rstrip('/')}/generated/{filename}"
    return None

@app.post("/api/post")
async def api_post(request: Request):
    """Post content to one or more connected platforms.

    Body JSON:
      {
        "platforms": ["x", "facebook", "instagram", "whatsapp"],
        "content": {
          "text": "Post text here…",
          "image_url": "https://…"           # required for Instagram
        },
        "whatsapp": {
          "group_name": "My Group"
        }
      }
    """
    body = await request.json()
    platforms = body.get("platforms", [])
    content = body.get("content", {})
    text = content.get("text", "")
    image_url = content.get("image_url")
    results = []

    for platform in platforms:
        if platform == "x":
            media_ids = None
            if image_url:
                media_path = image_url
                if image_url.startswith("http"):
                    try:
                        img_resp = requests.get(image_url, timeout=30)
                        img_resp.raise_for_status()
                        ext = os.path.splitext(image_url.split("?")[0])[1] or ".png"
                        media_path = os.path.join(DATA_DIR, f"tmp_x_media_{int(time.time())}{ext}")
                        with open(media_path, "wb") as f:
                            f.write(img_resp.content)
                    except Exception as exc:
                        results.append({"platform": "x", "status": "error", "error": f"Image download failed: {exc}"})
                        continue
                up = x_connect.upload_media("local_test_user", media_path)
                if up.get("status") == "ok":
                    media_ids = [up["media_id"]]
                else:
                    results.append({"platform": "x", "status": "error", "error": up.get("error", "Media upload failed")})
                    continue
                # Only delete temp downloaded files, not source images
                if media_path != image_url and os.path.exists(media_path) and "/tmp/" in media_path:
                    try:
                        os.remove(media_path)
                    except Exception:
                        pass
            r = x_connect.post_tweet("local_test_user", text, media_ids=media_ids)
            results.append({"platform": "x", **r})

        elif platform == "facebook":
            if image_url:
                media_path = _resolve_image_local(image_url)
                if media_path:
                    r = meta_connect.post_image("local_test_user", media_path, caption=text)
                    # Only delete temp downloaded files, not source images
                    if media_path != image_url and os.path.exists(media_path) and "/tmp/" in media_path:
                        try: os.remove(media_path)
                        except Exception: pass
                else:
                    results.append({"platform": "facebook", "status": "error", "error": "Image download failed"})
                    continue
            else:
                r = meta_connect.post_text("local_test_user", text)
            results.append({"platform": "facebook", **r})

        elif platform == "instagram":
            if not image_url:
                results.append({"platform": "instagram", "status": "error", "error": "image_url required for Instagram"})
                continue
            public_url = _make_public_image_url(image_url)
            if not public_url:
                results.append({"platform": "instagram", "status": "error", "error": "Cannot make image publicly accessible. Provide an http(s) image_url."})
                continue
            r = instagram_connect.post_image("local_test_user", public_url, caption=text)
            results.append({"platform": "instagram", **r})

        elif platform == "threads":
            if image_url:
                public_url = _make_public_image_url(image_url)
                if not public_url:
                    results.append({"platform": "threads", "status": "error", "error": "Cannot make image publicly accessible. Provide an http(s) image_url."})
                    continue
                r = threads_connect.post_image("local_test_user", public_url, text=text)
            else:
                r = threads_connect.post_text("local_test_user", text)
            results.append({"platform": "threads", **r})

        elif platform == "linkedin":
            if image_url:
                media_path = _resolve_image_local(image_url)
                if media_path:
                    r = linkedin_connect.post_image("local_test_user", media_path, caption=text)
                    # Only delete temp downloaded files, not source images
                    if media_path != image_url and os.path.exists(media_path) and "/tmp/" in media_path:
                        try: os.remove(media_path)
                        except Exception: pass
                else:
                    results.append({"platform": "linkedin", "status": "error", "error": "Image download failed"})
                    continue
            else:
                r = linkedin_connect.post_text("local_test_user", text)
            results.append({"platform": "linkedin", **r})

        elif platform == "telegram":
            tg_cfg = body.get("telegram", {})
            chat_id = tg_cfg.get("chat_id", "")
            if not chat_id:
                results.append({"platform": "telegram", "status": "error", "error": "telegram.chat_id required"})
                continue
            r = telegram_connect.send_message(str(chat_id), text)
            results.append({"platform": "telegram", **r})

        elif platform == "whatsapp":
            wa_cfg = body.get("whatsapp", {})
            group_names = wa_cfg.get("group_names", [])
            # Fallback to single group_name for backward compat
            single = wa_cfg.get("group_name", "")
            if single and single not in group_names:
                group_names.append(single)
            if not group_names:
                results.append({"platform": "whatsapp", "status": "error", "error": "whatsapp.group_names required"})
                continue
            for gname in group_names:
                r = whatsapp_connect.send_message_to_group(gname, text)
                results.append({"platform": "whatsapp", "group": gname, **r})

        else:
            results.append({"platform": platform, "status": "error", "error": "Unknown platform or not implemented yet."})

    # Persist a simple log
    _log_post(results, text)
    return {"results": results, "timestamp": _now_iso()}


def _log_post(results: list, text: str):
    """Append a JSON line to daily post log."""
    log_path = os.path.join(DATA_DIR, "post_log.jsonl")
    entry = {"time": _now_iso(), "text_preview": text[:120], "results": results}
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


@app.get("/api/post-log")
def api_post_log(limit: int = Query(50, ge=1, le=200)):
    """Read recent posting activity."""
    log_path = os.path.join(DATA_DIR, "post_log.jsonl")
    if not os.path.exists(log_path):
        return {"entries": []}
    entries = []
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except Exception:
                    pass
    return {"entries": entries[-limit:]}


@app.post("/api/whatsapp/send")
async def api_whatsapp_send(request: Request):
    """Standalone WhatsApp send endpoint."""
    body = await request.json()
    group_name = body.get("group_name", "")
    message = body.get("message", "")
    if not group_name or not message:
        raise HTTPException(status_code=400, detail="group_name and message are required")
    result = whatsapp_connect.send_message_to_group(group_name, message)
    if result.get("status") != "sent":
        raise HTTPException(status_code=502, detail=result.get("error", "Send failed"))
    return result


@app.get("/api/whatsapp/health")
def api_whatsapp_health():
    """Check WhatsApp Web session health (heartbeat pulse)."""
    return whatsapp_connect.check_session_health("local_test_user")


# ─── Content generation APIs ───────────────────────────────────────────────

@app.post("/api/images/generate")
async def api_generate_image(request: Request):
    body = await request.json()
    prompt = body.get("prompt", "")
    if not prompt:
        raise HTTPException(status_code=400, detail="prompt is required")

    result = image_gen.generate_image(prompt)
    if not result.get("ok"):
        raise HTTPException(status_code=502, detail=result.get("error", "Image generation failed"))

    return FileResponse(result["output_path"], media_type="image/png")


@app.post("/api/tts/generate")
async def api_generate_tts(request: Request):
    body = await request.json()
    text = body.get("text", "")
    voice = body.get("voice", "autumn")
    if not text:
        raise HTTPException(status_code=400, detail="text is required")

    result = groq_tts.generate_speech(text, voice=voice)
    if not result.get("ok"):
        raise HTTPException(status_code=502, detail=result.get("error", "TTS generation failed"))

    return FileResponse(result["output_path"], media_type="audio/wav")


# ─── Analytics APIs ────────────────────────────────────────────────────────

@app.get("/api/analytics/overview")
def api_analytics_overview():
    """High-level stats: connections, content generated, users."""
    # Count connections
    connection_counts = {"connected": 0, "total": 0}
    platforms = [
        x_connect, meta_connect, youtube_connect, reddit_connect,
        threads_connect, minds_connect, vk_connect, instagram_graph_connect, linkedin_connect, google_drive, whatsapp_connect, telegram_connect,
        whatsapp_business_connect,
    ]
    for platform in platforms:
        connection_counts["total"] += 1
        try:
            status = platform.get_connection_status("local_test_user")
            if status.get("status") == "connected":
                connection_counts["connected"] += 1
        except Exception:
            pass

    # Count generated content
    img_dir = os.path.join(DATA_DIR, "generated_images")
    tts_dir = os.path.join(DATA_DIR, "tts_output")
    image_count = len(glob.glob(os.path.join(img_dir, "*"))) if os.path.exists(img_dir) else 0
    audio_count = len(glob.glob(os.path.join(tts_dir, "*"))) if os.path.exists(tts_dir) else 0

    return {
        "platforms": connection_counts,
        "content_generated": {"images": image_count, "audio": audio_count, "total": image_count + audio_count},
        "timestamp": _now_iso(),
    }


@app.get("/api/analytics/connections")
def api_analytics_connections():
    """Per-platform connection status for charting."""
    platforms = [
        ("X", x_connect),
        ("Meta", meta_connect),
        ("YouTube", youtube_connect),
        ("Reddit", reddit_connect),
        ("Threads", threads_connect),
        ("Minds", minds_connect),
        ("VK", vk_connect),
        ("Instagram", instagram_connect),
        ("LinkedIn", linkedin_connect),
        ("Google Drive", google_drive),
        ("WhatsApp", whatsapp_connect),
        ("Telegram", telegram_connect),
        ("WhatsApp Business", whatsapp_business_connect),
    ]
    results = []
    for name, module in platforms:
        try:
            status = module.get_connection_status("local_test_user")
            results.append({"name": name, "status": status.get("status", "unknown")})
        except Exception:
            results.append({"name": name, "status": "error"})
    return {"platforms": results, "timestamp": _now_iso()}


@app.get("/api/analytics/content-history")
def api_analytics_content_history():
    """List recently generated images and audio files."""
    img_dir = os.path.join(DATA_DIR, "generated_images")
    tts_dir = os.path.join(DATA_DIR, "tts_output")

    images = []
    if os.path.exists(img_dir):
        for p in sorted(glob.glob(os.path.join(img_dir, "*")), key=os.path.getmtime, reverse=True)[:20]:
            images.append({"name": os.path.basename(p), "path": p, "size": os.path.getsize(p), "created": datetime.fromtimestamp(os.path.getmtime(p), tz=timezone.utc).isoformat()})

    audio = []
    if os.path.exists(tts_dir):
        for p in sorted(glob.glob(os.path.join(tts_dir, "*")), key=os.path.getmtime, reverse=True)[:20]:
            audio.append({"name": os.path.basename(p), "path": p, "size": os.path.getsize(p), "created": datetime.fromtimestamp(os.path.getmtime(p), tz=timezone.utc).isoformat()})

    return {"images": images, "audio": audio}


# ─── File serving ──────────────────────────────────────────────────────────

@app.get("/generated/{filename}")
def serve_generated_image(filename: str):
    path = os.path.join(DATA_DIR, "generated_images", filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path)


@app.get("/audio/{filename}")
def serve_generated_audio(filename: str):
    path = os.path.join(DATA_DIR, "tts_output", filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path)


@app.get("/static/whatsapp_qr.png")
def serve_whatsapp_qr():
    """Serve the current WhatsApp QR code image."""
    path = os.path.join(DATA_DIR, "whatsapp_qr.png")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="No QR code available. Start WhatsApp connect first.")
    return FileResponse(path)


# â”€â”€â”€ Approval Workflow â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@app.post("/api/queue/create")
async def api_queue_create(request: Request, db: Session = Depends(get_db)):
    """Create a queued post awaiting approval."""
    body = await request.json()
    client_id = body.get("client_id", "local_test_user")
    platforms = body.get("platforms", [])
    content = body.get("content", {})
    text = content.get("text", "")
    image_url = content.get("image_url")
    consultant_email = body.get("consultant_email")
    consultant_tg = body.get("consultant_telegram_chat_id")

    entry = create_queued_post(
        db=db,
        client_id=client_id,
        platforms=platforms,
        text=text,
        image_url=image_url,
        consultant_email=consultant_email,
        consultant_telegram_chat_id=consultant_tg,
    )

    if consultant_email:
        send_approval_request(
            to=consultant_email,
            post_text=text,
            platforms=platforms,
            image_url=image_url,
            approval_url=build_approval_url(entry.approval_token),
            reject_url=build_reject_url(entry.approval_token),
            preview_url=build_preview_url(entry.preview_token),
            client_name=client_id,
        )

    if consultant_tg:
        telegram_approval.send_approval_request(
            chat_id=consultant_tg,
            post_text=text,
            platforms=platforms,
            image_url=image_url,
            approval_token=entry.approval_token,
            client_name=client_id,
        )

    return {
        "status": "queued",
        "queue_id": entry.id,
        "approval_url": build_approval_url(entry.approval_token),
        "preview_url": build_preview_url(entry.preview_token),
    }


@app.get("/approve/{token}")
def approve_queued_post(token: str, db: Session = Depends(get_db)):
    entry = get_post_by_token(db, token, "approval")
    if not entry:
        raise HTTPException(status_code=404, detail="Token not found or expired")
    if entry.status != "pending":
        return {"status": entry.status, "message": "This post has already been processed."}

    approve_post(db, entry)
    platforms = json.loads(entry.platforms)
    text = entry.text or ""
    image_url = entry.image_url
    results = []

    for platform in platforms:
        if platform == "x":
            r = x_connect.post_tweet("local_test_user", text)
        elif platform == "facebook":
            r = meta_connect.post_text("local_test_user", text)
        elif platform == "threads":
            r = threads_connect.post_text("local_test_user", text)
        elif platform == "linkedin":
            r = linkedin_connect.post_text("local_test_user", text)
        elif platform == "instagram":
            if image_url:
                r = instagram_connect.post_image("local_test_user", image_url, text)
            else:
                r = {"status": "error", "error": "image_url required for Instagram"}
        elif platform == "whatsapp":
            r = whatsapp_connect.send_message("local_test_user", text)
        elif platform == "telegram":
            r = telegram_connect.send_message("local_test_user", text)
        else:
            r = {"status": "error", "error": f"Unknown platform: {platform}"}
        results.append({"platform": platform, **r})

    mark_posted(db, entry, json.dumps(results))

    if entry.consultant_email:
        send_approved_confirmation(
            to=entry.consultant_email,
            post_text=text,
            platforms=platforms,
            result_summary=f"Posted to {len([r for r in results if r['status']=='posted'])} of {len(results)} platforms",
        )

    return {"status": "approved_and_posted", "results": results, "message": "Post approved and published successfully."}


@app.get("/reject/{token}")
def reject_queued_post(token: str, reason: str = None, db: Session = Depends(get_db)):
    entry = get_post_by_token(db, token, "approval")
    if not entry:
        raise HTTPException(status_code=404, detail="Token not found or expired")
    if entry.status != "pending":
        return {"status": entry.status, "message": "This post has already been processed."}

    reject_post(db, entry, reason)
    if entry.consultant_email:
        send_rejected_notice(to=entry.consultant_email, post_text=entry.text or "", reason=reason)
    return {"status": "rejected", "message": "Post rejected." + (f" Reason: {reason}" if reason else "")}


@app.get("/preview/{token}")
def preview_queued_post(token: str, db: Session = Depends(get_db)):
    entry = get_post_by_token(db, token, "preview")
    if not entry:
        raise HTTPException(status_code=404, detail="Preview not found or expired")
    platforms = json.loads(entry.platforms)
    badges = " ".join(f'<span class="badge">{p.title()}</span>' for p in platforms)
    img_tag = f'<img src="{entry.image_url}" class="img">' if entry.image_url else ''
    return HTMLResponse(content=f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Post Preview</title>
<style>body{{font-family:sans-serif;max-width:600px;margin:40px auto;padding:0 20px;color:#1a1a2e;}}
.card{{border:1px solid #e5e7eb;border-radius:12px;padding:24px;box-shadow:0 4px 12px rgba(0,0,0,0.05);}}
.platforms{{display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap;}}
.badge{{padding:4px 12px;border-radius:20px;background:#eff6ff;color:#1d4ed8;font-size:0.8rem;font-weight:600;}}
.text{{font-size:1.1rem;line-height:1.6;margin:16px 0;}}
.img{{max-width:100%;border-radius:8px;margin-top:12px;}}
.actions{{margin-top:24px;display:flex;gap:12px;}}
.btn{{padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:600;color:#fff;display:inline-block;}}
.approve{{background:#10b981;}} .reject{{background:#ef4444;}}
</style></head><body>
<div class="card"><div class="platforms">{badges}</div>
<p class="text">{entry.text or "(No text)"}</p>{img_tag}
<div class="actions"><a href="/approve/{entry.approval_token}" class="btn approve">Approve</a>
<a href="/reject/{entry.approval_token}" class="btn reject">Reject</a></div>
<p style="font-size:0.8rem;color:#9ca3af;margin-top:16px;">This preview link expires in 24 hours.</p>
</div></body></html>""")


@app.post("/api/telegram/approval-webhook")
async def telegram_approval_webhook(request: Request):
    body = await request.json()
    if "callback_query" in body:
        result = telegram_approval.handle_callback(body["callback_query"])
        return {"ok": True, "result": result}
    if "message" in body and body["message"].get("text", "").startswith("/start"):
        chat_id = body["message"]["chat"]["id"]
        telegram_approval._api("sendMessage", {"chat_id": chat_id, "text": "Welcome to SMPF approval bot. Your chat ID is: " + str(chat_id)})
        return {"ok": True}
    return {"ok": True}


@app.get("/api/queue/status/{client_id}")
def api_queue_status(client_id: str, db: Session = Depends(get_db)):
    entries = db.query(PostQueue).filter(PostQueue.client_id == client_id).order_by(PostQueue.created_at.desc()).limit(20).all()
    return {"entries": [{"id": e.id, "platforms": json.loads(e.platforms), "text": e.text, "status": e.status, "created_at": e.created_at.isoformat() if e.created_at else None, "approved_at": e.approved_at.isoformat() if e.approved_at else None} for e in entries]}
