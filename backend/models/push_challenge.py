"""PushChallenge model for the (simulated) push-approval factor.

A login that uses the push factor creates a pending challenge. A mock device
endpoint approves or denies it, and the login flow polls for the result. This
mirrors how Duo/Okta push works, but the "device" is simulated server-side -
clearly documented as such in SECURITY_NOTES.md.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..extensions import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PushStatus:
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    EXPIRED = "expired"


class PushChallenge(Base):
    """A pending push-approval request with a time-to-live."""

    __tablename__ = "push_challenges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    challenge_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    status: Mapped[str] = mapped_column(String(20), default=PushStatus.PENDING, nullable=False)

    # Contextual info shown on the (mock) device.
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship("User")

    def is_expired(self, now: datetime | None = None) -> bool:
        now = now or _utcnow()
        # Normalise naive timestamps coming back from SQLite to UTC-aware.
        expires = self.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        return now >= expires

    @staticmethod
    def default_expiry(ttl_seconds: int = 120) -> datetime:
        return _utcnow() + timedelta(seconds=ttl_seconds)

    def to_dict(self) -> dict:
        return {
            "challenge_id": self.challenge_id,
            "user_id": self.user_id,
            "status": self.status,
            "ip_address": self.ip_address,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }

    def __repr__(self) -> str:  # pragma: no cover
        return f"<PushChallenge {self.challenge_id} status={self.status}>"
