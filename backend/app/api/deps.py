"""
Зависимости (dependencies) для API эндпоинтов.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.redis import RedisClient, get_redis
from app.core.security import verify_token

security = HTTPBearer()


async def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> str:
    """
    Извлекает user_id из JWT токена.
    Используется как dependency для защищённых эндпоинтов.

    Raises:
        HTTPException 401: Если токен невалиден или отсутствует
    """
    token = credentials.credentials
    payload = verify_token(token, token_type="access")

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload.sub


# Type aliases для удобства
CurrentUserId = Annotated[str, Depends(get_current_user_id)]
Redis = Annotated[RedisClient, Depends(get_redis)]
