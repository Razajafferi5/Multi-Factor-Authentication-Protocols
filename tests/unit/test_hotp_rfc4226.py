"""Validate our HOTP implementation against RFC 4226 Appendix D test vectors.

These assert our from-scratch code produces the EXACT values published in the
RFC - the authoritative correctness proof for HOTP.
"""

from backend.crypto import hotp
from tests.vectors.rfc_vectors import HOTP_SECRET, HOTP_VECTORS


def test_hotp_matches_rfc4226_appendix_d():
    for counter, expected in HOTP_VECTORS.items():
        actual = hotp.generate(HOTP_SECRET, counter, digits=6, algorithm="SHA1")
        assert actual == expected, f"counter={counter}: {actual} != {expected}"


def test_dynamic_truncation_offset_logic():
    # The truncation offset is the low 4 bits of the final HMAC byte; build a
    # digest whose last nibble is 5 and confirm we read from offset 5.
    digest = bytes(range(20))  # last byte = 19 -> low nibble = 3
    # bytes[3..6] = 03 04 05 06; top bit of 0x03 is clear so value = 0x03040506
    value = hotp.dynamic_truncation(digest, digits=10)
    assert value == 0x03040506 % (10 ** 10)


def test_hotp_verify_with_resync_window():
    # Server expects counter 3 but client is at counter 6: a look-ahead of 5
    # should still match and report the next counter as 7.
    code = hotp.generate(HOTP_SECRET, 6)
    matched, next_counter = hotp.verify(HOTP_SECRET, code, counter=3, look_ahead=5)
    assert matched is True
    assert next_counter == 7


def test_hotp_verify_rejects_out_of_window():
    code = hotp.generate(HOTP_SECRET, 20)
    matched, next_counter = hotp.verify(HOTP_SECRET, code, counter=3, look_ahead=5)
    assert matched is False
    assert next_counter == 3
