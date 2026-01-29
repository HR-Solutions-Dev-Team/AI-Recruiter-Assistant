"""
JWT авторизация и безопасность.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from app.core.config import settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenPayload(BaseModel):
    """Payload JWT токена."""

    sub: str
    exp: datetime
    type: str = "access"


class TokenData(BaseModel):
    """Данные из токена."""

    user_id: str | None = None


def create_access_token(
    subject: str | Any,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Создаёт JWT access token.

    Args:
        subject: Идентификатор пользователя (user_id)
        expires_delta: Время жизни токена

    Returns:
        Закодированный JWT токен
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )

    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "type": "access",
    }

    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(
    subject: str | Any,
    expires_delta: timedelta | None = None,
) -> str:
    """Создаёт JWT refresh token."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)

    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "type": "refresh",
    }

    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def verify_token(token: str, token_type: str = "access") -> TokenPayload | None:
    """
    Проверяет JWT токен.

    Args:
        token: JWT токен
        token_type: Тип токена (access/refresh)

    Returns:
        TokenPayload если токен валиден, None иначе
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        if payload.get("type") != token_type:
            return None

        return TokenPayload(
            sub=payload["sub"],
            exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
            type=payload.get("type", "access"),
        )
    except JWTError:
        return None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяет пароль."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Хеширует пароль."""
    return pwd_context.hash(password)
