"""
Сервис для генерации обзора вакансии через OpenRouter + Perplexity.
Предоставляет контекст о роли, компании и отрасли для рекрутеров.
"""

import json
import logging
from typing import Any

import httpx
from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger(__name__)


class OverviewData(BaseModel):
    """Структура данных обзора вакансии."""
    
    role_description: str
    """Описание профессии/роли в контексте сферы и компании."""
    
    company_overview: str | None = None
    """Краткий обзор компании (если указана)."""
    
    industry_context: str
    """Контекст отрасли и её роль на рынке."""
    
    business_processes: list[str]
    """Типичные бизнес-процессы, решаемые данной должностью."""


class OverviewResponse(BaseModel):
    """Ответ сервиса генерации обзора."""
    
    data: OverviewData
    sources: list[str] | None = None
    """Источники информации (если доступны от Perplexity)."""


SYSTEM_PROMPT = """Ты — эксперт по HR, рекрутингу и бизнес-процессам. Твоя задача — предоставить ИНФОРМАТИВНЫЙ и ПРАКТИЧНЫЙ обзор для рекрутера, который поможет ему лучше понять вакансию.

Ты получишь данные о вакансии: название должности, компания (если указана), отрасль.

Используй свои знания и актуальную информацию из интернета для формирования обзора.

ВАЖНО:
- Пиши на русском языке
- Будь кратким, но информативным
- Фокусируйся на практической пользе для рекрутера
- Если компания указана — найди реальную информацию о ней
- Адаптируй описание роли под специфику компании и отрасли

Верни JSON строго по следующей схеме:

{
  "role_description": "string — описание роли (2-4 предложения). Что делает специалист, какие задачи решает, какую ценность приносит бизнесу. Адаптируй под конкретную компанию/отрасль если указаны.",
  
  "company_overview": "string | null — краткий обзор компании (2-3 предложения). Чем занимается, позиция на рынке, особенности культуры. NULL если компания не указана.",
  
  "industry_context": "string — контекст отрасли (2-3 предложения). Текущее состояние отрасли, ключевые тренды, как это влияет на данную роль.",
  
  "business_processes": ["string"] — список из 4-6 типичных бизнес-процессов, в которых участвует данная роль. Кратко, по 1 предложению каждый.
}

ПРИМЕР для "Senior Frontend Developer" в "Яндекс":

{
  "role_description": "Senior Frontend Developer отвечает за разработку и оптимизацию пользовательских интерфейсов высоконагруженных сервисов. В контексте Яндекса это работа над продуктами с миллионами пользователей, где критичны производительность и масштабируемость.",
  
  "company_overview": "Яндекс — крупнейшая технологическая компания России, развивающая поисковик, маркетплейс, такси, доставку и облачные сервисы. Известна сильной инженерной культурой и собственными технологическими решениями.",
  
  "industry_context": "Российский IT-рынок активно развивается в условиях импортозамещения. Растёт спрос на специалистов, способных работать с отечественными технологическими стеками и высокими нагрузками.",
  
  "business_processes": [
    "Проектирование и разработка компонентов UI для веб-приложений",
    "Code review и менторинг junior-разработчиков",
    "Оптимизация производительности frontend-части приложений",
    "Участие в планировании спринтов и оценке задач",
    "Взаимодействие с дизайнерами и backend-командой",
    "Внедрение и поддержка CI/CD процессов для frontend"
  ]
}

Отвечай ТОЛЬКО валидным JSON без markdown-обёртки."""


class OverviewService:
    """Сервис для генерации обзора вакансии через Perplexity."""

    def __init__(self) -> None:
        self.api_key = settings.openrouter_api_key
        self.model = settings.openrouter_model_perplexity
        self.base_url = settings.openrouter_base_url

    async def generate_overview(
        self,
        job_title: str,
        company_name: str | None = None,
        industry: str | None = None,
        activity_sphere: str | None = None,
    ) -> OverviewResponse:
        """
        Генерирует обзор вакансии через Perplexity.

        Args:
            job_title: Название должности
            company_name: Название компании (опционально)
            industry: Отрасль (опционально)
            activity_sphere: Сфера деятельности (опционально)

        Returns:
            OverviewResponse с данными обзора
        """
        user_prompt = self._build_user_prompt(
            job_title, company_name, industry, activity_sphere
        )

        try:
            raw_response, citations = await self._call_perplexity(user_prompt)
            parsed_data = self._parse_response(raw_response)
            
            return OverviewResponse(
                data=OverviewData(**parsed_data),
                sources=citations,
            )
        except Exception as e:
            logger.error(f"Failed to generate overview: {e}")
            raise

    def _build_user_prompt(
        self,
        job_title: str,
        company_name: str | None,
        industry: str | None,
        activity_sphere: str | None,
    ) -> str:
        """Строит промпт для Perplexity."""
        parts = [f"Должность: {job_title}"]
        
        if company_name:
            parts.append(f"Компания: {company_name}")
        
        if industry:
            parts.append(f"Отрасль: {industry}")
        
        if activity_sphere:
            parts.append(f"Сфера деятельности: {activity_sphere}")
        
        prompt = "Сформируй обзор для рекрутера по следующей вакансии:\n\n"
        prompt += "\n".join(parts)
        
        if company_name:
            prompt += f"\n\nНайди актуальную информацию о компании {company_name} в интернете."
        
        return prompt

    async def _call_perplexity(self, user_prompt: str) -> tuple[str, list[str] | None]:
        """
        Вызывает OpenRouter API с моделью Perplexity.
        
        Returns:
            Tuple of (response_content, citations)
        """
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not configured")

        async with httpx.AsyncClient(timeout=90.0) as client:
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
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.3,
                    "max_tokens": 2000,
                },
            )
            response.raise_for_status()
            data = response.json()
            logger.debug(f"Perplexity response: {data}")

            if not data.get("choices"):
                logger.error(f"No choices in response: {data}")
                raise ValueError(f"Invalid API response: {data}")

            content = data["choices"][0].get("message", {}).get("content")
            if not content:
                logger.error(f"No content in response: {data}")
                raise ValueError("Empty response from Perplexity")

            # Perplexity может возвращать citations в отдельном поле
            citations = None
            if "citations" in data:
                citations = data["citations"]

            return content, citations

    def _parse_response(self, raw: str) -> dict[str, Any]:
        """Парсит JSON из ответа Perplexity."""
        if not raw:
            raise ValueError("Empty Perplexity response")

        content = raw.strip()

        # Убираем markdown обёртку если есть
        if content.startswith("```"):
            lines = content.split("\n")
            if lines[-1].strip() == "```":
                content = "\n".join(lines[1:-1])
            else:
                content = "\n".join(lines[1:])

        try:
            result = json.loads(content)
            if result is None:
                raise ValueError("Parsed result is None")
            return result
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}\nContent: {content[:500]}")
            raise ValueError(f"Invalid JSON from Perplexity: {e}")


overview_service = OverviewService()
