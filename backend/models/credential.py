"""Credential model: one row per enrolled second factor.

Each credential row stores the material for a single MFA factor belonging to a
user. Shared OTP secrets are stored ONLY as AES-256-GCM ciphertext in
``secret_ciphertext`` - never in plaintext (a non-negotiable requirement).
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, LargeBinary, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..extensions import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class CredentialType:
    """String constants for the supported factor types."""

    TOTP = "totp"
    HOTP = "hotp"
    WEBAUTHN = "webauthn"
    PUSH = "push"

    ALL = (TOTP, HOTP, WEBAUTHN, PUSH)


class Credential(Base):
    """A single enrolled authentication factor for a user.

    Fields are interpreted per ``type``:

    * ``totp`` / ``hotp`` - ``secret_ciphertext`` holds the encrypted shared
      secret. ``hotp_counter`` tracks the moving counter (RFC 4226).
    * ``webauthn`` - ``public_key`` / ``credential_id`` / ``sign_count`` hold
      the FIDO2 credential. ``secret_ciphertext`` is unused.
    * ``push`` - no secret material; presence of an enabled row means the user
      may receive push challenges.
    """

    __tablename__ = "credentials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False)

    # Human-friendly label shown in the dashboard ("Google Authenticator", etc.)
    label: Mapped[str | None] = mapped_column(String(120), nullable=True)

    # AES-256-GCM ciphertext of the OTP shared secret (nonce prepended).
    secret_ciphertext: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)

    # OTP configuration.
    algorithm: Mapped[str] = mapped_column(String(10), default="SHA1", nullable=False)
    digits: Mapped[int] = mapped_column(Integer, default=6, nullable=False)
    period: Mapped[int] = mapped_column(Integer, default=30, nullable=False)  # TOTP step
    hotp_counter: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # HOTP counter
    # Last TOTP time-step consumed, for replay prevention within the window.
    last_timestep: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # WebAuthn fields.
    credential_id: Mapped[str | None] = mapped_column(String(512), nullable=True, index=True)
    public_key: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    sign_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    transports: Mapped[str | None] = mapped_column(Text, nullable=True)

    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="credentials")

    def to_dict(self) -> dict:
        """Serialise non-secret metadata for the dashboard."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "type": self.type,
            "label": self.label,
            "algorithm": self.algorithm,
            "digits": self.digits,
            "period": self.period,
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
        }

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Credential id={self.id} user_id={self.user_id} type={self.type}>"
