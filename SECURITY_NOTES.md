# Security Notes & Known Limitations

This document records the security model and an **honest** list of limitations.
Stating these clearly is deliberate: it feeds the report's limitations section
and pre-empts common viva questions. Nothing here is hidden.

---

## What is real vs simulated

| Component | Status | Notes |
|-----------|--------|-------|
| HOTP (RFC 4226) | **Real, from scratch** | `backend/crypto/hotp.py`, stdlib only |
| TOTP (RFC 6238) | **Real, from scratch** | `backend/crypto/totp.py`, multi-algorithm |
| AES-256-GCM vault | **Real** | `cryptography` AEAD, HKDF-derived key |
| Argon2id hashing | **Real** | `argon2-cffi`, passwords + backup codes |
| WebAuthn/FIDO2 | **Real verification** | `py_webauthn` verifies attestation + assertion + sign count |
| Push approval | **Simulated device** | Real state machine/TTL/poll; the "phone" is a mock endpoint |
| CAPTCHA | **Simulated** | HMAC-signed arithmetic challenge, not hCaptcha/reCAPTCHA |
| Geo location | **Client-supplied** | lat/lon provided in the request, not IP-resolved |

---

## Key management (most important limitation)

- A **single server master key** (`MASTER_KEY`) is the root of trust. From it
  we derive one AES-256 key (HKDF-SHA256) that encrypts **every** user's OTP
  secret.
- There is **no per-user key**, **no HSM/KMS**, and **no key rotation**.
- If `MASTER_KEY` leaks, all stored OTP secrets are compromised. If it is lost,
  all secrets become undecryptable.
- In production this should be envelope encryption backed by a KMS/HSM
  (per-secret data keys wrapped by a managed master key) with rotation.
- If `MASTER_KEY` is unset, the vault generates an **ephemeral** key per process
  (tests/first-run only). Such secrets cannot be decrypted after a restart.

## Password & backup-code storage

- Passwords and backup codes are hashed with **Argon2id**
  (`time_cost=3`, `memory_cost=64 MiB`, `parallelism=4`). Plaintext is never
  stored and is unrecoverable. Backup-code plaintext is shown to the user once.

## OTP secrets at rest

- TOTP/HOTP shared secrets are stored **only** as AES-256-GCM ciphertext with a
  random 96-bit nonce per encryption, plus an authentication tag.
- The ciphertext is bound to `user_id` + factor via GCM **associated data**, so
  a secret cannot be silently moved to another user/factor.
- Verified by `tests/security/test_secret_at_rest.py` (raw DB read contains no
  plaintext).

## Replay protection (TOTP)

- The last accepted time-step is recorded per credential; a code at or below it
  is rejected, so a still-valid code cannot be reused within its window.
- Verified by `tests/security/test_replay.py`.

## Brute-force protection

- Sliding-window failure counting over `auth_events`. After
  `LOCKOUT_MAX_FAILURES` within `LOCKOUT_WINDOW_SECONDS`, the account is locked
  for `LOCKOUT_DURATION_SECONDS`. A CAPTCHA is required once failures reach half
  the threshold, and failed CAPTCHA attempts still escalate toward the lock.
- Counting is per user. A distributed attack across many usernames is not fully
  mitigated here (would need per-IP and global rate limits / a WAF).

## WebAuthn specifics

- Attestation and assertion are verified server-side, including challenge
  binding, RP-ID/origin checks, and signature-counter regression (clone)
  detection.
- Demo/test authenticators may use `none` attestation (no hardware root of
  trust); we accept it and note it. A production deployment with a defined
  authenticator policy would enforce attestation formats/AAGUIDs.
- WebAuthn challenges are kept in an **in-memory** per-process dict. This is
  fine for a single process but would need a shared store (e.g. Redis) behind
  multiple workers. A full positive ceremony needs a real browser/authenticator
  and is demonstrated manually; automated tests cover the negative paths.

## Admin API / dashboard authentication

- For this capstone demo, the `/api/admin/*` endpoints and the Streamlit
  dashboard have **no authentication**, so the demo is easy to run and grade.
- In production these must sit behind admin authentication + RBAC, network
  restrictions, and audit logging of admin actions.

## LLM (Claude) usage and graceful degradation

- The LLM **only** explains real anomaly-engine output (features + score); it is
  not a general chatbot.
- Data sent to Anthropic for flagged events: the numeric feature values and the
  anomaly score. No raw passwords or secrets are sent.
- **Graceful degradation**: if the API key is missing, or the call errors/times
  out, scoring and flagging still happen and the dashboard shows a deterministic
  feature summary instead of prose. Verified by `tests/unit/test_anomaly.py`.

## Geolocation

- Latitude/longitude are supplied by the client request (deterministic, offline,
  demo-friendly) rather than resolved from IP via a third-party service that
  could fail on Streamlit Cloud. A real deployment would use a vetted
  IP-geolocation provider and treat client-supplied coordinates as untrusted.

## Transport security

- TLS termination is assumed to be handled by the deployment platform
  (Streamlit Cloud / the API host). The app does not implement TLS itself.

## Anomaly model scope

- IsolationForest is trained per-user on historical features at scoring time.
  With fewer than 8 historical events a deterministic rule-based fallback is
  used (cold start). Models are not persisted; they are cheap to refit for the
  data volumes in this project.
