"""
Сервис для работы с сессиями вакансий.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel

from app.core.redis import redis_client


class SessionStatus(str, Enum):
    """Статус сессии создания вакансии."""

    CREATED = "created"
    TEXT_UPLOADED = "text_uploaded"
    PARSED = "parsed"
    CLARIFYING = "clarifying"
    COMPLETED = "completed"


class VacancySession(BaseModel):
    """Модель сессии создания вакансии."""

    session_id: str
    user_id: str
    status: SessionStatus = SessionStatus.CREATED
    original_text: str | None = None
    parsed_data: dict[str, Any] | None = None
    confidence: float | None = None
    warnings: list[str] | None = None
    missing_fields: list[str] | None = None
    created_at: str
    updated_at: str

    def get_completion_percent(self) -> int:
        """
        Вычисляет процент заполненности вакансии.

        Учитывает:
        - core (обязательно): 30%
        - requirements.skills: 25%
        - workConditions: 15%
        - responsibilities: 15%
        - company: 10%
        - orgStructure: 5%
        """
        if not self.parsed_data:
            return 0

        scores = {
            "core": (30, self._check_core),
            "skills": (25, self._check_skills),
            "work_conditions": (15, self._check_work_conditions),
            "responsibilities": (15, self._check_responsibilities),
            "company": (10, self._check_company),
            "org_structure": (5, self._check_org_structure),
        }

        total = 0
        for _name, (weight, checker) in scores.items():
            score = checker()
            total += weight * score

        return int(total)

    def _check_core(self) -> float:
        """Проверяет заполненность core блока."""
        if not self.parsed_data:
            return 0

        core = self.parsed_data.get("core") or {}
        if not core.get("jobTitle"):
            return 0

        filled = 1  # jobTitle есть
        if core.get("careerLevel"):
            filled += 1
        if core.get("industry"):
            filled += 1
        if core.get("synonyms"):
            filled += 0.5

        return min(filled / 3, 1.0)

    def _check_skills(self) -> float:
        """Проверяет заполненность навыков."""
        if not self.parsed_data:
            return 0

        requirements = self.parsed_data.get("requirements") or {}
        skills = requirements.get("skills") or []

        if not skills:
            return 0

        # Минимум 5 навыков для 100%
        return min(len(skills) / 5, 1.0)

    def _check_work_conditions(self) -> float:
        """Проверяет заполненность условий работы."""
        if not self.parsed_data:
            return 0

        wc = self.parsed_data.get("workConditions") or {}
        if not wc:
            return 0

        filled = 0
        if wc.get("salary"):
            filled += 1
        if wc.get("location"):
            filled += 1
        if wc.get("employmentType"):
            filled += 0.5
        if wc.get("schedule"):
            filled += 0.5

        return min(filled / 3, 1.0)

    def _check_responsibilities(self) -> float:
        """Проверяет заполненность обязанностей."""
        if not self.parsed_data:
            return 0

        resp = self.parsed_data.get("responsibilities") or {}
        if not resp:
            return 0

        zones = resp.get("zones") or []
        if not zones:
            return 0

        # Минимум 3 зоны для 100%
        return min(len(zones) / 3, 1.0)

    def _check_company(self) -> float:
        """Проверяет заполненность информации о компании."""
        if not self.parsed_data:
            return 0

        company = self.parsed_data.get("company") or {}
        if not company.get("name"):
            return 0

        filled = 1  # name есть
        if company.get("type"):
            filled += 0.5
        if company.get("size"):
            filled += 0.5
        if company.get("benefits"):
            filled += 1

        return min(filled / 3, 1.0)

    def _check_org_structure(self) -> float:
        """Проверяет заполненность оргструктуры."""
        if not self.parsed_data:
            return 0

        org = self.parsed_data.get("orgStructure") or {}
        if not org:
            return 0

        filled = 0
        if org.get("reportsTo"):
            filled += 1
        if org.get("teamRoles"):
            filled += 1

        return min(filled / 2, 1.0)


class SessionService:
    """Сервис для управления сессиями."""

    async def create_session(self, user_id: str) -> VacancySession:
        """Создаёт новую сессию."""
        now = datetime.now(timezone.utc).isoformat()
        session = VacancySession(
            session_id=str(uuid.uuid4()),
            user_id=user_id,
            status=SessionStatus.CREATED,
            created_at=now,
            updated_at=now,
        )

        await redis_client.set_session(session.session_id, session.model_dump())
        return session

    async def get_session(self, session_id: str, user_id: str) -> VacancySession | None:
        """Получает сессию по ID (с проверкой владельца)."""
        data = await redis_client.get_session(session_id)
        if data is None:
            return None

        session = VacancySession(**data)
        if session.user_id != user_id:
            return None

        return session

    async def update_session(
        self,
        session_id: str,
        user_id: str,
        **updates: Any,
    ) -> VacancySession | None:
        """Обновляет сессию."""
        session = await self.get_session(session_id, user_id)
        if session is None:
            return None

        updates["updated_at"] = datetime.now(timezone.utc).isoformat()

        session_dict = session.model_dump()
        session_dict.update(updates)

        await redis_client.set_session(session_id, session_dict)
        return VacancySession(**session_dict)

    async def delete_session(self, session_id: str, user_id: str) -> bool:
        """Удаляет сессию."""
        session = await self.get_session(session_id, user_id)
        if session is None:
            return False

        return await redis_client.delete_session(session_id)


session_service = SessionService()
