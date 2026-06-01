"""Cryptographic primitives for the MFA server.

Modules:

* ``vault``     - AES-256-GCM encryption of OTP secrets at rest.
* ``passwords`` - Argon2id password / backup-code hashing.
* ``hotp``      - RFC 4226 HOTP, implemented from scratch.
* ``totp``      - RFC 6238 TOTP on top of HOTP.
"""
