from datetime import datetime, timedelta
import hashlib
import secrets
from app.core.datetime import utcnow

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Default lifetime for refresh tokens: 30 days
REFRESH_TOKEN_DAYS = 30
# Length of the random refresh token (before hashing)
REFRESH_TOKEN_BYTES = 32


def hash_password(password: str) -> str:
    return password_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_context.verify(plain_password, hashed_password)


def create_access_token(
    subject: str,
    facility_id: str | None = None,
    role: str | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    expire = utcnow() + (expires_delta or timedelta(minutes=settings.token_expire_minutes))
    payload = {"sub": subject, "exp": expire}
    if facility_id is not None:
        payload["facility_id"] = facility_id
    if role is not None:
        payload["role"] = role
    return jwt.encode(payload, settings.auth_secret, algorithm=settings.auth_algorithm)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.auth_secret, algorithms=[settings.auth_algorithm])


# ---------------------------------------------------------------------------
# Refresh token helpers
# ---------------------------------------------------------------------------

def generate_refresh_token() -> str:
    """Generate a new random refresh token (URL-safe, 43 chars)."""
    return secrets.token_urlsafe(REFRESH_TOKEN_BYTES)


def hash_refresh_token(token: str) -> str:
    """Hash a refresh token with SHA-256 for storage (constant-time comparison)."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_refresh_token_expiry() -> datetime:
    return utcnow() + timedelta(days=REFRESH_TOKEN_DAYS)
