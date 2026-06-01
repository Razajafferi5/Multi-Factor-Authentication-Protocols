"""MFA enrollment + verification routes (TOTP, HOTP, backup codes, CAPTCHA)."""

from __future__ import annotations

from flask import Blueprint, g, jsonify, request

from ..services import captcha, mfa
from ..utils.fingerprint import context_from_flask
from .helpers import error, json_body, require_user, with_session

mfa_bp = Blueprint("mfa", __name__, url_prefix="/api/mfa")


# --- TOTP -------------------------------------------------------------------
@mfa_bp.post("/totp/enroll/start")
@with_session
def totp_enroll_start():
    body = json_body()
    user, err = require_user(g.session, body)
    if err:
        return err
    result = mfa.start_totp_enrollment(
        g.session, user,
        issuer=body.get("issuer", "MFA Capstone"),
        algorithm=body.get("algorithm", "SHA1"),
        digits=int(body.get("digits", 6)),
        period=int(body.get("period", 30)),
    )
    return jsonify(result), 201


@mfa_bp.post("/totp/enroll/verify")
@with_session
def totp_enroll_verify():
    body = json_body()
    user, err = require_user(g.session, body)
    if err:
        return err
    try:
        cred = mfa.verify_totp_enrollment(
            g.session, user, int(body["credential_id"]), body.get("code", "")
        )
    except (KeyError, mfa.MFAError) as exc:
        return error(str(exc) or "credential_id and code required", 400)
    return jsonify({"enabled": cred.enabled, "credential": cred.to_dict()}), 200


@mfa_bp.post("/totp/verify")
@with_session
def totp_verify():
    body = json_body()
    user, err = require_user(g.session, body)
    if err:
        return err
    context = context_from_flask(request, body)
    try:
        ok = mfa.verify_totp(g.session, user, body.get("code", ""), context=context)
    except mfa.MFAError as exc:
        return error(str(exc), 400)
    return jsonify({"verified": ok}), (200 if ok else 401)


# --- HOTP -------------------------------------------------------------------
@mfa_bp.post("/hotp/enroll/start")
@with_session
def hotp_enroll_start():
    body = json_body()
    user, err = require_user(g.session, body)
    if err:
        return err
    result = mfa.start_hotp_enrollment(
        g.session, user,
        algorithm=body.get("algorithm", "SHA1"),
        digits=int(body.get("digits", 6)),
    )
    return jsonify(result), 201


@mfa_bp.post("/hotp/enroll/verify")
@with_session
def hotp_enroll_verify():
    body = json_body()
    user, err = require_user(g.session, body)
    if err:
        return err
    try:
        cred = mfa.verify_hotp_enrollment(
            g.session, user, int(body["credential_id"]), body.get("code", "")
        )
    except (KeyError, mfa.MFAError) as exc:
        return error(str(exc) or "credential_id and code required", 400)
    return jsonify({"enabled": cred.enabled, "credential": cred.to_dict()}), 200


@mfa_bp.post("/hotp/verify")
@with_session
def hotp_verify():
    body = json_body()
    user, err = require_user(g.session, body)
    if err:
        return err
    context = context_from_flask(request, body)
    try:
        ok = mfa.verify_hotp(
            g.session, user, body.get("code", ""),
            resync_window=int(body.get("resync_window", 5)), context=context,
        )
    except mfa.MFAError as exc:
        return error(str(exc), 400)
    return jsonify({"verified": ok}), (200 if ok else 401)


# --- Backup codes -----------------------------------------------------------
@mfa_bp.post("/backup/generate")
@with_session
def backup_generate():
    body = json_body()
    user, err = require_user(g.session, body)
    if err:
        return err
    codes = mfa.generate_backup_codes(g.session, user, count=int(body.get("count", 10)))
    return jsonify({"codes": codes}), 201


@mfa_bp.post("/backup/verify")
@with_session
def backup_verify():
    body = json_body()
    user, err = require_user(g.session, body)
    if err:
        return err
    context = context_from_flask(request, body)
    ok = mfa.verify_backup_code_for_user(
        g.session, user, body.get("code", ""), context=context
    )
    return jsonify({"verified": ok}), (200 if ok else 401)


# --- CAPTCHA ----------------------------------------------------------------
@mfa_bp.get("/captcha")
def captcha_challenge():
    """Issue a (simulated) CAPTCHA challenge + signed token."""
    return jsonify(captcha.issue_challenge()), 200
