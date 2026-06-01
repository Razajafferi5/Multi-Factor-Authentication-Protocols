"""Security test: repeated password failures trigger lockout (brute force)."""

import uuid

from backend.config import config
from backend.services import auth
from backend.services.users import create_user
from backend.services.lockout import is_locked


def test_brute_force_triggers_lockout(session):
    uname = f"lock_{uuid.uuid4().hex[:8]}"
    user = create_user(session, username=uname, email=f"{uname}@x.com", password="CorrectHorse1!")

    # Hammer with wrong passwords up to the configured threshold.
    failures = 0
    for _ in range(config.lockout_max_failures + 2):
        try:
            auth.login_password(session, username=uname, password="wrong-password")
        except auth.AuthError:
            failures += 1

    session.refresh(user)
    assert failures >= config.lockout_max_failures
    assert is_locked(session, user), "account should be locked after threshold failures"

    # Even the correct password is refused while locked.
    try:
        auth.login_password(session, username=uname, password="CorrectHorse1!")
        locked_block = False
    except auth.AuthError as exc:
        locked_block = "locked" in str(exc)
    assert locked_block, "correct password must be refused during active lockout"
