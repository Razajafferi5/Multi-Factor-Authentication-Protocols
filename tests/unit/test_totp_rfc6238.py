"""Validate our TOTP implementation against RFC 6238 Appendix B test vectors.

Covers all three algorithms (SHA1/SHA256/SHA512) at the exact timestamps and
8-digit outputs published in the RFC.
"""

import pytest

from backend.crypto import totp
from tests.vectors.rfc_vectors import TOTP_SECRETS, TOTP_VECTORS


@pytest.mark.parametrize("unix_time,expected", TOTP_VECTORS)
def test_totp_matches_rfc6238_appendix_b(unix_time, expected):
    for algorithm, code in expected.items():
        secret = TOTP_SECRETS[algorithm]
        actual = totp.generate(
            secret, for_time=unix_time, digits=8, step=30, algorithm=algorithm
        )
        assert actual == code, f"{algorithm}@{unix_time}: {actual} != {code}"


def test_totp_verify_accepts_within_window():
    secret = TOTP_SECRETS["SHA1"]
    code = totp.generate(secret, for_time=1111111111, digits=8, algorithm="SHA1")
    # A code generated 29 seconds earlier should still verify with window=1.
    assert totp.verify(
        secret, code, for_time=1111111111 + 29, digits=8, algorithm="SHA1", valid_window=1
    )


def test_totp_verify_rejects_outside_window():
    secret = TOTP_SECRETS["SHA1"]
    code = totp.generate(secret, for_time=1111111111, digits=8, algorithm="SHA1")
    # Two full steps later (60s) the code must be rejected with window=1.
    assert not totp.verify(
        secret, code, for_time=1111111111 + 65, digits=8, algorithm="SHA1", valid_window=1
    )
