"""
Health check эндпоинты.
"""

from fastapi import APIRouter

from app.core.config import settings
from app.core.redis import redis_client

router = APIRouter()


@router.get("/health")
async def healthcheck() -> dict:
    """Проверка здоровья сервиса."""
    redis_ok = await redis_client.ping()

    return {
        "status": "ok" if redis_ok else "degraded",
        "version": settings.app_version,
        "services": {
            "redis": "ok" if redis_ok else "unavailable",
        },
    }
