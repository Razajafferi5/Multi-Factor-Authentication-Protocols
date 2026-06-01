"""Registration and password (first-factor) login routes."""

from __future__ import annotations

from flask import Blueprint, g, jsonify, request

from ..services import auth
from ..services.users import UserError
from ..utils.fingerprint import context_from_flask
from .helpers import error, json_body, with_session

auth_bp = Blueprint("auth", __name__, url_prefix="/api")


@auth_bp.post("/register")
@with_session
def register():
    """Create a new account (password factor)."""
    body = json_body()
    try:
        user = auth.register(
            g.session,
            username=body.get("username", ""),
            email=body.get("email", ""),
            password=body.get("password", ""),
        )
    except UserError as exc:
        return error(str(exc), 409)
    return jsonify({"user": user.to_dict()}), 201


@auth_bp.post("/login")
@with_session
def login():
    """Verify the password factor; report required MFA factors."""
    body = json_body()
    context = context_from_flask(request, body)
    try:
        result = auth.login_password(
            g.session,
            username=body.get("username", ""),
            password=body.get("password", ""),
            context=context,
            captcha_token=body.get("captcha_token"),
            captcha_answer=body.get("captcha_answer"),
        )
    except auth.AuthError as exc:
        # Surface lockout/captcha status the service attached to the error.
        msg = str(exc)
        code = 423 if "locked" in msg else (428 if "captcha" in msg else 401)
        return error(msg, code, **(exc.status or {}))
    return jsonify(result), 200
