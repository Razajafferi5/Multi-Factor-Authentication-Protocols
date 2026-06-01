"""FIDO2 / WebAuthn factor using the py_webauthn library.

This factor performs REAL server-side cryptographic verification:

* Registration: we generate ``PublicKeyCredentialCreationOptions``, then verify
  the authenticator's attestation response and store the resulting credential
  public key + sign count.
* Authentication: we generate a challenge, then verify the assertion signature
  against the stored public key and enforce the signature counter (clone
  detection, WebAuthn spec section 6.1.1).

What is REAL vs SIMULATED (stated honestly for the report):
* REAL: attestation/assertion signature verification, challenge binding,
  origin/RP-ID checks, sign-count regression detection - all done by the
  ``webauthn`` library against the actual response bytes.
* The only convenience is that demo/test authenticators may use ``none``
  attestation (no hardware root of trust), which we accept and note.

Challenges are kept in a short-lived in-memory store keyed by user id. For a
single-process deployment this is fine; a multi-process deployment would move
them to Redis. Documented in SECURITY_NOTES.md.
"""

from __future__ import annotations

import base64
import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import config
from ..models import Credential, CredentialType, User
from ..utils.fingerprint import RequestContext
from .events import log_auth_event

# webauthn (py_webauthn) imports. Kept at module level since it is a hard dep.
from webauthn import (
    generate_authentication_options,
    generate_registration_options,
    options_to_json,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers import base64url_to_bytes, bytes_to_base64url
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialDescriptor,
    UserVerificationRequirement,
)


class WebAuthnError(Exception):
    """User-facing WebAuthn error."""


# Ephemeral per-user challenge store: {user_id: b64url_challenge}.
_REGISTRATION_CHALLENGES: dict[int, bytes] = {}
_AUTHENTICATION_CHALLENGES: dict[int, bytes] = {}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------
def begin_registration(session: Session, user: User) -> dict:
    """Produce creation options for the browser's ``navigator.credentials.create``."""
    options = generate_registration_options(
        rp_id=config.webauthn_rp_id,
        rp_name=config.webauthn_rp_name,
        user_id=str(user.id).encode("utf-8"),
        user_name=user.username,
        user_display_name=user.email,
        authenticator_selection=AuthenticatorSelectionCriteria(
            user_verification=UserVerificationRequirement.PREFERRED,
        ),
    )
    _REGISTRATION_CHALLENGES[user.id] = options.challenge
    return json.loads(options_to_json(options))


def finish_registration(session: Session, user: User, credential: dict) -> Credential:
    """Verify the attestation response and persist the credential.

    ``credential`` is the JSON object returned by the browser from
    ``navigator.credentials.create``.
    """
    expected_challenge = _REGISTRATION_CHALLENGES.pop(user.id, None)
    if expected_challenge is None:
        raise WebAuthnError("no registration challenge in progress")

    try:
        verification = verify_registration_response(
            credential=credential,
            expected_challenge=expected_challenge,
            expected_rp_id=config.webauthn_rp_id,
            expected_origin=config.webauthn_rp_origin,
        )
    except Exception as exc:  # noqa: BLE001 - library raises various types
        raise WebAuthnError(f"attestation verification failed: {exc}") from exc

    cred = Credential(
        user_id=user.id,
        type=CredentialType.WEBAUTHN,
        label="Security key",
        credential_id=bytes_to_base64url(verification.credential_id),
        public_key=verification.credential_public_key,
        sign_count=verification.sign_count,
        enabled=True,
    )
    session.add(cred)
    session.commit()
    return cred


# ---------------------------------------------------------------------------
# Authentication (assertion)
# ---------------------------------------------------------------------------
def begin_authentication(session: Session, user: User) -> dict:
    """Produce request options for ``navigator.credentials.get``."""
    creds = _user_webauthn_credentials(session, user)
    if not creds:
        raise WebAuthnError("no webauthn credential enrolled")

    allow = [
        PublicKeyCredentialDescriptor(id=base64url_to_bytes(c.credential_id))
        for c in creds
    ]
    options = generate_authentication_options(
        rp_id=config.webauthn_rp_id,
        allow_credentials=allow,
        user_verification=UserVerificationRequirement.PREFERRED,
    )
    _AUTHENTICATION_CHALLENGES[user.id] = options.challenge
    return json.loads(options_to_json(options))


def finish_authentication(
    session: Session,
    user: User,
    credential: dict,
    *,
    context: RequestContext | None = None,
) -> bool:
    """Verify an assertion response; enforce the signature counter."""
    expected_challenge = _AUTHENTICATION_CHALLENGES.pop(user.id, None)
    if expected_challenge is None:
        raise WebAuthnError("no authentication challenge in progress")

    raw_id = credential.get("rawId") or credential.get("id")
    cred = session.scalar(
        select(Credential).where(
            Credential.user_id == user.id,
            Credential.type == CredentialType.WEBAUTHN,
            Credential.credential_id == raw_id,
        )
    )
    if cred is None:
        raise WebAuthnError("unknown credential id")

    success = False
    reason = None
    try:
        verification = verify_authentication_response(
            credential=credential,
            expected_challenge=expected_challenge,
            expected_rp_id=config.webauthn_rp_id,
            expected_origin=config.webauthn_rp_origin,
            credential_public_key=cred.public_key,
            credential_current_sign_count=cred.sign_count,
            require_user_verification=False,
        )
        # Clone-detection: the new sign count must strictly advance (unless the
        # authenticator reports 0, meaning it doesn't keep a counter).
        if verification.new_sign_count == 0 and cred.sign_count == 0:
            success = True
        elif verification.new_sign_count > cred.sign_count:
            success = True
        else:
            reason = "sign_count_regression"
        if success:
            cred.sign_count = verification.new_sign_count
            cred.last_used_at = _utcnow()
    except Exception as exc:  # noqa: BLE001
        reason = "assertion_invalid"
        success = False

    log_auth_event(
        session, factor="webauthn", success=success, user_id=user.id,
        username_attempted=user.username, reason=reason, context=context,
    )
    if success:
        session.commit()
    return success


def _user_webauthn_credentials(session: Session, user: User) -> list[Credential]:
    return list(
        session.scalars(
            select(Credential).where(
                Credential.user_id == user.id,
                Credential.type == CredentialType.WEBAUTHN,
                Credential.enabled.is_(True),
            )
        )
    )
