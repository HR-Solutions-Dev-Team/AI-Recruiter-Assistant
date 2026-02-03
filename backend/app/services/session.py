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
        Вычисляет процент заполненности вакансии динамически.
        
        Каждое заполненное поле даёт свою долю процента.
        Учитывает Executive Search поля (hiringContext, successCriteria и т.д.)
        """
        if not self.parsed_data:
            return 0
        
        # Определяем все поля и их веса
        # Общий вес = 100%, распределён по важности для Executive Search
        field_weights = {
            # Core (15% total)
            "core.jobTitle": 10,
            "core.careerLevel": 3,
            "core.industry": 2,
            
            # Business Context (20% total) - критично для exec search
            "hiringContext.businessProblem": 8,
            "hiringContext.triggerEvent": 6,
            "hiringContext.expectedImpact": 6,
            
            # Success Criteria (15% total)
            "successCriteria.onboardingMilestones": 8,
            "successCriteria.shortTermKPIs": 7,
            
            # Ideal Candidate (15% total)
            "differentiators.industryExpertise": 5,
            "differentiators.scaleExperience": 4,
            "differentiators.achievementMarkers": 4,
            "differentiators.companyBackground": 2,
            
            # Requirements (15% total)
            "dealbreakers.absoluteRequirements": 5,
            "dealbreakers.experienceMinimums": 4,
            "dealbreakers.nonNegotiables": 3,
            "requirements.skills": 3,
            
            # Responsibilities (10% total)
            "responsibilities.criticalTasks": 5,
            "responsibilities.zones": 5,
            
            # Work Conditions (5% total)
            "workConditions.salary": 2,
            "workConditions.location": 3,
            
            # Company/Org (5% total)
            "company.name": 2,
            "orgStructure.reportsTo": 3,
        }
        
        total_score = 0
        
        for field_path, weight in field_weights.items():
            if self._is_field_filled(field_path):
                total_score += weight
        
        return min(int(total_score), 100)
    
    def _is_field_filled(self, field_path: str) -> bool:
        """Проверяет, заполнено ли поле."""
        if not self.parsed_data:
            return False
        
        parts = field_path.split(".")
        value = self.parsed_data
        
        for part in parts:
            if not isinstance(value, dict):
                return False
            value = value.get(part)
            if value is None:
                return False
        
        # Проверяем, что значение не пустое
        if isinstance(value, str):
            return bool(value.strip())
        elif isinstance(value, list):
            return len(value) > 0
        elif isinstance(value, dict):
            # Для вложенных объектов проверяем наличие любых данных
            return bool(value)
        else:
            return value is not None


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
