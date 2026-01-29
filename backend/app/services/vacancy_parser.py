"""
Сервис для парсинга текста вакансии через OpenRouter API.
Извлекает структурированные данные из произвольного текста вакансии.
"""

import json
import logging
from typing import Any

import httpx

from app.core.config import settings
from app.models.vacancy import ParseVacancyResponse, VacancyInput

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """Ты — эксперт по HR и рекрутингу. Твоя задача — извлечь структурированные данные из текста вакансии.

ВАЖНО: Этот сервис предназначен для поиска РЕДКИХ и УЗКОСПЕЦИАЛИЗИРОВАННЫХ специалистов (5-10 кандидатов на вакансию), поэтому важна максимальная детализация.

Верни JSON строго по следующей схеме (все поля опциональны кроме core.jobTitle):

{
  "core": {
    "jobTitle": "string (ОБЯЗАТЕЛЬНО) — название должности",
    "synonyms": ["string"] — альтернативные названия роли,
    "careerLevel": {
      "code": "intern|junior|middle|senior|lead|head|director|c-level",
      "experienceYearsMin": number,
      "experienceYearsMax": number
    },
    "industry": {
      "name": "string — отрасль",
      "subIndustry": "string — подотрасль"
    }
  },
  "company": {
    "name": "string — название компании",
    "type": "startup|sme|enterprise|corporation|government|ngo|consulting",
    "size": "1-10|11-50|51-200|201-500|501-1000|1001-5000|5000+",
    "benefits": [{"name": "string"}],
    "publicLinks": [{"type": "site|hh|linkedin|habr|glassdoor|github|other", "url": "string"}]
  },
  "classification": {
    "businessFunction": {"name": "string — IT, Finance, HR, Marketing и т.д."},
    "roleFamily": {"name": "string — Engineering, Management, Analytics и т.д."},
    "orgLevel": {"code": "ic|team_lead|manager|senior_manager|director|vp|c_level"},
    "businessModel": {"name": "string", "segment": "B2B|B2C|B2B2C|B2G|C2C|D2C"},
    "projectType": "string — продукт, аутсорс, аутстафф, стартап, R&D"
  },
  "workConditions": {
    "employmentType": {"name": "full-time|part-time|contract|freelance|internship|temporary"},
    "schedule": {"name": "5/2|2/2|flexible|shift|remote-async|hybrid"},
    "workHours": "string — часы работы, например '10:00-19:00 MSK'",
    "salary": {
      "amountMin": number,
      "amountMax": number,
      "currency": "RUB|USD|EUR|GBP|KZT|BYN|UAH|GEL|AMD|AZN",
      "period": "month|year|hour|project",
      "comment": "string — gross/net, бонусы"
    },
    "location": {
      "city": "string",
      "region": "string",
      "country": "string",
      "remote": "office|remote|hybrid|relocate",
      "relocationSupport": boolean,
      "visaSupport": boolean
    }
  },
  "requirements": {
    "education": {
      "level": "any|secondary|bachelor|master|phd|mba",
      "fields": ["string — направления образования"],
      "comment": "string"
    },
    "experience": {
      "yearsMin": number,
      "yearsMax": number,
      "domains": ["string — домены опыта: FinTech, High-load и т.д."],
      "mustHave": ["string — обязательный опыт"],
      "niceToHave": ["string — желательный опыт"]
    },
    "skills": [
      {
        "name": "string — название навыка",
        "category": "hard|soft|management|digital_tool",
        "isRequired": boolean,
        "level": "basic|intermediate|advanced|expert",
        "comment": "string — пояснение"
      }
    ],
    "languages": [
      {
        "code": "string — ru, en, de",
        "name": "string — Русский, English",
        "proficiency": "A1|A2|B1|B2|C1|C2|native",
        "isRequired": boolean
      }
    ]
  },
  "responsibilities": {
    "scope": "string — общее описание зоны ответственности",
    "zones": ["string — конкретные зоны ответственности"],
    "businessProcesses": [
      {
        "name": "string — название процесса",
        "subprocesses": [{"name": "string"}]
      }
    ]
  },
  "orgStructure": {
    "reportsTo": "string — кому подчиняется",
    "subordinatesCount": number,
    "orgUnit": "string — название отдела",
    "teamRoles": ["string — роли в команде"],
    "crossFunctionalLinks": ["string — взаимодействие с другими отделами"]
  }
}

ПРАВИЛА:
1. Извлекай ТОЛЬКО то, что явно указано в тексте. Не додумывай.
2. Если информация отсутствует — не включай поле в ответ.
3. Для навыков определяй категорию:
   - hard: технические навыки (языки программирования, фреймворки, инструменты)
   - soft: мягкие навыки (коммуникация, критическое мышление)
   - management: управленческие навыки (менторство, планирование, найм)
   - digital_tool: цифровые инструменты (Jira, Figma, Notion)
4. Определяй isRequired=true для must-have требований, false для nice-to-have.
5. Отвечай ТОЛЬКО валидным JSON без markdown-обёртки."""


