"""
Аутентификация API.
Для MVP используем простую генерацию токена без базы пользователей.
"""

import uuid

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.core.security import create_access_token, create_refresh_token, verify_token

router = APIRouter()


class TokenRequest(BaseModel):
    """Запрос на получение токена."""

    # Для MVP: простой идентификатор клиента
    # В продакшене: email + password или OAuth
    client_id: str | None = None


class TokenResponse(BaseModel):
    """Ответ с токенами."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class RefreshRequest(BaseModel):
    """Запрос на обновление токена."""

    refresh_token: str


@router.post("/token", response_model=TokenResponse)
async def get_token(request: TokenRequest) -> TokenResponse:
    """
    Получить JWT токен для доступа к API.

    Для MVP: генерирует токен для любого client_id.
    В продакшене: требует валидацию credentials.
    """
    # Генерируем user_id
    user_id = request.client_id or str(uuid.uuid4())

    access_token = create_access_token(subject=user_id)
    refresh_token = create_refresh_token(subject=user_id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=3600,  # 1 hour
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshRequest) -> TokenResponse:
    """
    Обновить access token используя refresh token.
    """
    payload = verify_token(request.refresh_token, token_type="refresh")

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    access_token = create_access_token(subject=payload.sub)
    refresh_token = create_refresh_token(subject=payload.sub)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=3600,
    )
