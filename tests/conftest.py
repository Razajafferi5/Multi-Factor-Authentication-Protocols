"""Pytest configuration: isolated in-memory database + Flask test client.

Each test session gets its own temporary SQLite database and a configured
``MASTER_KEY`` so vault round-trips are deterministic, without touching any
real ``mfa.db`` or requiring environment setup.
"""

from __future__ import annotations

import base64
import os

import pytest

# Configure environment BEFORE importing backend modules (config reads env at
# import time). A throwaway file DB keeps state across the engine's connections.
os.environ.setdefault("MASTER_KEY", base64.b64encode(b"0" * 32).decode())
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_mfa.db")
os.environ.setdefault("ANTHROPIC_API_KEY", "")  # force LLM graceful fallback


@pytest.fixture(scope="session", autouse=True)
def _clean_db():
    """Start each test session from a fresh database file."""
    db_path = "./test_mfa.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    from backend.extensions import init_db

    init_db()
    yield
    # Leave the file for post-mortem inspection; ignore removal errors.
    try:
        os.remove(db_path)
    except OSError:
        pass


@pytest.fixture()
def session():
    from backend.extensions import SessionLocal

    s = SessionLocal()
    try:
        yield s
    finally:
        SessionLocal.remove()


@pytest.fixture()
def client():
    from backend.app import create_app

    app = create_app()
    app.config.update(TESTING=True)
    with app.test_client() as c:
        yield c
