"""Unit tests for the AES-256-GCM secret vault."""

import pytest
from cryptography.exceptions import InvalidTag

from backend.crypto import vault


def test_roundtrip_bytes():
    secret = b"super-secret-totp-seed"
    blob = vault.encrypt(secret)
    assert blob != secret  # actually encrypted
    assert vault.decrypt(blob) == secret


def test_roundtrip_str_helpers():
    secret = "JBSWY3DPEHPK3PXP"
    blob = vault.encrypt_str(secret)
    assert vault.decrypt_str(blob) == secret


def test_nonce_is_unique_per_encryption():
    blob1 = vault.encrypt(b"same plaintext")
    blob2 = vault.encrypt(b"same plaintext")
    # Different nonces -> different ciphertext for identical plaintext.
    assert blob1 != blob2


def test_tampered_ciphertext_fails_authentication():
    blob = bytearray(vault.encrypt(b"important"))
    blob[-1] ^= 0x01  # flip a bit in the GCM tag
    with pytest.raises(InvalidTag):
        vault.decrypt(bytes(blob))


def test_associated_data_must_match():
    blob = vault.encrypt(b"bound", associated_data=b"user:1")
    # Correct AAD decrypts.
    assert vault.decrypt(blob, associated_data=b"user:1") == b"bound"
    # Wrong AAD is rejected (prevents moving a secret between users).
    with pytest.raises(InvalidTag):
        vault.decrypt(blob, associated_data=b"user:2")
