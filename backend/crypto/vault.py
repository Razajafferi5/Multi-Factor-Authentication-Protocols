"""AES-256-GCM secret vault for encrypting OTP shared secrets at rest.

Design
------
* A single 32-byte *server master key* (``MASTER_KEY``) is the root of trust.
* From it we derive a 256-bit AES key with HKDF-SHA256 (RFC 5869), using a
  fixed application-specific ``info`` string so the derived key is domain
  separated from any other use of the master key.
* Each secret is sealed with AES-256-GCM (NIST SP 800-38D), an AEAD cipher that
  provides both confidentiality and integrity. A fresh random 96-bit nonce is
  generated per encryption and prepended to the ciphertext+tag.

Wire format of a sealed blob::

    [ 12-byte nonce ][ ciphertext ][ 16-byte GCM tag ]

KEY-MANAGEMENT LIMITATION (documented honestly for the report):
A single master key encrypts every user's secret. There is no per-user key,
no HSM, and no key rotation. In production these secrets would live behind a
KMS / HSM with envelope encryption and rotation. See SECURITY_NOTES.md.
"""

from __future__ import annotations

import os

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from ..config import config

# Domain-separation label for HKDF. Changing this invalidates all ciphertexts.
_HKDF_INFO = b"mfa-server/aes-256-gcm/secret-vault/v1"
_NONCE_BYTES = 12  # 96-bit nonce is the GCM-recommended size.

# Cache an ephemeral key for test environments that don't set MASTER_KEY, so
# encrypt/decrypt round-trips remain consistent within a single process.
_EPHEMERAL_MASTER_KEY: bytes | None = None


def _master_key() -> bytes:
    """Resolve the 32-byte master key, generating an ephemeral one if needed.

    Production MUST set ``MASTER_KEY``. The ephemeral fallback exists only so
    tests and first-run demos work without configuration; it is regenerated
    each process and therefore cannot decrypt previously stored secrets.
    """
    global _EPHEMERAL_MASTER_KEY
    key = config.master_key_bytes()
    if key is not None:
        return key
    if _EPHEMERAL_MASTER_KEY is None:
        _EPHEMERAL_MASTER_KEY = os.urandom(32)
    return _EPHEMERAL_MASTER_KEY


def _derive_aes_key(master_key: bytes) -> bytes:
    """Derive a 256-bit AES key from the master key via HKDF-SHA256."""
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,  # 256-bit key for AES-256.
        salt=None,  # No salt: master key is already high-entropy random.
        info=_HKDF_INFO,
    )
    return hkdf.derive(master_key)


def encrypt(plaintext: bytes, associated_data: bytes | None = None) -> bytes:
    """Seal ``plaintext`` and return ``nonce || ciphertext || tag``.

    ``associated_data`` is authenticated but not encrypted (e.g. a user id can
    be bound to the ciphertext to prevent swapping secrets between users).
    """
    if not isinstance(plaintext, (bytes, bytearray)):
        raise TypeError("plaintext must be bytes")
    aes_key = _derive_aes_key(_master_key())
    aesgcm = AESGCM(aes_key)
    nonce = os.urandom(_NONCE_BYTES)
    sealed = aesgcm.encrypt(nonce, bytes(plaintext), associated_data)
    return nonce + sealed


def decrypt(blob: bytes, associated_data: bytes | None = None) -> bytes:
    """Open a blob produced by :func:`encrypt`.

    Raises ``cryptography.exceptions.InvalidTag`` if the ciphertext or the
    associated data has been tampered with, or the wrong key is used.
    """
    if blob is None or len(blob) <= _NONCE_BYTES:
        raise ValueError("ciphertext blob is too short to contain a nonce")
    aes_key = _derive_aes_key(_master_key())
    aesgcm = AESGCM(aes_key)
    nonce, sealed = blob[:_NONCE_BYTES], blob[_NONCE_BYTES:]
    return aesgcm.decrypt(nonce, sealed, associated_data)


def encrypt_str(plaintext: str, associated_data: bytes | None = None) -> bytes:
    """Convenience wrapper to seal a UTF-8 string (e.g. a Base32 secret)."""
    return encrypt(plaintext.encode("utf-8"), associated_data)


def decrypt_str(blob: bytes, associated_data: bytes | None = None) -> str:
    """Convenience wrapper returning a UTF-8 string."""
    return decrypt(blob, associated_data).decode("utf-8")
