# SMPF v1 — app/portal/database.py — 2026-08-24
"""Database setup for the portal.

SQLite on purpose — it's a single file (data/smpf.db), no server to
install or run, no admin rights needed. This matches what was agreed:
simulate locally on SQLite now, move to MySQL/Postgres only once this
is on real hosting with real paying clients.
"""
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import DATA_DIR

DB_PATH = os.path.join(DATA_DIR, "smpf.db")
os.makedirs(DATA_DIR, exist_ok=True)

# check_same_thread=False is needed because FastAPI can use a different
# thread per request; SQLite is fine with this for a single-file,
# low-concurrency local setup like this one.
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency — yields a DB session, closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create tables if they don't exist yet. Safe to call every startup."""
    from app.portal import models  # noqa: F401 — ensures models are registered before create_all
    Base.metadata.create_all(bind=engine)
