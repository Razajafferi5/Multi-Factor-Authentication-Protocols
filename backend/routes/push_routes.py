"""Push-approval routes: create challenge, mock device response, poll."""

from __future__ import annotations

from flask import Blueprint, g, jsonify, request

from ..services import push
from ..utils.fingerprint import context_from_flask
from .helpers import error, json_body, require_user, with_session

push_bp = Blueprint("push", __name__, url_prefix="/api/mfa/push")


@push_bp.post("/challenge")
@with_session
def create_challenge():
    body = json_body()
    user, err = require_user(g.session, body)
    if err:
        return err
    context = context_from_flask(request, body)
    challenge = push.create_challenge(
        g.session, user, ttl_seconds=int(body.get("ttl_seconds", 120)), context=context
    )
    return jsonify(challenge.to_dict()), 201


@push_bp.post("/mock-device/<challenge_id>/<action>")
@with_session
def mock_device(challenge_id: str, action: str):
    """Simulated device endpoint: action is 'approve' or 'deny'."""
    if action not in ("approve", "deny"):
        return error("action must be 'approve' or 'deny'", 400)
    try:
        challenge = push.respond(g.session, challenge_id, approve=(action == "approve"))
    except push.PushError as exc:
        return error(str(exc), 409)
    return jsonify(challenge.to_dict()), 200


@push_bp.get("/poll/<challenge_id>")
@with_session
def poll(challenge_id: str):
    context = context_from_flask(request, {})
    try:
        result = push.poll(g.session, challenge_id, context=context)
    except push.PushError as exc:
        return error(str(exc), 404)
    return jsonify(result), 200
