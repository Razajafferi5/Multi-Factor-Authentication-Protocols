"""CROSS-VALIDATION AGAINST A REFERENCE IMPLEMENTATION (pyotp).

============================================================================
IMPORTANT: ``pyotp`` is used here ONLY as an INDEPENDENT REFERENCE ORACLE to
confirm that our from-scratch RFC 4226 / RFC 6238 implementations
(``backend/crypto/hotp.py`` and ``backend/crypto/totp.py``) produce IDENTICAL
codes for the same key / counter / time.

pyotp is a TEST-ONLY dependency. It is NEVER imported by production code. The
production server generates and verifies every OTP with our own code.
============================================================================
"""

import base64
import os

import pyotp  # test-only reference oracle

from backend.crypto import hotp, totp


def _random_base32_secret(n_bytes: int = 20) -> str:
    return base64.b32encode(os.urandom(n_bytes)).decode("ascii").rstrip("=")


def test_hotp_agrees_with_pyotp_across_counters():
    secret = _random_base32_secret()
    reference = pyotp.HOTP(secret)
    for counter in range(0, 50):
        ours = hotp.generate(secret, counter, digits=6, algorithm="SHA1")
        theirs = reference.at(counter)
        assert ours == theirs, f"counter={counter}: ours={ours} pyotp={theirs}"


def test_totp_agrees_with_pyotp_across_timestamps():
    secret = _random_base32_secret()
    reference = pyotp.TOTP(secret)  # SHA1, 6 digits, 30s step (defaults)
    for ts in (0, 30, 59, 1234567890, 1700000000, 1999999999):
        ours = totp.generate(secret, for_time=ts, digits=6, step=30, algorithm="SHA1")
        theirs = reference.at(ts)
        assert ours == theirs, f"ts={ts}: ours={ours} pyotp={theirs}"


def test_totp_agrees_with_pyotp_sha256_8_digits():
    secret = _random_base32_secret(32)
    reference = pyotp.TOTP(secret, digits=8, digest="sha256")
    for ts in (0, 30, 1700000123, 1888888888):
        ours = totp.generate(secret, for_time=ts, digits=8, step=30, algorithm="SHA256")
        theirs = reference.at(ts)
        assert ours == theirs, f"ts={ts}: ours={ours} pyotp={theirs}"
