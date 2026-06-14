from datetime import datetime, timedelta
from app.core.datetime import utcnow

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return password_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_context.verify(plain_password, hashed_password)


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    expire = utcnow() + (expires_delta or timedelta(minutes=settings.token_expire_minutes))
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.auth_secret, algorithm=settings.auth_algorithm)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.auth_secret, algorithms=[settings.auth_algorithm])
