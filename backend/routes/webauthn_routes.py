"""FIDO2 / WebAuthn routes: registration + authentication ceremonies."""

from __future__ import annotations

from flask import Blueprint, g, jsonify, request

from ..services import webauthn_service as wa
from ..utils.fingerprint import context_from_flask
from .helpers import error, json_body, require_user, with_session

webauthn_bp = Blueprint("webauthn", __name__, url_prefix="/api/mfa/webauthn")


@webauthn_bp.post("/register/begin")
@with_session
def register_begin():
    body = json_body()
    user, err = require_user(g.session, body)
    if err:
        return err
    return jsonify(wa.begin_registration(g.session, user)), 200


@webauthn_bp.post("/register/finish")
@with_session
def register_finish():
    body = json_body()
    user, err = require_user(g.session, body)
    if err:
        return err
    try:
        cred = wa.finish_registration(g.session, user, body.get("credential", {}))
    except wa.WebAuthnError as exc:
        return error(str(exc), 400)
    return jsonify({"enabled": cred.enabled, "credential_id": cred.credential_id}), 201


@webauthn_bp.post("/authenticate/begin")
@with_session
def authenticate_begin():
    body = json_body()
    user, err = require_user(g.session, body)
    if err:
        return err
    try:
        return jsonify(wa.begin_authentication(g.session, user)), 200
    except wa.WebAuthnError as exc:
        return error(str(exc), 400)


@webauthn_bp.post("/authenticate/finish")
@with_session
def authenticate_finish():
    body = json_body()
    user, err = require_user(g.session, body)
    if err:
        return err
    context = context_from_flask(request, body)
    try:
        ok = wa.finish_authentication(
            g.session, user, body.get("credential", {}), context=context
        )
    except wa.WebAuthnError as exc:
        return error(str(exc), 400)
    return jsonify({"verified": ok}), (200 if ok else 401)
