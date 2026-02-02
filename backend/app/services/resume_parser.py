"""
Service for parsing resume text via OpenRouter API (Gemini Flash).
Extracts structured data from resume text.
"""

import json
import logging
from typing import Any

import httpx

from app.core.config import settings
from app.models.resume import ParseResumeResponse, ResumeInput

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """Ты — эксперт по HR и рекрутингу. Твоя задача — извлечь структурированные данные из текста резюме кандидата.

ВАЖНО: Извлекай ВСЕ данные максимально подробно, особенно опыт работы, навыки и достижения.

Верни JSON строго по следующей схеме:

{
  "personal": {
    "firstName": "string — имя",
    "lastName": "string — фамилия",
    "middleName": "string — отчество",
    "birthDate": "YYYY-MM-DD — дата рождения",
    "gender": "male|female|other"
  },
  "contacts": {
    "email": "string",
    "phone": "string",
    "phoneSecondary": "string",
    "telegram": "string — без @",
    "whatsapp": "string",
    "linkedinUrl": "string",
    "githubUrl": "string",
    "portfolioUrl": "string"
  },
  "desiredPosition": {
    "title": "string — желаемая должность",
    "salaryMin": number,
    "salaryMax": number,
    "salaryCurrency": "RUB|USD|EUR"
  },
  "location": {
    "city": "string",
    "region": "string",
    "country": "string",
    "willingToRelocate": boolean,
    "willingToTravel": boolean,
    "travelTimePercent": number
  },
  "employment": {
    "employmentType": "full-time|part-time|contract|freelance|internship",
    "scheduleType": "5/2|2/2|flexible|remote-async",
    "remotePreference": "office|remote|hybrid"
  },
  "summary": "string — краткое описание о себе, профессиональное резюме",
  "totalExperienceMonths": number — общий стаж в месяцах,
  "experience": [
    {
      "companyName": "string (ОБЯЗАТЕЛЬНО)",
      "companyIndustry": "string — отрасль компании",
      "companySize": "string — размер компании",
      "companyUrl": "string",
      "position": "string (ОБЯЗАТЕЛЬНО)",
      "department": "string",
      "startDate": "YYYY-MM-DD",
      "endDate": "YYYY-MM-DD или null если текущее место",
      "isCurrent": boolean,
      "durationMonths": number,
      "locationCity": "string",
      "locationCountry": "string",
      "responsibilities": "string — обязанности (подробно)",
      "achievements": "string — достижения (подробно)",
      "technologies": ["string — используемые технологии"]
    }
  ],
  "education": [
    {
      "institutionName": "string (ОБЯЗАТЕЛЬНО)",
      "institutionType": "university|college|school|course|bootcamp",
      "faculty": "string",
      "specialization": "string",
      "degree": "secondary|vocational|bachelor|master|phd|mba",
      "startYear": number,
      "endYear": number,
      "isCurrent": boolean,
      "locationCity": "string",
      "locationCountry": "string",
      "description": "string",
      "gpa": number
    }
  ],
  "skills": [
    {
      "name": "string (ОБЯЗАТЕЛЬНО)",
      "category": "hard|soft|management|digital_tool",
      "level": "basic|intermediate|advanced|expert",
      "yearsOfExperience": number,
      "lastUsedYear": number
    }
  ],
  "languages": [
    {
      "name": "string (ОБЯЗАТЕЛЬНО) — название языка",
      "code": "string — ru, en, de",
      "proficiency": "A1|A2|B1|B2|C1|C2|native",
      "isNative": boolean
    }
  ],
  "certificates": [
    {
      "name": "string (ОБЯЗАТЕЛЬНО)",
      "issuingOrganization": "string",
      "issueDate": "YYYY-MM-DD",
      "expiryDate": "YYYY-MM-DD",
      "credentialId": "string",
      "credentialUrl": "string",
      "description": "string"
    }
  ]
}

ПРАВИЛА:
1. Извлекай ТОЛЬКО то, что явно указано в тексте. Не додумывай.
2. Если информация отсутствует — не включай поле в ответ.
3. Для навыков определяй категорию:
   - hard: технические навыки (языки программирования, фреймворки, инструменты)
   - soft: мягкие навыки (коммуникация, критическое мышление)
   - management: управленческие навыки (менторство, планирование, найм)
   - digital_tool: цифровые инструменты (Jira, Figma, Notion)
4. Обязательно извлекай ВСЕ места работы с обязанностями и достижениями.
5. Вычисляй totalExperienceMonths суммируя все места работы.
6. Отвечай ТОЛЬКО валидным JSON без markdown-обёртки."""


