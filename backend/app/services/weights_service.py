"""
Сервис для расчёта весов критериев отбора кандидатов через LLM.
Анализирует вакансию и определяет приоритеты категорий.
"""

import json
import logging
from typing import Any

import httpx
from pydantic import BaseModel, Field

from app.core.config import settings

logger = logging.getLogger(__name__)


class CategoryWeight(BaseModel):
    """Вес одной категории (баллы 0-10)."""
    
    key: str
    weight: int = Field(ge=0, le=10)


class WeightsResult(BaseModel):
    """Результат расчёта весов (баллы 0-10 для каждой категории)."""
    
    weights: dict[str, int]  # баллы 0-10


# Категории для расчёта весов
WEIGHT_CATEGORIES = [
    {
        "key": "core",
        "title": "Позиция",
        "description": "Название должности, уровень, грейд, отрасль",
    },
    {
        "key": "company",
        "title": "Компания",
        "description": "Тип компании, размер, сфера деятельности",
    },
    {
        "key": "workConditions",
        "title": "Условия работы",
        "description": "Формат работы, график, зарплата, локация",
    },
    {
        "key": "requirements",
        "title": "Требования",
        "description": "Образование, опыт работы, навыки, языки",
    },
    {
        "key": "responsibilities",
        "title": "Обязанности",
        "description": "Зоны ответственности, задачи, процессы",
    },
    {
        "key": "hiringContext",
        "title": "Контекст найма",
        "description": "Причина открытия вакансии, бизнес-проблема, ожидаемый результат",
    },
    {
        "key": "successCriteria",
        "title": "Критерии успеха",
        "description": "KPI, milestones, ожидания от кандидата",
    },
    {
        "key": "differentiators",
        "title": "Идеальный кандидат",
        "description": "Отраслевая экспертиза, масштаб опыта, достижения, бэкграунд",
    },
    {
        "key": "dealbreakers",
        "title": "Критические требования",
        "description": "Абсолютные требования, минимальный опыт, red flags",
    },
]


WEIGHTS_CALCULATION_PROMPT = """Ты — эксперт по Executive Search и оценке кандидатов.

Проанализируй вакансию и определи ПРИОРИТЕТЫ (важность) категорий критериев отбора.
Твоя задача — понять, какие категории НАИБОЛЕЕ ВАЖНЫ для успешного найма на ЭТУ КОНКРЕТНУЮ позицию.

=== ДАННЫЕ ВАКАНСИИ ===
{vacancy_data}

=== КАТЕГОРИИ ДЛЯ ОЦЕНКИ ===
{categories_description}

=== ПРАВИЛА ОЦЕНКИ ===

Оцени каждую категорию по шкале от 0 до 10:
- 0 = категория НЕ важна для этой вакансии
- 1-3 = низкая важность
- 4-6 = средняя важность  
- 7-8 = высокая важность
- 9-10 = критически важно для успеха найма

=== ЛОГИКА ПРИОРИТИЗАЦИИ ===

Для РУКОВОДЯЩИХ позиций (lead, head, director, c-level):
- hiringContext, successCriteria, differentiators, dealbreakers — выше важность (7-10)
- requirements (навыки) — ниже важность (3-5, следуют из опыта)

Для ТЕХНИЧЕСКИХ позиций (developer, engineer, analyst):
- requirements (навыки, стек) — высокая важность (7-9)
- workConditions (формат, локация) — ниже для удалёнки (3-5)

Для SALES/BUSINESS позиций:
- company, workConditions — выше важность (6-8)
- successCriteria (KPI) — критично важно (8-10)

Для РЕДКИХ специалистов:
- differentiators, dealbreakers — максимальная важность (8-10)
- company — ниже (4-6, такие специалисты выбирают сами)

=== УЧИТЫВАЙ ===

1. Заполненность секций — если секция пустая, она менее важна
2. Специфику роли — что критично для успеха именно этой позиции
3. Уровень позиции — senior/executive требуют больше контекста
4. Срочность — если urgent, больше важность dealbreakers

=== ФОРМАТ ОТВЕТА ===

Верни ТОЛЬКО валидный JSON (без markdown, без комментариев):
{{
  "core": <число 0-10>,
  "company": <число 0-10>,
  "workConditions": <число 0-10>,
  "requirements": <число 0-10>,
  "responsibilities": <число 0-10>,
  "hiringContext": <число 0-10>,
  "successCriteria": <число 0-10>,
  "differentiators": <число 0-10>,
  "dealbreakers": <число 0-10>
}}

Каждое значение — целое число от 0 до 10."""


