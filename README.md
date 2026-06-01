# MFA Authentication Server

A multi-factor authentication (MFA) server built for an Information Security
capstone. It implements one-time-password algorithms **from the RFCs by hand**,
encrypts all shared secrets at rest, logs every authentication attempt, and runs
an **AI anomaly-detection layer** over that log. A **Streamlit** admin dashboard
visualises users, the auth log, anomaly alerts and analytics, and is deployable
to **Streamlit Community Cloud**.

---

## Highlights (what to look at first)

| Area | File(s) |
|------|---------|
| HOTP from scratch (RFC 4226) | [`backend/crypto/hotp.py`](backend/crypto/hotp.py) |
| TOTP from scratch (RFC 6238) | [`backend/crypto/totp.py`](backend/crypto/totp.py) |
| AES-256-GCM secret vault | [`backend/crypto/vault.py`](backend/crypto/vault.py) |
| Argon2id password hashing | [`backend/crypto/passwords.py`](backend/crypto/passwords.py) |
| Anomaly features + IsolationForest + Claude | [`backend/services/anomaly/`](backend/services/anomaly/) |
| WebAuthn/FIDO2 (real verification) | [`backend/services/webauthn_service.py`](backend/services/webauthn_service.py) |
| RFC test vectors + pyotp oracle | [`tests/vectors/`](tests/vectors/), [`tests/oracle/`](tests/oracle/) |
| Security test suite | [`tests/security/`](tests/security/) |
| Streamlit dashboard | [`dashboard/streamlit_app.py`](dashboard/streamlit_app.py) |

> **OTP is implemented by hand.** `pyotp` appears **only** in
> [`tests/oracle/test_pyotp_cross_validation.py`](tests/oracle/test_pyotp_cross_validation.py)
> as an independent reference oracle. Production code never imports it.

---

## Features

- **Password factor** (first level): Argon2id-hashed, never reversible.
- **TOTP** (RFC 6238): SHA1/SHA256/SHA512, configurable digits and time step,
  QR-code enrollment via `otpauth://` provisioning URIs, replay protection.
- **HOTP** (RFC 4226): counter-based with a resynchronisation window.
- **Push approval** (simulated device): pending challenge -> approve/deny -> poll.
- **FIDO2 / WebAuthn**: real server-side attestation + assertion verification
  with signature-counter clone detection (via `py_webauthn`).
- **Backup codes**: single-use, Argon2id-hashed at rest.
- **Brute-force protection**: sliding-window lockout + CAPTCHA trigger.
- **AI anomaly layer**: per-login feature extraction (geo distance, impossible
  travel, new device, unusual hour, failed-attempt burst), per-user
  IsolationForest scoring, and a Claude-generated plain-language explanation
  that **degrades gracefully** to a feature summary if the LLM is unavailable.
- **Streamlit admin dashboard**: users, auth log, anomaly alerts, analytics.

---

## Architecture

```
Streamlit dashboard ──HTTP──> Flask REST API ──> Services ──> SQLite
        │                                            │
        └────────── EMBEDDED (in-process) ───────────┘
                                                     │
                                            crypto (hotp/totp/vault)
                                            anomaly (features/IF/LLM)
```

The service layer is framework-agnostic, so the dashboard can either call the
REST API over HTTP (production-shaped) or import the services in-process
(`EMBEDDED=1`, handy for a single Streamlit Cloud container).

---

## Setup

Requires Python 3.11+.

```bash
python -m venv .venv
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env        # then edit .env
```

Generate a master key for the secret vault and put it in `.env` as `MASTER_KEY`:

```bash
python -c "import os,base64; print(base64.b64encode(os.urandom(32)).decode())"
```

(Optional) set `ANTHROPIC_API_KEY` in `.env` to enable Claude explanations;
without it the system uses the graceful feature-summary fallback.

---

## Run

### 1. Seed demo data (recommended)

```bash
python -m scripts.seed
```

Creates synthetic users plus a realistic login history with injected anomalies
(impossible travel, new device, failed-attempt bursts) so the AI layer and
dashboard have something to show. All scores are computed by the real model.

### 2. Start the API

```bash
flask --app backend.app run        # http://localhost:5000
# or:  python -m backend
```

### 3. Start the dashboard

```bash
streamlit run dashboard/streamlit_app.py
```

By default the dashboard talks to the API at `API_BASE_URL`. To run everything
in one process (no separate API), set `EMBEDDED=1` in the environment.

---