class ResumeParserService:
    """Service for parsing resume text via LLM."""

    def __init__(self) -> None:
        self.api_key = settings.openrouter_api_key
        self.model = settings.openrouter_model_fast  # Gemini Flash
        self.base_url = settings.openrouter_base_url

    async def parse(self, text: str) -> ParseResumeResponse:
        """
        Parses resume text and returns structured data.

        Args:
            text: Raw resume text

        Returns:
            ParseResumeResponse with parsed data
        """
        try:
            raw_response = await self._call_llm(text)
            parsed_data = self._parse_llm_response(raw_response)
            return self._build_response(parsed_data, text)
        except Exception as e:
            logger.error(f"Failed to parse resume: {e}")
            raise

    async def _call_llm(self, text: str) -> str:
        """Calls OpenRouter API with Gemini Flash."""
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not configured")

        user_prompt = f"Извлеки структурированные данные из следующего резюме:\n\n{text}"

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
                    "temperature": 0.1,
                    "max_tokens": 8000,
                },
            )
            response.raise_for_status()
            data = response.json()
            logger.debug(f"OpenRouter response: {data}")

            if not data.get("choices"):
                logger.error(f"No choices in response: {data}")
                raise ValueError(f"Invalid API response: {data}")

            content = data["choices"][0].get("message", {}).get("content")
            if not content:
                logger.error(f"No content in response: {data}")
                raise ValueError("Empty response from LLM")

            return content

    def _parse_llm_response(self, raw: str) -> dict[str, Any]:
        """Parses JSON from LLM response."""
        if not raw:
            raise ValueError("Empty LLM response")

        content = raw.strip()

        # Remove markdown wrapper if present
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
            raise ValueError(f"Invalid JSON from LLM: {e}")

    def _build_response(
        self,
        parsed_data: dict[str, Any],
        original_text: str,
    ) -> ParseResumeResponse:
        """Builds response with validation and metrics."""
        warnings: list[str] = []
        missing_fields: list[str] = []

        # Check recommended fields
        recommended_checks = [
            ("personal.firstName", self._get_nested(parsed_data, "personal.firstName")),
            ("personal.lastName", self._get_nested(parsed_data, "personal.lastName")),
            ("contacts.email", self._get_nested(parsed_data, "contacts.email")),
            ("contacts.phone", self._get_nested(parsed_data, "contacts.phone")),
            ("experience", parsed_data.get("experience")),
            ("skills", parsed_data.get("skills")),
        ]

        for field_name, value in recommended_checks:
            if not value:
                missing_fields.append(field_name)

        # Check experience quality
        experience = parsed_data.get("experience", [])
        if experience and len(experience) < 1:
            warnings.append("Не найден опыт работы")
        
        skills = parsed_data.get("skills", [])
        if skills and len(skills) < 3:
            warnings.append(
                f"Извлечено мало навыков ({len(skills)}). "
                "Возможно, стоит добавить больше для точного сопоставления."
            )

        confidence = self._calculate_confidence(parsed_data)

        # Validate and create model
        resume_input = ResumeInput.model_validate(parsed_data)
        resume_input.full_text = {"text": original_text, "source": "imported"}

        return ParseResumeResponse(
            data=resume_input,
            confidence=confidence,
            warnings=warnings if warnings else None,
            missing_fields=missing_fields if missing_fields else None,
        )

    def _get_nested(self, data: dict, path: str) -> Any:
        """Gets nested value by dot-separated path."""
        parts = path.split(".")
        value = data
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None
        return value

    def _calculate_confidence(self, data: dict[str, Any]) -> float:
        """Calculates parser confidence based on data completeness."""
        scores = {
            "personal.firstName": 0.1,
            "personal.lastName": 0.1,
            "contacts.email": 0.05,
            "contacts.phone": 0.05,
            "desiredPosition.title": 0.1,
            "experience": 0.25,
            "skills": 0.2,
            "education": 0.1,
            "languages": 0.05,
        }

        total = 0.0
        for path, weight in scores.items():
            value = self._get_nested(data, path) if "." in path else data.get(path)

            if value:
                if isinstance(value, list) and len(value) >= 2:
                    total += weight
                elif isinstance(value, list) and len(value) > 0:
                    total += weight * 0.7
                elif not isinstance(value, list):
                    total += weight

        return round(min(total, 1.0), 2)


resume_parser_service = ResumeParserService()
