"""End-to-end API test: register -> login -> enroll TOTP -> verify (HTTP layer).

Drives the real Flask test client to prove the multi-factor flow works through
the REST API, not just the service layer.
"""

import uuid

from backend.crypto import totp


def test_full_register_login_totp_flow(client, session):
    uname = f"api_{uuid.uuid4().hex[:8]}"

    # 1) Register (password factor).
    r = client.post("/api/register", json={
        "username": uname, "email": f"{uname}@x.com", "password": "Password123!",
    })
    assert r.status_code == 201
    user_id = r.get_json()["user"]["id"]

    # 2) Password login - no MFA enrolled yet.
    r = client.post("/api/login", json={"username": uname, "password": "Password123!"})
    assert r.status_code == 200
    body = r.get_json()
    assert body["ok"] is True
    assert body["mfa_required"] is False

    # 3) Start TOTP enrollment.
    r = client.post("/api/mfa/totp/enroll/start", json={"user_id": user_id})
    assert r.status_code == 201
    enroll = r.get_json()
    assert enroll["otpauth_uri"].startswith("otpauth://totp/")
    assert enroll["qr_data_uri"].startswith("data:image/png;base64,")

    # 4) Confirm enrollment with a freshly generated code.
    code = totp.generate(enroll["secret"], digits=6, step=30, algorithm="SHA1")
    r = client.post("/api/mfa/totp/enroll/verify", json={
        "user_id": user_id, "credential_id": enroll["credential_id"], "code": code,
    })
    assert r.status_code == 200
    assert r.get_json()["enabled"] is True

    # 5) Login again - MFA now required and TOTP is listed.
    r = client.post("/api/login", json={"username": uname, "password": "Password123!"})
    body = r.get_json()
    assert body["mfa_required"] is True
    assert "totp" in body["factors"]


def test_wrong_password_is_unauthorized(client):
    uname = f"api_{uuid.uuid4().hex[:8]}"
    client.post("/api/register", json={
        "username": uname, "email": f"{uname}@x.com", "password": "Password123!",
    })
    r = client.post("/api/login", json={"username": uname, "password": "nope"})
    assert r.status_code == 401
