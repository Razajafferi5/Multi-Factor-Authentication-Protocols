"""Published test vectors copied verbatim from the RFC appendices.

These are the authoritative reference values used to prove our hand-written
implementations are correct.

* RFC 4226 Appendix D - HOTP test values.
  https://www.rfc-editor.org/rfc/rfc4226#appendix-D
* RFC 6238 Appendix B - TOTP test values.
  https://www.rfc-editor.org/rfc/rfc6238#appendix-B
"""

# RFC 4226 uses the ASCII secret "12345678901234567890" (20 bytes).
HOTP_SECRET = b"12345678901234567890"

# HOTP(secret, counter) -> 6-digit value, counters 0..9 (Appendix D).
HOTP_VECTORS = {
    0: "755224",
    1: "287082",
    2: "359152",
    3: "969429",
    4: "338314",
    5: "254676",
    6: "287922",
    7: "162583",
    8: "399871",
    9: "520489",
}

# RFC 6238 Appendix B uses a different ASCII seed per algorithm, all 8-digit,
# T0=0, X=30.
TOTP_SECRETS = {
    "SHA1": b"12345678901234567890",
    "SHA256": b"12345678901234567890123456789012",
    "SHA512": b"1234567890123456789012345678901234567890123456789012345678901234",
}

# (unix_time, {algorithm: expected_8_digit_code})
TOTP_VECTORS = [
    (59, {"SHA1": "94287082", "SHA256": "46119246", "SHA512": "90693936"}),
    (1111111109, {"SHA1": "07081804", "SHA256": "68084774", "SHA512": "25091201"}),
    (1111111111, {"SHA1": "14050471", "SHA256": "67062674", "SHA512": "99943326"}),
    (1234567890, {"SHA1": "89005924", "SHA256": "91819424", "SHA512": "93441116"}),
    (2000000000, {"SHA1": "69279037", "SHA256": "90698825", "SHA512": "38618901"}),
    (20000000000, {"SHA1": "65353130", "SHA256": "77737706", "SHA512": "47863826"}),
]
