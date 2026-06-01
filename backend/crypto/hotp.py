"""RFC 4226 - HMAC-Based One-Time Password (HOTP), implemented from scratch.

Reference: https://www.rfc-editor.org/rfc/rfc4226

This module deliberately uses ONLY the Python standard library (``hmac``,
``hashlib``, ``struct``, ``base64``). It does NOT use ``pyotp`` or any other
OTP library - that is a hard requirement of the assignment. ``pyotp`` appears
only in the test suite as an independent cross-validation oracle.

The HOTP algorithm (RFC 4226 Section 5.3)::

    HOTP(K, C) = Truncate(HMAC-SHA-1(K, C))

where:

* ``K`` is the shared secret key.
* ``C`` is an 8-byte big-endian counter.
* ``Truncate`` is the dynamic truncation function of Section 5.3.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import struct

# Map algorithm names to hashlib constructors. RFC 4226 specifies SHA-1; RFC
# 6238 (TOTP) extends OTP to SHA-256 / SHA-512, so we support all three here so
# TOTP can reuse this code.
_ALGORITHMS = {
    "SHA1": hashlib.sha1,
    "SHA256": hashlib.sha256,
    "SHA512": hashlib.sha512,
}


def normalize_secret(secret: str | bytes) -> bytes:
    """Decode a shared secret into raw key bytes.

    Authenticator apps exchange secrets as Base32 (RFC 4648) text, so a string
    input is treated as Base32 (case-insensitive, padding optional). Raw bytes
    are returned unchanged.
    """
    if isinstance(secret, (bytes, bytearray)):
        return bytes(secret)
    cleaned = secret.strip().replace(" ", "").upper()
    # Base32 requires the input length to be a multiple of 8; pad with '='.
    padding = (-len(cleaned)) % 8
    cleaned += "=" * padding
    return base64.b32decode(cleaned, casefold=True)


def dynamic_truncation(hmac_digest: bytes, digits: int = 6) -> int:
    """Dynamic Truncation (RFC 4226 Section 5.3).

    Steps, quoting the RFC:

    1. Let ``offset = low-order 4 bits of the last byte`` of the HMAC result.
    2. Read the 4 bytes starting at ``offset`` as a big-endian integer.
    3. Mask off the most-significant bit to get a 31-bit positive number
       (``Snum``), avoiding sign/endianness ambiguity.
    4. The HOTP value is ``Snum mod 10**digits``.
    """
    # Step 1: offset is the low 4 bits of the final byte.
    offset = hmac_digest[-1] & 0x0F

    # Step 2 & 3: take 4 bytes from offset, drop the top bit (31-bit value).
    binary = (
        ((hmac_digest[offset] & 0x7F) << 24)
        | ((hmac_digest[offset + 1] & 0xFF) << 16)
        | ((hmac_digest[offset + 2] & 0xFF) << 8)
        | (hmac_digest[offset + 3] & 0xFF)
    )

    # Step 4: reduce modulo 10**digits to get the final code.
    return binary % (10 ** digits)


def generate(
    secret: str | bytes,
    counter: int,
    digits: int = 6,
    algorithm: str = "SHA1",
) -> str:
    """Compute the HOTP value for ``(secret, counter)``.

    Args:
        secret: Base32 string or raw key bytes.
        counter: Moving counter ``C`` (non-negative integer).
        digits: Number of output digits (RFC default 6; 6-8 typical).
        algorithm: One of ``SHA1`` / ``SHA256`` / ``SHA512``.

    Returns:
        The zero-padded OTP as a string of length ``digits``.
    """
    if counter < 0:
        raise ValueError("counter must be non-negative")
    algo = _ALGORITHMS.get(algorithm.upper())
    if algo is None:
        raise ValueError(f"unsupported algorithm: {algorithm!r}")

    key = normalize_secret(secret)

    # Counter is encoded as an 8-byte (64-bit) big-endian value (Section 5.1).
    counter_bytes = struct.pack(">Q", counter)

    # HMAC-SHA-1 (or SHA-256/512) over the counter (Section 5.2).
    digest = hmac.new(key, counter_bytes, algo).digest()

    code = dynamic_truncation(digest, digits)
    return str(code).zfill(digits)


def verify(
    secret: str | bytes,
    code: str,
    counter: int,
    digits: int = 6,
    algorithm: str = "SHA1",
    look_ahead: int = 0,
) -> tuple[bool, int]:
    """Verify an HOTP ``code`` against the expected ``counter``.

    Supports a resynchronisation window (RFC 4226 Section 7.4): the server may
    look ahead up to ``look_ahead`` counter values to tolerate the client's
    counter having advanced (e.g. button mashing on a hardware token).

    Returns:
        ``(matched, next_counter)``. On success ``next_counter`` is the counter
        value *after* the matched one, which the caller should persist. On
        failure ``next_counter`` equals the input ``counter`` unchanged.
    """
    code = str(code).strip()
    for offset in range(look_ahead + 1):
        candidate = generate(secret, counter + offset, digits, algorithm)
        # Constant-time comparison to avoid timing side channels.
        if hmac.compare_digest(candidate, code):
            return True, counter + offset + 1
    return False, counter
