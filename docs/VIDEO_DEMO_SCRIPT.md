# 10-Minute Video Demo Script

A timed walkthrough for recording the required demonstration video. Rehearse
once so the timing fits within ten minutes. Have two terminals and a browser
ready before recording.

Pre-flight (do BEFORE recording):

```bash
python -m scripts.seed
python -m scripts.capture_test_results
python -m scripts.figures
flask --app backend.app run          # terminal 1
streamlit run dashboard/streamlit_app.py   # terminal 2
```

---

## 0:00 - 0:45  Introduction

- State the project: a multi-factor authentication server with an AI login
  anomaly layer, built for the Information Security capstone.
- Name the team and the factors supported: password, TOTP, HOTP, push,
  FIDO2/WebAuthn, plus backup codes.

## 0:45 - 2:30  OTP implemented from scratch (the differentiator)

- Open `backend/crypto/hotp.py` and `backend/crypto/totp.py`.
- Explain that HOTP/TOTP are implemented directly from RFC 4226 / RFC 6238,
  not from a library; point to the dynamic-truncation function.
- Run the RFC-vector and oracle tests live:

```bash
pytest tests/unit/test_hotp_rfc4226.py tests/unit/test_totp_rfc6238.py tests/oracle -v
```

- Emphasise: our codes match the published RFC values and an independent
  reference oracle exactly.

## 2:30 - 4:00  Secrets at rest + password hashing

- Open `backend/crypto/vault.py`; explain AES-256-GCM with an HKDF-derived key
  and per-encryption nonce, and Argon2id for passwords.
- Run the security tests:

```bash
pytest tests/security -v
```

- Call out the secret-at-rest test (raw DB bytes contain no plaintext) and the
  replay test (a reused TOTP code is rejected).

## 4:00 - 6:00  Live factor flows (API)

- Register a user and start TOTP enrollment; show the returned QR / otpauth URI.
- Scan with an authenticator app (or generate a code) and verify it.
- Demonstrate the push factor: create a challenge, approve it on the mock
  device endpoint, then poll and show it complete.
- Briefly show backup-code generation and a single-use redemption.

## 6:00 - 8:00  AI anomaly layer + dashboard

- Switch to the Streamlit dashboard.
- Analytics page: show KPIs, attempts over time, success/fail ratio, and the
  geographic login map with flagged (impossible-travel) events highlighted.
- Anomalies page: open a flagged event and read its explanation (LLM prose, or
  the deterministic feature summary if no API key is set).
- Explain graceful degradation: the system still scores and flags without the
  LLM.

## 8:00 - 9:15  Hardening + evidence

- Trigger several failed logins to show CAPTCHA requirement and lockout.
- Open the Test Evidence page to show the captured pytest output, then mention
  the exported dataset (`dataset/auth_events.csv`).

## 9:15 - 10:00  Wrap-up

- Summarise: standards-compliant crypto, multiple factors, encrypted secrets,
  explainable anomaly detection, and honest limitations (single master key,
  simulated push/CAPTCHA, unauthenticated admin for the demo).
- Point to the technical report and the GitHub repository.
