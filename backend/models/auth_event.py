"""AuthEvent model: the audit log and the data source for the AI layer.

Every authentication attempt - password, any MFA factor, enrollment, push -
writes one row here. The anomaly engine extracts features from a user's
historical events, and the admin dashboard renders this table directly.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..extensions import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AuthEvent(Base):
    """A single authentication attempt and its outcome.

    ``geo`` and ``features`` are stored as JSON text for portability across
    SQLite. The anomaly fields (``anomaly_score`` / ``is_flagged`` /
    ``explanation``) are populated by the AI layer after scoring.
    """

    __tablename__ = "auth_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Nullable: a failed login for an unknown username has no user_id.
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    username_attempted: Mapped[str | None] = mapped_column(String(120), nullable=True)

    factor: Mapped[str] = mapped_column(String(20), nullable=False)  # password|totp|hotp|...
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    # Optional machine-readable reason (e.g. "bad_password", "replayed_code").
    reason: Mapped[str | None] = mapped_column(String(60), nullable=True)

    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    device_fingerprint: Mapped[str | None] = mapped_column(String(128), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)

    # JSON: {"lat": .., "lon": .., "city": ..., "country": ...}
    geo: Mapped[str | None] = mapped_column(Text, nullable=True)

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False, index=True
    )

    # --- AI anomaly layer outputs -------------------------------------------
    # JSON-encoded feature vector used for scoring.
    features: Mapped[str | None] = mapped_column(Text, nullable=True)
    # IsolationForest score (higher = more normal in our convention).
    anomaly_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_flagged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Natural-language explanation (Claude) or NULL when degraded to features.
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User | None"] = relationship("User")

    # --- JSON helpers --------------------------------------------------------
    def set_geo(self, geo: dict | None) -> None:
        self.geo = json.dumps(geo) if geo else None

    def get_geo(self) -> dict | None:
        return json.loads(self.geo) if self.geo else None

    def set_features(self, features: dict | None) -> None:
        self.features = json.dumps(features) if features else None

    def get_features(self) -> dict | None:
        return json.loads(self.features) if self.features else None

    def to_dict(self) -> dict:
        """Flatten for the dashboard table / API responses."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "username_attempted": self.username_attempted,
            "factor": self.factor,
            "success": self.success,
            "reason": self.reason,
            "ip_address": self.ip_address,
            "device_fingerprint": self.device_fingerprint,
            "user_agent": self.user_agent,
            "geo": self.get_geo(),
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "features": self.get_features(),
            "anomaly_score": self.anomaly_score,
            "is_flagged": self.is_flagged,
            "explanation": self.explanation,
        }

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<AuthEvent id={self.id} user_id={self.user_id} "
            f"factor={self.factor} success={self.success}>"
        )
