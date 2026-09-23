"""Email service with trickle/throttle for bulk sends.

Requires SMTP credentials in .env:
  SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, FROM_EMAIL

If not configured, falls back to logging the email body (dev mode).
"""
import os, smtplib, json, time, threading, queue as queue_module
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timezone

SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
FROM_EMAIL = os.environ.get("FROM_EMAIL", "noreply@finwatchpro.net")
BASE_URL = os.environ.get("PUBLIC_BASE_URL", "https://smpf.finwatchpro.net").rstrip("/")

# ─── Trickle feed settings ───
# Domain SMTP is more trusted, but still throttle to avoid rate limits.
TRICKLE_BATCH_SIZE = int(os.environ.get("SMTP_BATCH_SIZE", "8"))      # emails per batch
TRICKLE_DELAY_SEC = int(os.environ.get("SMTP_BATCH_DELAY", "30"))     # seconds between batches
TRICKLE_MAX_PER_HOUR = int(os.environ.get("SMTP_MAX_PER_HOUR", "200")) # hard ceiling

# In-memory queue + worker thread
_email_queue = queue_module.Queue()
_worker_thread = None
_worker_lock = threading.Lock()

_sent_count_lock = threading.Lock()
_sent_count = 0          # count this session
_hour_start = time.time()  # reset window


def _can_send() -> bool:
    """Check if we're within rate limits."""
    global _sent_count, _hour_start
    with _sent_count_lock:
        now = time.time()
        if now - _hour_start > 3600:
            _sent_count = 0
            _hour_start = now
        return _sent_count < TRICKLE_MAX_PER_HOUR


def _record_sent(n: int = 1):
    """Record that n emails were sent."""
    global _sent_count, _hour_start
    with _sent_count_lock:
        now = time.time()
        if now - _hour_start > 3600:
            _sent_count = 0
            _hour_start = now
        _sent_count += n


@dataclass
class _QueuedEmail:
    to: str
    subject: str
    html_body: str
    text_body: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


def _smtp_send(e: _QueuedEmail) -> bool:
    """Actually dispatch one email via SMTP."""
    if not SMTP_HOST or not SMTP_USER or not SMTP_PASSWORD:
        print(f"[EMAIL FALLBACK] To: {e.to}\nSubject: {e.subject}\n---\n{e.html_body[:500]}\n---")
        return True

    msg = MIMEMultipart("alternative")
    msg["Subject"] = e.subject
    msg["From"] = FROM_EMAIL
    msg["To"] = e.to

    if e.text_body:
        msg.attach(MIMEText(e.text_body, "plain", "utf-8"))
    msg.attach(MIMEText(e.html_body, "html", "utf-8"))

    # Add List-Unsubscribe header (helps deliverability)
    if e.metadata and "unsubscribe_url" in e.metadata:
        msg.add_header("List-Unsubscribe", f"<{e.metadata['unsubscribe_url']}>")

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(FROM_EMAIL, [e.to], msg.as_string())
        _record_sent(1)
        return True
    except Exception as exc:
        print(f"[EMAIL ERROR to {e.to}] {exc}")
        return False


def _worker_loop():
    """Background thread: drain queue in trickle batches."""
    while True:
        batch: List[_QueuedEmail] = []
        try:
            # Fill a batch (up to batch size) with non-blocking gets
            for _ in range(TRICKLE_BATCH_SIZE):
                item = _email_queue.get_nowait()
                if item is None:
                    return  # poison pill
                batch.append(item)
        except queue_module.Empty:
            pass

        if not batch:
            time.sleep(2)
            continue

        # Throttle: wait until hour window resets if at limit
        while not _can_send():
            print("[TRICKLE] Hourly limit reached, waiting 60s...")
            time.sleep(60)

        # Send the batch
        for e in batch:
            _smtp_send(e)

        # Delay before next batch
        if TRICKLE_DELAY_SEC > 0:
            time.sleep(TRICKLE_DELAY_SEC)


def _ensure_worker():
    """Start the background email worker if not already running."""
    global _worker_thread
    with _worker_lock:
        if _worker_thread is None or not _worker_thread.is_alive():
            _worker_thread = threading.Thread(target=_worker_loop, daemon=True)
            _worker_thread.start()
            print("[EMAIL] Trickle worker started")