class VacancyParserService:
    """Сервис для парсинга текста вакансии через LLM."""

    def __init__(self) -> None:
        self.api_key = settings.openrouter_api_key
        self.model = settings.openrouter_model
        self.base_url = settings.openrouter_base_url

    async def parse(
        self,
        text: str,
        hints: dict[str, str] | None = None,
    ) -> ParseVacancyResponse:
        """
        Парсит текст вакансии и возвращает структурированные данные.

        Args:
            text: Исходный текст вакансии
            hints: Опциональные подсказки (company_name, industry)

        Returns:
            ParseVacancyResponse с распарсенными данными
        """
        user_prompt = self._build_user_prompt(text, hints)

        try:
            raw_response = await self._call_llm(user_prompt)
            parsed_data = self._parse_llm_response(raw_response)
            return self._build_response(parsed_data, text)
        except Exception as e:
            logger.error(f"Failed to parse vacancy: {e}")
            raise

    def _build_user_prompt(self, text: str, hints: dict[str, str] | None) -> str:
        """Строит промпт для LLM."""
        prompt = f"Извлеки структурированные данные из следующего текста вакансии:\n\n{text}"

        if hints:
            hint_parts = []
            if hints.get("company_name"):
                hint_parts.append(f"Компания: {hints['company_name']}")
            if hints.get("industry"):
                hint_parts.append(f"Отрасль: {hints['industry']}")
            if hint_parts:
                prompt += f"\n\nПодсказки:\n" + "\n".join(hint_parts)

        return prompt

    async def _call_llm(self, user_prompt: str) -> str:
        """Вызывает OpenRouter API."""
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not configured")

        async with httpx.AsyncClient(timeout=60.0) as client:
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
                    "temperature": 0.1,
                    "max_tokens": 4000,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    def _parse_llm_response(self, raw: str) -> dict[str, Any]:
        """Парсит JSON из ответа LLM."""
        content = raw.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

        return json.loads(content)

    def _build_response(
        self,
        parsed_data: dict[str, Any],
        original_text: str,
    ) -> ParseVacancyResponse:
        """Строит ответ с валидацией и метриками."""
        warnings: list[str] = []
        missing_fields: list[str] = []

        if "core" not in parsed_data or "jobTitle" not in parsed_data.get("core", {}):
            raise ValueError("Missing required field: core.jobTitle")

        recommended_fields = [
            ("core.careerLevel", parsed_data.get("core", {}).get("careerLevel")),
            ("requirements.skills", parsed_data.get("requirements", {}).get("skills")),
            ("workConditions.salary", parsed_data.get("workConditions", {}).get("salary")),
            ("workConditions.location", parsed_data.get("workConditions", {}).get("location")),
        ]

        for field_name, value in recommended_fields:
            if not value:
                missing_fields.append(field_name)

        skills = parsed_data.get("requirements", {}).get("skills", [])
        if skills and len(skills) < 3:
            warnings.append(
                f"Извлечено мало навыков ({len(skills)}). "
                "Рекомендуется добавить больше для точного поиска."
            )

        confidence = self._calculate_confidence(parsed_data)

        vacancy_input = VacancyInput.model_validate(parsed_data)
        vacancy_input.full_text = {"text": original_text, "source": "imported"}

        return ParseVacancyResponse(
            data=vacancy_input,
            confidence=confidence,
            warnings=warnings if warnings else None,
            missing_fields=missing_fields if missing_fields else None,
        )

    def _calculate_confidence(self, data: dict[str, Any]) -> float:
        """Вычисляет уверенность парсера на основе заполненности данных."""
        scores = {
            "core.jobTitle": 0.2,
            "core.careerLevel": 0.1,
            "core.industry": 0.05,
            "company.name": 0.05,
            "workConditions.salary": 0.1,
            "workConditions.location": 0.05,
            "requirements.skills": 0.2,
            "requirements.experience": 0.1,
            "requirements.languages": 0.05,
            "responsibilities.zones": 0.1,
        }

        total = 0.0
        for path, weight in scores.items():
            parts = path.split(".")
            value = data
            for part in parts:
                if isinstance(value, dict):
                    value = value.get(part)
                else:
                    value = None
                    break

            if value:
                if isinstance(value, list) and len(value) >= 3:
                    total += weight
                elif isinstance(value, list) and len(value) > 0:
                    total += weight * 0.7
                elif not isinstance(value, list):
                    total += weight

        return round(min(total, 1.0), 2)


vacancy_parser_service = VacancyParserService()
