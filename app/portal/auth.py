# SMPF v1 — app/portal/auth.py — 2026-08-24
"""Auth logic for the portal.

Password hashing uses hashlib.pbkdf2_hmac — pure Python standard
library, no native compilation, no admin rights needed to install.
(bcrypt is more common but can require a native compiler on some
Windows setups without admin rights — pbkdf2 avoids that entirely
while still being a real, salted, iterated hash, not plain text.)

Work-email rule: same principle as the earlier smma-os auth work,
applied correctly from the start here — the PRIMARY email is checked
against the free-domain blocklist, not just an optional secondary
field. That was a real bug found and fixed in the older codebase;
built right the first time here.
"""
import hashlib
import hmac
import os
import re
import secrets
from datetime import datetime, timedelta, timezone

PBKDF2_ITERATIONS = 260_000

FREE_EMAIL_DOMAINS = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "icloud.com",
    "protonmail.com", "aol.com", "mail.com", "yandex.com", "gmx.com",
    "live.com", "msn.com", "zoho.com", "inbox.com", "hotmail.co.uk",
    "yahoo.co.uk", "googlemail.com",
}

LOCKOUT_THRESHOLD = 5
LOCKOUT_MINUTES = 30


def hash_password(password: str) -> tuple[str, str]:
    """Returns (hash, salt), both hex strings, ready to store."""
    salt = secrets.token_hex(16)
    pw_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), PBKDF2_ITERATIONS
    ).hex()
    return pw_hash, salt


def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    """Constant-time-ish comparison via hashlib.compare_digest — avoids
    timing attacks that a plain == comparison would be vulnerable to."""
    check_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), PBKDF2_ITERATIONS
    ).hex()
    return hmac.compare_digest(check_hash, stored_hash)


def validate_work_email(email: str) -> tuple[bool, str]:
    """Returns (is_valid, error_message). Rejects free/consumer email
    domains — this is THE primary registration gate, applied to the
    actual account email, not an optional secondary field."""
    if not email or "@" not in email:
        return False, "A valid email address is required."

    domain = email.split("@")[-1].lower().strip()

    if domain in FREE_EMAIL_DOMAINS:
        return False, (
            f"Please register with a company email address, not a free "
            f"provider like {domain}. A company domain is required."
        )

    if "." not in domain:
        return False, "That doesn't look like a real domain."

    return True, ""


def validate_password_strength(password: str) -> tuple[bool, str]:
    if len(password) < 12:
        return False, "Password must be at least 12 characters."
    if not re.search(r"[A-Z]", password):
        return False, "Password must include an uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must include a lowercase letter."
    if not re.search(r"[0-9]", password):
        return False, "Password must include a number."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must include a special character."
    return True, ""


def is_locked_out(user) -> bool:
    if user.locked_until is None:
        return False
    locked_until = user.locked_until
    if locked_until.tzinfo is None:
        locked_until = locked_until.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) < locked_until


def record_failed_login(user, db):
    user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
    if user.failed_login_attempts >= LOCKOUT_THRESHOLD:
        user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_MINUTES)
    db.commit()


def reset_failed_logins(user, db):
    user.failed_login_attempts = 0
    user.locked_until = None
    db.commit()
