"""Password hashing (Argon2id), session signing and CSRF helpers."""
import hmac
import secrets
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, VerifyMismatchError

from .config import settings

_hasher = PasswordHasher(
    time_cost=settings.ARGON2_TIME_COST,
    memory_cost=settings.ARGON2_MEMORY_COST,
    parallelism=settings.ARGON2_PARALLELISM,
)


def hash_password(raw: str) -> str:
    return _hasher.hash(raw)


def verify_password(stored_hash: str, raw: str) -> bool:
    if not stored_hash:
        return False
    try:
        _hasher.verify(stored_hash, raw)
        return True
    except (VerifyMismatchError, VerificationError, Exception):
        return False


def needs_rehash(stored_hash: str) -> bool:
    try:
        return _hasher.check_needs_rehash(stored_hash)
    except Exception:
        return False


# ---------------------------------------------------------------- sessions
def _signer():
    from itsdangerous import URLSafeSerializer
    return URLSafeSerializer(settings.SECRET_KEY, salt="hq-session")


def make_session_token(identity: str, role: str) -> str:
    return _signer().dumps({"id": identity, "role": role, "n": secrets.token_hex(8)})


def read_session_token(token: str):
    try:
        return _signer().loads(token)
    except Exception:
        return None


def new_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def csrf_ok(sent: str | None, expected: str | None) -> bool:
    if not sent or not expected:
        return False
    return hmac.compare_digest(sent, expected)


# ---------------------------------------------------------------- misc
def constant_time_eq(a: str, b: str) -> bool:
    return hmac.compare_digest(str(a).encode(), str(b).encode())


def new_team_code(length: int = 6) -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(secrets.choice(alphabet) for _ in range(length))