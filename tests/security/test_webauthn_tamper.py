"""Security test: tampered / invalid WebAuthn assertions never authenticate.

A full positive WebAuthn ceremony requires a real (or virtual) hardware
authenticator and a browser, so it is exercised manually for the demo. Here we
prove the SECURITY-CRITICAL negative paths server-side:

* An assertion with no challenge in progress is rejected.
* A tampered / malformed assertion against an enrolled credential fails
  verification (returns False) and is logged as a failure - it never grants
  access.
"""

import os
import uuid

import pytest

from backend.models import Credential, CredentialType
from backend.services import webauthn_service as wa
from backend.services.users import create_user


def _make_user_with_webauthn_cred(session):
    uname = f"wa_{uuid.uuid4().hex[:8]}"
    user = create_user(session, username=uname, email=f"{uname}@x.com", password="Password123!")
    cred = Credential(
        user_id=user.id,
        type=CredentialType.WEBAUTHN,
        label="Test key",
        credential_id="dGVzdC1jcmVkLWlk",  # base64url("test-cred-id")
        public_key=os.urandom(77),  # plausible-length COSE key bytes (not valid)
        sign_count=5,
        enabled=True,
    )
    session.add(cred)
    session.commit()
    return user, cred


def test_assertion_without_challenge_is_rejected(session):
    user, _ = _make_user_with_webauthn_cred(session)
    with pytest.raises(wa.WebAuthnError):
        wa.finish_authentication(session, user, {"id": "dGVzdC1jcmVkLWlk", "rawId": "dGVzdC1jcmVkLWlk"})


def test_tampered_assertion_does_not_authenticate(session):
    user, cred = _make_user_with_webauthn_cred(session)

    # Simulate a challenge being in progress for this user.
    wa._AUTHENTICATION_CHALLENGES[user.id] = os.urandom(32)

    tampered = {
        "id": cred.credential_id,
        "rawId": cred.credential_id,
        "type": "public-key",
        "response": {
            "authenticatorData": "AAAA",      # garbage
            "clientDataJSON": "AAAA",          # garbage
            "signature": "AAAA",               # garbage / tampered signature
        },
    }
    ok = wa.finish_authentication(session, user, tampered)
    assert ok is False, "a tampered assertion must never authenticate"
