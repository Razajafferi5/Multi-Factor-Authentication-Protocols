"""BackupCode model: single-use recovery codes, hashed at rest.

Backup codes are an account-recovery factor. Like passwords, they are stored
only as Argon2id hashes (never plaintext) and each code may be consumed once.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..extensions import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class BackupCode(Base):
    """One recovery code. ``used_at`` is set when the code is redeemed."""

    __tablename__ = "backup_codes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    # Argon2id hash of the code. Plaintext is shown to the user exactly once.
    code_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="backup_codes")

    @property
    def is_used(self) -> bool:
        return self.used_at is not None

    def __repr__(self) -> str:  # pragma: no cover
        return f"<BackupCode id={self.id} user_id={self.user_id} used={self.is_used}>"