## API quick reference

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/register` | Create account (password factor) |
| POST | `/api/login` | Verify password, report required MFA factors |
| POST | `/api/mfa/totp/enroll/start` | Begin TOTP enrollment (returns QR + URI) |
| POST | `/api/mfa/totp/enroll/verify` | Confirm TOTP with first code |
| POST | `/api/mfa/totp/verify` | Verify a TOTP code |
| POST | `/api/mfa/hotp/enroll/start` \| `/verify` | HOTP enrollment |
| POST | `/api/mfa/hotp/verify` | Verify an HOTP code (resync window) |
| POST | `/api/mfa/push/challenge` | Create push challenge |
| POST | `/api/mfa/push/mock-device/<id>/<approve\|deny>` | Simulated device action |
| GET  | `/api/mfa/push/poll/<id>` | Poll challenge status |
| POST | `/api/mfa/webauthn/register/begin` \| `/finish` | FIDO2 registration |
| POST | `/api/mfa/webauthn/authenticate/begin` \| `/finish` | FIDO2 assertion |
| POST | `/api/mfa/backup/generate` \| `/verify` | Backup codes |
| GET  | `/api/mfa/captcha` | Issue a (simulated) CAPTCHA |
| GET/POST/PATCH | `/api/admin/users` | User management |
| GET  | `/api/admin/events` | Auth log (filters: `user_id`, `flagged_only`) |
| GET  | `/api/admin/analytics` | Aggregated metrics for charts |

Example: enroll and verify TOTP

```bash
curl -X POST localhost:5000/api/register -H "Content-Type: application/json" \
  -d '{"username":"dave","email":"dave@x.com","password":"Password123!"}'

curl -X POST localhost:5000/api/mfa/totp/enroll/start -H "Content-Type: application/json" \
  -d '{"user_id":1}'
# -> returns secret, otpauth_uri, qr_data_uri
```

---

## Tests

Run the full suite:

```bash
pytest
```

Capture real output to a timestamped evidence file (for the report):

```bash
python -m scripts.capture_test_results
# writes test_evidence/report_<UTC>.txt
```

What the tests cover:

- **RFC vectors**: HOTP (RFC 4226 Appendix D) and TOTP (RFC 6238 Appendix B)
  exact published values, all three hash algorithms.
- **pyotp oracle**: our codes match an independent implementation byte-for-byte.
- **Vault**: round-trip, unique nonces, tamper detection, AAD binding.
- **Security**: TOTP replay rejected, brute-force lockout, secrets encrypted at
  rest (raw DB read contains no plaintext), WebAuthn tamper/no-challenge
  rejection.
- **Anomaly**: feature extraction, cold-start flagging, LLM graceful fallback.
- **API flow**: register -> login -> enroll -> verify over the HTTP layer.

---

## Deploy to Streamlit Community Cloud

1. Push this repo to GitHub.
2. Create a new Streamlit app with main file `dashboard/streamlit_app.py`.
3. In **Settings -> Secrets**, paste one of the configurations from
   [`.streamlit/secrets.toml.example`](.streamlit/secrets.toml.example):
   - **Remote API**: set `EMBEDDED="0"` and `API_BASE_URL` to a deployed Flask
     instance (e.g. on Render/Railway).
   - **Single-container demo**: set `EMBEDDED="1"`, `MASTER_KEY`, `SECRET_KEY`
     and optionally `ANTHROPIC_API_KEY`.

> Note: Streamlit Cloud has an ephemeral filesystem. For persistent demo data,
> point `DATABASE_URL` at a hosted database, or re-run the seed on startup.

---

## Course deliverables (dataset, figures, report)

```bash
python -m scripts.seed              # demo users + login history (run first)
python -m scripts.export_dataset    # -> dataset/auth_events.csv
python -m scripts.figures           # -> docs/figures/*.png (diagrams + charts)
python -m scripts.generate_report   # -> docs/Technical_Report.docx
```

The technical report is auto-generated as a formatted Word document (Times New
Roman 12pt, 1.5 spacing, 1 inch margins, numbered figures/tables/equations,
IEEE references, Courier New code listings, page numbers from the Introduction).
After opening it in Word, right-click the Table of Contents and choose "Update
Field" to populate page numbers. Edit the prose in
[`scripts/report_content.py`](scripts/report_content.py) and the cover-page
placeholders (university, team, roll numbers, supervisor) there too.

Supporting docs:

- [`docs/USER_MANUAL.md`](docs/USER_MANUAL.md) - full setup/run/operate guide.
- [`docs/VIDEO_DEMO_SCRIPT.md`](docs/VIDEO_DEMO_SCRIPT.md) - timed 10-minute demo script.

## Known limitations

See [`SECURITY_NOTES.md`](SECURITY_NOTES.md) for an honest accounting of
limitations (single master key, simulated push/CAPTCHA, unauthenticated admin
API for the demo, in-memory WebAuthn challenge store, etc.).