def enqueue_email(to: str, subject: str, html_body: str, text_body: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> bool:
    """Queue an email for trickle delivery. Returns immediately."""
    _ensure_worker()
    _email_queue.put(_QueuedEmail(to=to, subject=subject, html_body=html_body, text_body=text_body, metadata=metadata))
    return True


def flush_queue(timeout: float = 30.0) -> Dict[str, Any]:
    """Block until queue is empty or timeout. Returns stats."""
    start = time.time()
    while time.time() - start < timeout:
        if _email_queue.empty():
            return {"status": "flushed", "pending": 0}
        time.sleep(1)
    return {"status": "timeout", "pending": _email_queue.qsize()}


def get_stats() -> Dict[str, Any]:
    """Current queue + rate stats."""
    with _sent_count_lock:
        return {
            "pending": _email_queue.qsize(),
            "sent_this_hour": _sent_count,
            "hourly_limit": TRICKLE_MAX_PER_HOUR,
            "batch_size": TRICKLE_BATCH_SIZE,
            "batch_delay_sec": TRICKLE_DELAY_SEC,
        }


# ─── High-level helpers ───


def send_approval_request(
    to: str,
    post_text: str,
    platforms: list,
    image_url: Optional[str],
    approval_url: str,
    reject_url: str,
    preview_url: str,
    client_name: str = "",
):
    platforms_str = ", ".join(platforms)
    subject = f"New post needs approval — {client_name or 'SMPF Client'}"

    html = f"""\
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Post Approval</title>
<style>
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;max-width:560px;margin:24px auto;padding:0 16px;color:#1a1a2e;line-height:1.5;}}
.card{{border:1px solid #e5e7eb;border-radius:12px;padding:20px;margin:16px 0;background:#f9fafb;}}
.meta{{color:#6b7280;font-size:0.875rem;margin-bottom:8px;}}
.text{{font-style:italic;margin:0;}}
img{{max-width:100%;border-radius:8px;margin-top:12px;}}
.actions{{text-align:center;margin:24px 0;}}
.btn{{display:inline-block;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:600;color:#fff;margin:0 6px;}}
.approve{{background:#10b981;}} .reject{{background:#ef4444;}}
.footer{{font-size:0.75rem;color:#9ca3af;text-align:center;margin-top:16px;}}
</style></head>
<body>
<h2 style="color:#3b82f6;">Post Approval Required</h2>
<p class="meta"><strong>Client:</strong> {client_name or 'Unknown'}<br><strong>Platforms:</strong> {platforms_str}</p>
<div class="card"><p class="text">{post_text or '(No text)'}</p></div>
{f'<img src="{image_url}" alt="Post image">' if image_url else ''}
<div class="actions">
<a href="{approval_url}" class="btn approve">APPROVE</a>
<a href="{reject_url}" class="btn reject">REJECT</a>
</div>
<p style="text-align:center;"><a href="{preview_url}">Preview how this will look</a></p>
<p class="footer">This link expires in 24 hours. Do not forward this email.</p>
</body></html>"""

    text = f"""\
Post Approval Required
Client: {client_name or 'Unknown'}
Platforms: {platforms_str}

{post_text or '(No text)'}

Approve: {approval_url}
Reject: {reject_url}
Preview: {preview_url}

Link expires in 24 hours.
"""

    enqueue_email(to, subject, html, text)


def send_approved_confirmation(to: str, post_text: str, platforms: list, result_summary: str):
    subject = "Your post has been approved and published"
    html = f"""\
<html><body style="font-family:sans-serif;max-width:600px;margin:20px auto;">
<h2 style="color:#10b981;">Post Published ✅</h2>
<p><strong>Platforms:</strong> {', '.join(platforms)}</p>
<div style="border:1px solid #e5e7eb;border-radius:8px;padding:16px;background:#f9fafb;">
<p style="margin:0;font-style:italic;">{post_text or '(No text)'}</p>
</div>
<p>{result_summary}</p>
</body></html>"""
    enqueue_email(to, subject, html)


def send_rejected_notice(to: str, post_text: str, reason: str = None):
    subject = "Your post was not approved"
    html = f"""\
<html><body style="font-family:sans-serif;max-width:600px;margin:20px auto;">
<h2 style="color:#ef4444;">Post Rejected</h2>
<div style="border:1px solid #e5e7eb;border-radius:8px;padding:16px;background:#f9fafb;">
<p style="margin:0;font-style:italic;">{post_text or '(No text)'}</p>
</div>
<p><strong>Reason:</strong> {reason or 'No reason provided.'}</p>
</body></html>"""
    enqueue_email(to, subject, html)


def send_bulk_newsletter(
    recipients: List[str],
    subject: str,
    html_body: str,
    text_body: Optional[str] = None,
    unsubscribe_url: Optional[str] = None,
):
    """Send newsletter to a list with trickle throttling.

    Usage:
        send_bulk_newsletter(
            recipients=["a@x.com", "b@x.com", ...],
            subject="SMPF Newsletter",
            html_body="<html>...</html>",
            unsubscribe_url="https://finwatchpro.net/unsubscribe?token=..."
        )
        stats = flush_queue(timeout=300)  # wait up to 5 min
    """
    meta = {"unsubscribe_url": unsubscribe_url} if unsubscribe_url else None
    for to in recipients:
        enqueue_email(to, subject, html_body, text_body, metadata=meta)
    return get_stats()
