"""SQLAlchemy ORM models for the MFA server.

Importing this package registers every model on ``Base.metadata`` so that
``init_db()`` can create the full schema.
"""

from .user import User
from .credential import Credential, CredentialType
from .auth_event import AuthEvent
from .backup_code import BackupCode
from .push_challenge import PushChallenge, PushStatus

__all__ = [
    "User",
    "Credential",
    "CredentialType",
    "AuthEvent",
    "BackupCode",
    "PushChallenge",
    "PushStatus",
]
