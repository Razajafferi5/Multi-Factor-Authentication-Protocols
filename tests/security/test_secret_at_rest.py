"""Security test: TOTP secrets are never stored in plaintext.

We enroll a TOTP credential, then read the raw bytes back from the database and
assert the plaintext Base32 secret does NOT appear anywhere in the stored blob,
and that the stored blob decrypts back to the original only via the vault.
"""

import uuid

from sqlalchemy import text

from backend.crypto import vault
from backend.extensions import engine
from backend.services import mfa
from backend.services.users import create_user


def test_totp_secret_encrypted_at_rest(session):
    uname = f"atrest_{uuid.uuid4().hex[:8]}"
    user = create_user(session, username=uname, email=f"{uname}@x.com", password="Password123!")
    start = mfa.start_totp_enrollment(session, user)
    plaintext_secret = start["secret"]
    cred_id = start["credential_id"]

    # Read the raw stored bytes directly via Core SQL (bypassing the ORM).
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT secret_ciphertext FROM credentials WHERE id = :id"),
            {"id": cred_id},
        ).first()

    stored_blob = row[0]
    assert stored_blob is not None

    # The plaintext secret must not be findable in the stored bytes.
    assert plaintext_secret.encode("utf-8") not in stored_blob
    assert plaintext_secret not in stored_blob.decode("latin-1", errors="ignore")

    # And it must decrypt back correctly through the vault (with the AAD used).
    aad = f"user:{user.id}:factor:totp".encode("utf-8")
    assert vault.decrypt_str(stored_blob, aad) == plaintext_secret
