"""Flask application factory.

Run locally with::

    flask --app backend.app run        # or: python -m backend.app

The factory wires configuration, initialises the database schema, registers all
blueprints and enables CORS so the Streamlit dashboard (a different origin) can
call the API in HTTP mode.
"""

from __future__ import annotations

from flask import Flask, jsonify
from flask_cors import CORS

from .config import config
from .extensions import init_db
from .routes import ALL_BLUEPRINTS


def create_app() -> Flask:
    """Construct and configure the Flask application."""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = config.secret_key

    # Allow the dashboard origin(s) to call the API.
    CORS(app)

    # Create tables on startup (idempotent).
    init_db()

    for bp in ALL_BLUEPRINTS:
        app.register_blueprint(bp)

    @app.get("/")
    def index():
        return jsonify({
            "service": "MFA Authentication Server",
            "status": "running",
            "endpoints": [
                "/api/register", "/api/login",
                "/api/mfa/totp/...", "/api/mfa/hotp/...",
                "/api/mfa/push/...", "/api/mfa/webauthn/...",
                "/api/mfa/backup/...", "/api/admin/...",
            ],
        })

    return app


# Module-level app so `flask --app backend.app` and gunicorn both work.
app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
