"""Password and backup-code hashing using Argon2id.

Argon2id (winner of the 2015 Password Hashing Competition) is a memory-hard
function resistant to GPU/ASIC cracking. We use it for both user passwords and
single-use backup codes. Hashes are one-way: plaintext is never recoverable.

If ``argon2-cffi`` were unavailable we would fall back to bcrypt, but Argon2id
is the preferred algorithm per the brief and is a hard dependency here.
"""

from __future__ import annotations

from argon2 import PasswordHasher
from argon2 import exceptions as argon2_exceptions

# Parameters chosen for an interactive login on commodity hardware. Documented
# in SECURITY_NOTES.md. (time_cost=3, memory_cost=64 MiB, parallelism=4 are
# sane 2024-era defaults; argon2-cffi's defaults are similar.)
_hasher = PasswordHasher(
    time_cost=3,
    memory_cost=64 * 1024,  # 64 MiB
    parallelism=4,
    hash_len=32,
    salt_len=16,
)


def hash_password(password: str) -> str:
    """Return an Argon2id encoded hash string for ``password``."""
    if not password:
        raise ValueError("password must not be empty")
    return _hasher.hash(password)


def verify_password(stored_hash: str, password: str) -> bool:
    """Return True iff ``password`` matches ``stored_hash``.

    Uses Argon2's constant-time verifier and swallows the library's
    verification exceptions, returning a plain boolean to callers.
    """
    try:
        return _hasher.verify(stored_hash, password)
    except (
        argon2_exceptions.VerifyMismatchError,
        argon2_exceptions.InvalidHashError,
        argon2_exceptions.VerificationError,
    ):
        return False


def needs_rehash(stored_hash: str) -> bool:
    """True if the hash was produced with weaker parameters than current."""
    try:
        return _hasher.check_needs_rehash(stored_hash)
    except argon2_exceptions.InvalidHashError:
        return True


# Backup codes use the same primitive; aliased for call-site clarity.
hash_backup_code = hash_password
verify_backup_code = verify_password
