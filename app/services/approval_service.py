"""Post queue and approval workflow for SMPF."""
import json, secrets, os
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.portal.models import PostQueue

APPROVAL_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "https://smpf.finwatchpro.net").rstrip("/")
TOKEN_TTL_HOURS = 24


def _generate_token():
    return secrets.token_urlsafe(32)


def create_queued_post(
    db: Session,
    client_id: str,
    platforms: list,
    text: str = None,
    image_url: str = None,
    image_path: str = None,
    consultant_email: str = None,
    consultant_telegram_chat_id: str = None,
):
    """Save a post to the queue and return tokens."""
    entry = PostQueue(
        client_id=client_id,
        platforms=json.dumps(platforms),
        text=text,
        image_url=image_url,
        image_path=image_path,
        status="pending",
        approval_token=_generate_token(),
        preview_token=_generate_token(),
        consultant_email=consultant_email,
        consultant_telegram_chat_id=consultant_telegram_chat_id,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=TOKEN_TTL_HOURS),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def get_post_by_token(db: Session, token: str, token_type: str = "approval"):
    """Lookup post by approval or preview token."""
    if token_type == "approval":
        return db.query(PostQueue).filter(PostQueue.approval_token == token).first()
    return db.query(PostQueue).filter(PostQueue.preview_token == token).first()


def approve_post(db: Session, entry: PostQueue):
    """Mark approved, return the entry for posting."""
    entry.status = "approved"
    entry.approved_at = datetime.now(timezone.utc)
    db.commit()
    return entry


def reject_post(db: Session, entry: PostQueue, reason: str = None):
    """Mark rejected with optional reason."""
    entry.status = "rejected"
    entry.rejection_reason = reason
    db.commit()
    return entry


def mark_posted(db: Session, entry: PostQueue, result_json: str):
    """Mark as posted with result log."""
    entry.status = "posted"
    entry.posted_at = datetime.now(timezone.utc)
    entry.posted_result = result_json
    db.commit()
    return entry


def get_pending_for_client(db: Session, client_id: str, limit: int = 50):
    return (
        db.query(PostQueue)
        .filter(PostQueue.client_id == client_id)
        .order_by(PostQueue.created_at.desc())
        .limit(limit)
        .all()
    )


def build_approval_url(token: str) -> str:
    return f"{APPROVAL_BASE_URL}/approve/{token}"


def build_reject_url(token: str) -> str:
    return f"{APPROVAL_BASE_URL}/reject/{token}"


def build_preview_url(token: str) -> str:
    return f"{APPROVAL_BASE_URL}/preview/{token}"
