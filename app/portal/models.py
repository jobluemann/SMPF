# SMPF v1 — app/portal/models.py — 2026-08-24
"""Portal database models."""
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, Boolean

from app.portal.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    company_name = Column(String, nullable=True)
    password_hash = Column(String, nullable=False)
    password_salt = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True)

    # Account lockout, same pattern proven in the earlier smma-os auth work.
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)


class PostQueue(Base):
    __tablename__ = "post_queue"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(String, nullable=False, index=True)
    platforms = Column(String, nullable=False)  # JSON array as string
    text = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    image_path = Column(String, nullable=True)
    status = Column(String, default="pending", index=True)  # pending/approved/rejected/posted/expired
    approval_token = Column(String, unique=True, index=True, nullable=False)
    preview_token = Column(String, unique=True, index=True, nullable=False)
    consultant_email = Column(String, nullable=True)
    consultant_telegram_chat_id = Column(String, nullable=True)
    rejection_reason = Column(String, nullable=True)
    posted_result = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    approved_at = Column(DateTime, nullable=True)
    posted_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