class WeightsService:
    """Сервис для расчёта весов критериев через LLM."""

    def __init__(self) -> None:
        self.api_key = settings.openrouter_api_key
        self.model = settings.openrouter_model
        self.base_url = settings.openrouter_base_url

    async def calculate_weights(
        self,
        vacancy_data: dict[str, Any],
    ) -> WeightsResult:
        """
        Рассчитывает веса категорий критериев отбора на основе данных вакансии.

        Args:
            vacancy_data: Данные вакансии

        Returns:
            WeightsResult с весами для каждой категории
        """
        # Формируем описание категорий
        categories_desc = "\n".join(
            f"- {cat['key']}: {cat['title']} — {cat['description']}"
            for cat in WEIGHT_CATEGORIES
        )

        # Формируем промпт
        prompt = WEIGHTS_CALCULATION_PROMPT.format(
            vacancy_data=json.dumps(vacancy_data, ensure_ascii=False, indent=2),
            categories_description=categories_desc,
        )

        # Вызываем LLM
        response = await self._call_llm(prompt)

        if not response:
            # Fallback на дефолтные веса
            return self._get_default_weights(vacancy_data)

        try:
            weights = json.loads(response)
            
            # Валидация (баллы 0-10)
            validated_weights = self._validate_and_normalize(weights)
            
            return WeightsResult(weights=validated_weights)
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse weights response: {e}")
            return self._get_default_weights(vacancy_data)

    def _validate_and_normalize(self, weights: dict[str, Any]) -> dict[str, int]:
        """Валидирует веса (баллы 0-10)."""
        valid_keys = {cat["key"] for cat in WEIGHT_CATEGORIES}
        result: dict[str, int] = {}

        # Извлекаем валидные значения
        for key in valid_keys:
            value = weights.get(key, 5)  # default 5 баллов
            if isinstance(value, (int, float)):
                # Ограничиваем диапазон 0-10
                result[key] = max(0, min(10, int(value)))
            else:
                result[key] = 5

        return result

    def _get_default_weights(self, vacancy_data: dict[str, Any]) -> WeightsResult:
        """Возвращает дефолтные веса (баллы 0-10) на основе простой эвристики."""
        weights = {
            "core": 6,
            "company": 5,
            "workConditions": 5,
            "requirements": 6,
            "responsibilities": 5,
            "hiringContext": 5,
            "successCriteria": 5,
            "differentiators": 5,
            "dealbreakers": 5,
        }

        # Простые эвристики
        career_level = (
            vacancy_data.get("core", {}).get("careerLevel", {}).get("code", "")
        )
        job_title = vacancy_data.get("core", {}).get("jobTitle", "").lower()

        # Senior/Executive — больше важности на контекст и критерии
        if career_level in ["senior", "lead", "head", "director", "c-level"]:
            weights["hiringContext"] = 8
            weights["successCriteria"] = 7
            weights["differentiators"] = 8
            weights["dealbreakers"] = 7
            weights["requirements"] = 4
            weights["core"] = 6
            weights["company"] = 4
            weights["workConditions"] = 4
            weights["responsibilities"] = 6

        # IT роли — навыки важнее
        if any(
            kw in job_title
            for kw in ["developer", "engineer", "программист", "разработчик", "devops", "data", "analyst"]
        ):
            weights["requirements"] = 8
            weights["workConditions"] = 4
            weights["company"] = 4

        return WeightsResult(weights=weights)

    async def _call_llm(self, prompt: str) -> str | None:
        """Вызывает OpenRouter API."""
        if not self.api_key:
            logger.error("OPENROUTER_API_KEY not configured")
            return None

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://ai-recruiter-assistant.local",
                        "X-Title": "AI Recruiter Assistant",
                    },
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.2,  # Низкая температура для стабильности
                        "max_tokens": 500,
                    },
                )
                response.raise_for_status()
                data = response.json()

                if not data.get("choices"):
                    return None

                content = data["choices"][0].get("message", {}).get("content")
                return self._clean_json_response(content) if content else None

        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return None

    def _clean_json_response(self, content: str) -> str:
        """Очищает ответ LLM от markdown обёртки."""
        content = content.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            if lines[-1].strip() == "```":
                content = "\n".join(lines[1:-1])
            else:
                content = "\n".join(lines[1:])
        return content.strip()


weights_service = WeightsService()
