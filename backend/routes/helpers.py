"""Shared helpers for route blueprints (session handling, error JSON)."""

from __future__ import annotations

from functools import wraps

from flask import g, jsonify, request

from ..extensions import SessionLocal
from ..services.users import get_user


def with_session(view):
    """Provide a per-request SQLAlchemy session on ``g`` and clean it up.

    Using a decorator keeps each view focused on logic while guaranteeing the
    scoped session is removed (returning the connection) after the request.
    """

    @wraps(view)
    def wrapper(*args, **kwargs):
        g.session = SessionLocal()
        try:
            return view(*args, **kwargs)
        finally:
            SessionLocal.remove()

    return wrapper


def json_body() -> dict:
    """Return the request JSON body as a dict (empty dict if none)."""
    return request.get_json(silent=True) or {}


def error(message: str, status: int = 400, **extra):
    """Build a consistent JSON error response."""
    payload = {"error": message}
    payload.update(extra)
    return jsonify(payload), status


def require_user(session, body: dict):
    """Resolve ``user_id`` from the body into a User or raise a 404-style error."""
    user_id = body.get("user_id")
    if user_id is None:
        return None, error("user_id is required", 400)
    user = get_user(session, int(user_id))
    if user is None:
        return None, error("user not found", 404)
    return user, None
