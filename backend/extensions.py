"""Shared infrastructure objects (database engine + session factory).

We use SQLAlchemy directly (not Flask-SQLAlchemy) so the exact same data layer
can be imported by both the Flask API and the Streamlit dashboard when running
in EMBEDDED mode.
"""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, scoped_session, sessionmaker

from .config import config


class Base(DeclarativeBase):
    """Declarative base shared by all ORM models."""


# ``check_same_thread`` must be disabled for SQLite under Flask's threaded dev
# server and Streamlit, which both touch the session from multiple threads.
_engine_kwargs: dict = {"future": True}
if config.database_url.startswith("sqlite"):
    _engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(config.database_url, **_engine_kwargs)

# scoped_session gives a thread-local session, appropriate for web servers.
SessionLocal = scoped_session(
    sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
)


def init_db() -> None:
    """Create all tables. Idempotent; safe to call on every startup."""
    # Import models for side effects so they register on ``Base.metadata``.
    from . import models  # noqa: F401  (registration side effect)

    Base.metadata.create_all(bind=engine)


def get_session():
    """Return the thread-local session (convenience accessor)."""
    return SessionLocal()
