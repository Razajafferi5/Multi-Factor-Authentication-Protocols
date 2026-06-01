"""Flask blueprints exposing the REST API.

Blueprints:

* ``auth_bp``     - registration + password (first-factor) login.
* ``mfa_bp``      - TOTP/HOTP enrollment + verification, backup codes.
* ``push_bp``     - push-approval challenge / mock device / poll.
* ``webauthn_bp`` - FIDO2 registration + assertion.
* ``admin_bp``    - user management + event/anomaly queries for the dashboard.
"""

from .auth_routes import auth_bp
from .mfa_routes import mfa_bp
from .push_routes import push_bp
from .webauthn_routes import webauthn_bp
from .admin_routes import admin_bp

ALL_BLUEPRINTS = [auth_bp, mfa_bp, push_bp, webauthn_bp, admin_bp]

__all__ = ["ALL_BLUEPRINTS"]
