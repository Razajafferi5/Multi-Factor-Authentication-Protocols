"""User account model.

A user holds the password factor (the first level of multi-level
authentication) plus lockout bookkeeping. Additional factors are stored in the
``Credential`` table linked back to the user.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..extensions import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    """An authenticatable account.

    The ``password_hash`` is an Argon2id hash (never reversible). Lockout
    fields support the sliding-window brute-force protection implemented in the
    lockout service.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)

    # Argon2id hash string (includes algorithm + parameters + salt).
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Lockout state. ``locked_until`` is a UTC timestamp; NULL means not locked.
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)

    credentials: Mapped[list["Credential"]] = relationship(
        "Credential", back_populates="user", cascade="all, delete-orphan"
    )
    backup_codes: Mapped[list["BackupCode"]] = relationship(
        "BackupCode", back_populates="user", cascade="all, delete-orphan"
    )

    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Serialise for API/dashboard use. Never includes the password hash."""
        data = {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "is_active": self.is_active,
            "is_admin": self.is_admin,
            "locked_until": self.locked_until.isoformat() if self.locked_until else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "enrolled_factors": sorted({c.type for c in self.credentials if c.enabled}),
        }
        return data

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<User id={self.id} username={self.username!r}>"
