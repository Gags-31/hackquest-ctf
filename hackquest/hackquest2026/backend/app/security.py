"""Passwords, sessions and team access codes."""
import hashlib
import hmac
import secrets
import string
from datetime import datetime, timedelta, timezone

from itsdangerous import BadSignature, URLSafeTimedSerializer

from .config import SECRET_KEY, SESSION_HOURS

try:
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError

    _ph = PasswordHasher()
    _HAS_ARGON2 = True
except ImportError:  # pragma: no cover - fallback only
    _HAS_ARGON2 = False


def hash_password(password: str) -> str:
    if _HAS_ARGON2:
        return _ph.hash(password)
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 210_000)
    return f"pbkdf2_sha256${salt}${digest.hex()}"


def verify_password(stored: str, password: str) -> bool:
    try:
        if stored.startswith("pbkdf2_sha256$"):
            _, salt, digest = stored.split("$")
            candidate = hashlib.pbkdf2_hmac(
                "sha256", password.encode(), bytes.fromhex(salt), 210_000
            ).hex()
            return hmac.compare_digest(candidate, digest)
        if _HAS_ARGON2:
            _ph.verify(stored, password)
            return True
    except (VerifyMismatchError, ValueError, TypeError):
        return False
    return False


def constant_time_eq(a: str, b: str) -> bool:
    return hmac.compare_digest(str(a).encode("utf-8"), str(b).encode("utf-8"))


_serializer = URLSafeTimedSerializer(SECRET_KEY, salt="hqctf2026-session")


def make_session(actor_type: str, actor_id: int) -> str:
    return _serializer.dumps({"t": actor_type, "i": actor_id})


def read_session(token: str) -> dict | None:
    try:
        return _serializer.loads(token, max_age=SESSION_HOURS * 3600)
    except (BadSignature, ValueError):
        return None


CSRF_ALPHABET = string.ascii_letters + string.digits
CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # unambiguous


def new_csrf_token() -> str:
    return "".join(secrets.choice(CSRF_ALPHABET) for _ in range(32))


def new_team_code() -> str:
    return "HQ-" + "".join(secrets.choice(CODE_ALPHABET) for _ in range(6))


def new_temp_password() -> str:
    return "HQ!" + "".join(secrets.choice(CSRF_ALPHABET) for _ in range(18))


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def as_utc(value: datetime | None) -> datetime | None:
    """SQLite drops timezone info; treat stored naive timestamps as UTC."""
    if value is not None and value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value

