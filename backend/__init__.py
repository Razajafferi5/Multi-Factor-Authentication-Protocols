"""MFA Authentication Server backend package.

A university Information Security capstone implementing a multi-factor
authentication server with:

* RFC 4226 (HOTP) and RFC 6238 (TOTP) implemented from scratch (no pyotp).
* AES-256-GCM encrypted secret vault and Argon2id password hashing.
* WebAuthn/FIDO2, push-approval simulation and single-use backup codes.
* An AI anomaly-detection layer (IsolationForest + Claude explanations).

The package is split into:

* ``crypto``   - cryptographic primitives (vault, hotp, totp, passwords).
* ``models``   - SQLAlchemy ORM models.
* ``services`` - business logic shared by the REST API and the dashboard.
* ``routes``   - Flask blueprints exposing the REST API.
* ``utils``    - small helpers (device fingerprint, geo math).
"""
