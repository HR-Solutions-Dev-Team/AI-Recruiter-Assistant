"""
Redis клиент для хранения сессий.
"""

import json
import logging
from typing import Any

import redis.asyncio as redis

from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """Асинхронный клиент Redis для работы с сессиями."""

    def __init__(self) -> None:
        self._client: redis.Redis | None = None

    async def connect(self) -> None:
        """Подключается к Redis."""
        if self._client is None:
            self._client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            logger.info("Connected to Redis")

    async def disconnect(self) -> None:
        """Отключается от Redis."""
        if self._client:
            await self._client.close()
            self._client = None
            logger.info("Disconnected from Redis")

    @property
    def client(self) -> redis.Redis:
        """Возвращает клиент Redis."""
        if self._client is None:
            raise RuntimeError("Redis client not connected. Call connect() first.")
        return self._client

    async def set_session(
        self,
        session_id: str,
        data: dict[str, Any],
        expire_seconds: int | None = None,
    ) -> None:
        """
        Сохраняет данные сессии.

        Args:
            session_id: ID сессии
            data: Данные для сохранения
            expire_seconds: TTL в секундах (по умолчанию из настроек)
        """
        key = f"session:{session_id}"
        value = json.dumps(data, ensure_ascii=False, default=str)
        ttl = expire_seconds or settings.session_expire_seconds

        await self.client.setex(key, ttl, value)
        logger.debug(f"Session {session_id} saved with TTL {ttl}s")

    async def get_session(self, session_id: str) -> dict[str, Any] | None:
        """
        Получает данные сессии.

        Args:
            session_id: ID сессии

        Returns:
            Данные сессии или None если не найдена
        """
        key = f"session:{session_id}"
        value = await self.client.get(key)

        if value is None:
            return None

        return json.loads(value)

    async def update_session(
        self,
        session_id: str,
        data: dict[str, Any],
        refresh_ttl: bool = True,
    ) -> bool:
        """
        Обновляет данные сессии (merge).

        Args:
            session_id: ID сессии
            data: Данные для добавления/обновления
            refresh_ttl: Обновлять TTL при обновлении

        Returns:
            True если сессия обновлена, False если не найдена
        """
        existing = await self.get_session(session_id)
        if existing is None:
            return False

        existing.update(data)
        await self.set_session(
            session_id,
            existing,
            settings.session_expire_seconds if refresh_ttl else None,
        )
        return True

    async def delete_session(self, session_id: str) -> bool:
        """
        Удаляет сессию.

        Args:
            session_id: ID сессии

        Returns:
            True если удалена, False если не существовала
        """
        key = f"session:{session_id}"
        result = await self.client.delete(key)
        return result > 0

    async def ping(self) -> bool:
        """Проверяет соединение с Redis."""
        try:
            await self.client.ping()
            return True
        except Exception:
            return False


redis_client = RedisClient()


async def get_redis() -> RedisClient:
    """Dependency для получения Redis клиента."""
    return redis_client
