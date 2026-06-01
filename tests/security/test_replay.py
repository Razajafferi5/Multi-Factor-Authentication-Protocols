"""Security test: a TOTP code cannot be replayed within its validity window.

Reusing a still-valid code is the classic OTP replay attack. Our MFA service
records the last accepted time-step and rejects any code at or below it.
"""

import uuid

from backend.crypto import totp, vault
from backend.models import Credential, CredentialType
from backend.services import mfa
from backend.services.users import create_user


def _enroll_totp(session):
    uname = f"replay_{uuid.uuid4().hex[:8]}"
    user = create_user(session, username=uname, email=f"{uname}@x.com", password="Password123!")
    start = mfa.start_totp_enrollment(session, user)
    secret = start["secret"]
    code = totp.generate(secret, digits=6, step=30, algorithm="SHA1")
    mfa.verify_totp_enrollment(session, user, start["credential_id"], code)
    return user, secret


def test_totp_replay_is_rejected(session):
    user, secret = _enroll_totp(session)
    code = totp.generate(secret, digits=6, step=30, algorithm="SHA1")

    first = mfa.verify_totp(session, user, code)
    second = mfa.verify_totp(session, user, code)

    assert first is True, "first use of the code should succeed"
    assert second is False, "the same code must be rejected on replay"
