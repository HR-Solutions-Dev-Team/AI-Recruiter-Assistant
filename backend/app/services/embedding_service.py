"""
Service for creating text embeddings using OpenRouter API.
Used for resume and vacancy vectorization.
"""

import logging
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for creating text embeddings via OpenRouter."""

    def __init__(self) -> None:
        self.api_key = settings.openrouter_api_key
        self.base_url = "https://openrouter.ai/api/v1"
        # Use multilingual model that works with Russian
        self.model = "intfloat/multilingual-e5-large"
        self.dimensions = 1024  # This model outputs 1024 dimensions

    async def create_embedding(self, text: str) -> list[float]:
        """
        Creates embedding vector for given text.

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding vector
        """
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not configured")

        try:
            # Truncate text if too long
            truncated_text = text[:30000] if len(text) > 30000 else text

            async with httpx.AsyncClient(timeout=60.0) as client:
                request_body = {
                    "model": self.model,
                    "input": truncated_text,
                    "encoding_format": "float",
                }
                
                logger.info(f"Embedding request: model={self.model}, input_len={len(truncated_text)}")
                
                response = await client.post(
                    f"{self.base_url}/embeddings",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://ai-recruiter.local",
                        "X-Title": "AI Recruiter Assistant",
                    },
                    json=request_body,
                )
                
                logger.info(f"Embedding response status: {response.status_code}")
                
                data = response.json()
                logger.info(f"Embedding response keys: {list(data.keys())}")
                
                if "error" in data:
                    logger.error(f"OpenRouter error: {data['error']}")
                    raise ValueError(f"OpenRouter error: {data['error'].get('message', 'Unknown error')}")
                
                if "data" not in data or len(data["data"]) == 0:
                    logger.error(f"No embedding data in response: {data}")
                    raise ValueError("No embedding data received")
                
                embedding = data["data"][0]["embedding"]
                logger.info(f"Created embedding with {len(embedding)} dimensions")
                return embedding

        except Exception as e:
            logger.error(f"Failed to create embedding: {e}")
            raise

    async def create_resume_embedding(self, resume_data: dict[str, Any]) -> list[float]:
        """
        Creates embedding for resume data.
        Uses full text if available, otherwise constructs from structured data.

        Args:
            resume_data: Parsed resume data dict

        Returns:
            Embedding vector
        """
        # First try to use full text if available
        full_text_data = resume_data.get("fullText") or resume_data.get("full_text")
        if full_text_data and full_text_data.get("text"):
            full_text = full_text_data["text"]
            logger.info(f"Using full text for resume embedding ({len(full_text)} chars)")
            return await self.create_embedding(full_text)
        
        # Otherwise construct from structured data
        text_parts = []

        # Desired position (important for matching)
        desired = resume_data.get("desiredPosition") or resume_data.get("desired_position") or {}
        if desired.get("title"):
            text_parts.append(f"Желаемая должность: {desired['title']}")

        # Summary
        if resume_data.get("summary"):
            text_parts.append(f"О себе: {resume_data['summary']}")

        # Experience (most important)
        experience = resume_data.get("experience", []) or []
        for exp in experience:
            exp_text = f"Опыт работы: {exp.get('position', '')} в {exp.get('companyName') or exp.get('company_name', '')}"
            if exp.get("responsibilities"):
                exp_text += f". Обязанности: {exp['responsibilities']}"
            if exp.get("achievements"):
                exp_text += f". Достижения: {exp['achievements']}"
            if exp.get("technologies"):
                techs = exp["technologies"] if isinstance(exp["technologies"], list) else [exp["technologies"]]
                exp_text += f". Технологии: {', '.join(techs)}"
            text_parts.append(exp_text)

        # Skills (very important for matching)
        skills = resume_data.get("skills", []) or []
        if skills:
            skill_names = [s.get("name", "") for s in skills if s.get("name")]
            if skill_names:
                text_parts.append(f"Навыки: {', '.join(skill_names)}")

        # Education
        education = resume_data.get("education", []) or []
        for edu in education:
            edu_text = f"Образование: {edu.get('institutionName') or edu.get('institution_name', '')}"
            if edu.get("specialization"):
                edu_text += f", {edu['specialization']}"
            if edu.get("degree"):
                edu_text += f", {edu['degree']}"
            text_parts.append(edu_text)

        # Languages
        languages = resume_data.get("languages", []) or []
        if languages:
            lang_texts = []
            for lang in languages:
                lang_text = lang.get("name", "")
                if lang.get("proficiency"):
                    lang_text += f" ({lang['proficiency']})"
                lang_texts.append(lang_text)
            if lang_texts:
                text_parts.append(f"Языки: {', '.join(lang_texts)}")

        # Location
        location = resume_data.get("location", {}) or {}
        if location.get("city"):
            text_parts.append(f"Город: {location['city']}")

        full_text = "\n".join(text_parts)
        
        if not full_text.strip():
            raise ValueError("No text data available for embedding")
        
        logger.info(f"Resume embedding text ({len(full_text)} chars): {full_text[:200]}...")

        return await self.create_embedding(full_text)

    async def create_vacancy_embedding(self, vacancy_data: dict[str, Any]) -> list[float]:
        """
        Creates embedding for vacancy data.
        Constructs a text representation optimized for matching.

        Args:
            vacancy_data: Vacancy data dict

        Returns:
            Embedding vector
        """
        text_parts = []

        # Core info
        core = vacancy_data.get("core", {}) or {}
        if core.get("jobTitle") or core.get("job_title"):
            text_parts.append(f"Должность: {core.get('jobTitle') or core.get('job_title')}")
        if core.get("synonyms"):
            text_parts.append(f"Синонимы: {', '.join(core['synonyms'])}")

        career_level = core.get("careerLevel") or core.get("career_level") or {}
        if career_level.get("code"):
            text_parts.append(f"Уровень: {career_level['code']}")

        # Company
        company = vacancy_data.get("company", {}) or {}
        if company.get("name"):
            text_parts.append(f"Компания: {company['name']}")
        activity = company.get("activitySphere") or company.get("activity_sphere") or {}
        if activity.get("sphere", {}).get("name"):
            text_parts.append(f"Сфера: {activity['sphere']['name']}")

        # Requirements (important for matching)
        requirements = vacancy_data.get("requirements", {}) or {}
        
        skills = requirements.get("skills", []) or []
        if skills:
            required_skills = [s.get("name") for s in skills if s.get("isRequired") or s.get("is_required")]
            optional_skills = [s.get("name") for s in skills if not (s.get("isRequired") or s.get("is_required"))]
            if required_skills:
                text_parts.append(f"Обязательные навыки: {', '.join(filter(None, required_skills))}")
            if optional_skills:
                text_parts.append(f"Желательные навыки: {', '.join(filter(None, optional_skills))}")

        experience = requirements.get("experience", {}) or {}
        if experience.get("mustHave") or experience.get("must_have"):
            must_have = experience.get("mustHave") or experience.get("must_have")
            text_parts.append(f"Обязательный опыт: {', '.join(must_have)}")
        if experience.get("domains"):
            text_parts.append(f"Домены: {', '.join(experience['domains'])}")

        languages = requirements.get("languages", []) or []
        if languages:
            lang_texts = []
            for lang in languages:
                lang_text = lang.get("name", "")
                if lang.get("proficiency"):
                    lang_text += f" ({lang['proficiency']})"
                lang_texts.append(lang_text)
            text_parts.append(f"Языки: {', '.join(lang_texts)}")

        # Responsibilities
        responsibilities = vacancy_data.get("responsibilities", {}) or {}
        if responsibilities.get("scope"):
            text_parts.append(f"Зона ответственности: {responsibilities['scope']}")
        if responsibilities.get("zones"):
            text_parts.append(f"Обязанности: {', '.join(responsibilities['zones'])}")

        # Work conditions
        work_conditions = vacancy_data.get("workConditions") or vacancy_data.get("work_conditions") or {}
        location = work_conditions.get("location", {}) or {}
        if location.get("city"):
            text_parts.append(f"Город: {location['city']}")
        if location.get("remote"):
            text_parts.append(f"Формат работы: {location['remote']}")

        full_text = "\n".join(text_parts)
        logger.debug(f"Vacancy embedding text ({len(full_text)} chars): {full_text[:500]}...")

        return await self.create_embedding(full_text)


embedding_service = EmbeddingService()
