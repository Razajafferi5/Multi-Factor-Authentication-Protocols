# User Manual - MFA Authentication Server

This manual explains how to install, run, operate, and test the MFA server and
its admin dashboard. It targets two audiences: an evaluator running the project
locally, and an administrator using the dashboard.

---

## 1. Prerequisites

- Python 3.11 or newer (developed on 3.12).
- Git (to clone the repository).
- A modern web browser (for the dashboard and any WebAuthn demo).

## 2. Installation

```bash
# 1. Clone and enter the project
git clone [INSERT GITHUB REPOSITORY LINK HERE]
cd "IS Project Raza"

# 2. Create and activate a virtual environment
python -m venv .venv
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# macOS / Linux:
# source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
copy .env.example .env        # Windows
# cp .env.example .env        # macOS/Linux
```

Generate and set a master key in `.env`:

```bash
python -c "import os,base64; print(base64.b64encode(os.urandom(32)).decode())"
# paste the value into MASTER_KEY=... in .env
```

Optionally set `ANTHROPIC_API_KEY` to enable AI-written anomaly explanations;
without it, the system shows a deterministic feature summary instead.

## 3. Seeding demonstration data

```bash
python -m scripts.seed
```

This creates sample users and a realistic login history with injected
anomalies (impossible travel, failed-attempt bursts) so the dashboard and AI
layer have meaningful content. All anomaly scores are computed by the real
model.

## 4. Running the server and dashboard

Open two terminals (both with the virtual environment activated):

```bash
# Terminal 1 - REST API
flask --app backend.app run            # serves http://localhost:5000

# Terminal 2 - admin dashboard
streamlit run dashboard/streamlit_app.py
```

To run everything in a single process (no separate API), set `EMBEDDED=1` in
the environment before launching Streamlit.

## 5. Using the dashboard

The dashboard has five pages (no login by design for the demo):

- Users: create accounts, enable/disable them, and see enrolled factors.
- MFA Log: the full authentication audit trail, filterable per user with a
  drill-down summary.
- Anomalies: flagged events with the LLM explanation or a feature fallback.
- Analytics: KPI metrics, attempts over time, success/fail ratio, attempts by
  factor, and a geographic login map with flagged events highlighted.
- Test Evidence: the latest captured pytest output.

## 6. Exercising the factors (API)

Register and enroll TOTP:

```bash
curl -X POST localhost:5000/api/register -H "Content-Type: application/json" \
  -d '{"username":"dave","email":"dave@x.com","password":"Password123!"}'

curl -X POST localhost:5000/api/mfa/totp/enroll/start \
  -H "Content-Type: application/json" -d '{"user_id":1}'
# Returns secret, otpauth_uri, and a QR data URI. Scan the QR with an
# authenticator app, then verify the first code:

curl -X POST localhost:5000/api/mfa/totp/enroll/verify \
  -H "Content-Type: application/json" \
  -d '{"user_id":1,"credential_id":1,"code":"123456"}'
```

Push approval (simulated device):

```bash
# Create a challenge
curl -X POST localhost:5000/api/mfa/push/challenge -H "Content-Type: application/json" -d '{"user_id":1}'
# Approve from the mock device
curl -X POST localhost:5000/api/mfa/push/mock-device/<challenge_id>/approve
# Poll for the result
curl localhost:5000/api/mfa/push/poll/<challenge_id>
```

## 7. Running tests and capturing evidence

```bash
pytest                                   # run the full suite
python -m scripts.capture_test_results   # write test_evidence/report_<UTC>.txt
```

## 8. Generating the dataset and report

```bash
python -m scripts.export_dataset    # -> dataset/auth_events.csv
python -m scripts.figures           # -> docs/figures/*.png
python -m scripts.generate_report   # -> docs/Technical_Report.docx
```

After opening `Technical_Report.docx` in Microsoft Word, right-click the Table
of Contents and choose "Update Field" to populate page numbers.

## 9. Troubleshooting

- "MASTER_KEY must decode to exactly 32 bytes": regenerate the key as in step 2.
- Dashboard shows no data: run `python -m scripts.seed` first, or check
  `API_BASE_URL` / `EMBEDDED` settings.
- Report build reports the file is locked: close it in Word/preview and re-run
  `python -m scripts.generate_report`.
