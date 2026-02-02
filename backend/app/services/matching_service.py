"""
Service for matching resumes with vacancies.
Calculates weighted similarity scores and generates interview questions.
"""

import json
import logging
import math
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


# Weight categories with their keys
WEIGHT_CATEGORIES = {
    "core": "weight_core",
    "company": "weight_company",
    "workConditions": "weight_work_conditions",
    "requirements": "weight_requirements",
    "responsibilities": "weight_responsibilities",
    "hiringContext": "weight_hiring_context",
    "successCriteria": "weight_success_criteria",
    "differentiators": "weight_differentiators",
    "dealbreakers": "weight_dealbreakers",
}


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """
    Calculates cosine similarity between two vectors.
    
    Args:
        vec1: First vector
        vec2: Second vector
        
    Returns:
        Cosine similarity value between -1 and 1
    """
    if len(vec1) != len(vec2):
        raise ValueError(f"Vector dimensions don't match: {len(vec1)} vs {len(vec2)}")
    
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = math.sqrt(sum(a * a for a in vec1))
    magnitude2 = math.sqrt(sum(b * b for b in vec2))
    
    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0
    
    return dot_product / (magnitude1 * magnitude2)


class MatchingService:
    """Service for resume-vacancy matching."""

    def __init__(self) -> None:
        self.api_key = settings.openrouter_api_key
        self.model = settings.openrouter_model_fast  # Gemini Flash
        self.base_url = settings.openrouter_base_url

    def calculate_match_score(
        self,
        resume_embedding: list[float],
        vacancy_embedding: list[float],
        weights: dict[str, int] | None = None,
        gaps: dict[str, Any] | None = None,
    ) -> tuple[float, float, dict[str, dict[str, float]]]:
        """
        Calculates strict weighted match score for high-skilled specialist search.

        Scoring formula:
        - Cosine 0.5 = 0%, Cosine 1.0 = 100% (linear scale)
        - Gaps reduce score proportionally to category weights
        - Critical gaps (weight 9-10) cause significant penalties

        Args:
            resume_embedding: Resume vector
            vacancy_embedding: Vacancy vector
            weights: Category weights (0-10 scale)
            gaps: Identified gaps from analyze_gaps

        Returns:
            Tuple of (match_score 0-100, cosine_similarity, weighted_scores dict)
        """
        # Calculate base cosine similarity
        raw_similarity = cosine_similarity(resume_embedding, vacancy_embedding)
        
        # Strict linear scale: 0.5 = 0%, 1.0 = 100%
        # Formula: (cosine - 0.5) * 200
        base_score = max(0, min(100, (raw_similarity - 0.5) * 200))
        
        logger.info(f"Cosine similarity: {raw_similarity:.4f} -> Base score: {base_score:.1f}%")
        
        if not weights:
            return base_score, raw_similarity, {}

        # Calculate weighted category scores and penalties
        weighted_scores = {}
        total_weight = 0
        weighted_sum = 0
        total_penalty = 0

        # Map gaps to categories for penalty calculation
        gap_penalties = self._calculate_gap_penalties(gaps, weights)

        for category, weight_key in WEIGHT_CATEGORIES.items():
            weight = weights.get(weight_key, weights.get(category, 5))
            
            if weight == 0:
                # Category ignored
                weighted_scores[category] = {
                    "weight": 0,
                    "penalty": 0,
                    "contribution": 0,
                }
                continue

            # Get penalty for this category based on gaps
            category_penalty = gap_penalties.get(category, 0)
            
            # Category score = base_score minus penalty
            # Penalty impact scales with weight (critical categories hurt more)
            penalty_impact = category_penalty * (weight / 10)  # Scale by importance
            category_score = max(0, base_score - penalty_impact)
            
            # Weight contribution to final score
            contribution = category_score * weight
            
            weighted_scores[category] = {
                "weight": weight,
                "base_score": round(base_score, 2),
                "penalty": round(penalty_impact, 2),
                "category_score": round(category_score, 2),
                "contribution": round(contribution, 2),
            }
            
            total_weight += weight
            weighted_sum += contribution
            total_penalty += penalty_impact

        # Calculate final weighted score
        if total_weight > 0:
            final_score = weighted_sum / total_weight
        else:
            final_score = base_score

        # Clamp to 0-100
        final_score = max(0, min(100, final_score))

        logger.info(f"Final score: {final_score:.1f}% (base: {base_score:.1f}%, total penalty: {total_penalty:.1f})")

        return round(final_score, 2), raw_similarity, weighted_scores

    def _calculate_gap_penalties(
        self,
        gaps: dict[str, Any] | None,
        weights: dict[str, int],
    ) -> dict[str, float]:
        """
        Calculate penalties for each category based on identified gaps.
        
        Penalty scale:
        - Missing required skill: 15% per skill
        - Missing optional skill: 5% per skill
        - Insufficient experience: 20%
        - Missing must-have experience: 25%
        - Missing required language: 15%
        - Missing optional language: 5%
        """
        penalties = {cat: 0.0 for cat in WEIGHT_CATEGORIES}
        
        if not gaps:
            return penalties
        
        # Skills penalties -> affects "requirements" category
        missing_skills = gaps.get("missing_skills", [])
        for skill in missing_skills:
            if skill.get("required"):
                penalties["requirements"] += 15  # Required skill missing
            else:
                penalties["requirements"] += 5   # Optional skill missing
        
        # Experience penalties -> affects "requirements" and "core"
        experience_gaps = gaps.get("experience_gaps", [])
        for gap in experience_gaps:
            if gap.get("type") == "insufficient_years":
                # Calculate penalty based on how much experience is missing
                required = gap.get("required", 0)
                actual = gap.get("actual", 0)
                if required > 0:
                    deficit_ratio = (required - actual) / required
                    penalties["requirements"] += 20 * deficit_ratio
                    penalties["core"] += 10 * deficit_ratio
            elif gap.get("type") == "missing_must_have":
                penalties["requirements"] += 25  # Critical experience missing
                penalties["core"] += 15
        
        # Language penalties -> affects "requirements"
        language_gaps = gaps.get("language_gaps", [])
        for gap in language_gaps:
            if gap.get("is_required"):
                penalties["requirements"] += 15
            else:
                penalties["requirements"] += 5
        
        # Education gaps -> affects "requirements"
        education_gaps = gaps.get("education_gaps", [])
        for gap in education_gaps:
            penalties["requirements"] += 10
        
        # Other gaps
        other_gaps = gaps.get("other_gaps", [])
        for gap in other_gaps:
            penalties["differentiators"] += 5
        
        # Cap penalties at reasonable maximum per category
        for cat in penalties:
            penalties[cat] = min(penalties[cat], 80)  # Max 80% penalty per category
        
        logger.info(f"Gap penalties: {penalties}")
        
        return penalties

    async def analyze_gaps(
        self,
        resume_data: dict[str, Any],
        vacancy_data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Analyzes gaps between resume and vacancy requirements.

        Args:
            resume_data: Parsed resume data
            vacancy_data: Vacancy data

        Returns:
            Dict with identified gaps
        """
        gaps = {
            "missing_skills": [],
            "experience_gaps": [],
            "education_gaps": [],
            "language_gaps": [],
            "other_gaps": [],
        }

        # Extract resume skills
        resume_skills = set()
        for skill in resume_data.get("skills", []) or []:
            if skill.get("name"):
                resume_skills.add(skill["name"].lower())

        # Check required skills
        vacancy_requirements = vacancy_data.get("requirements", {}) or {}
        vacancy_skills = vacancy_requirements.get("skills", []) or []
        
        for skill in vacancy_skills:
            skill_name = skill.get("name", "")
            is_required = skill.get("isRequired") or skill.get("is_required", True)
            
            if skill_name and skill_name.lower() not in resume_skills:
                gaps["missing_skills"].append({
                    "skill": skill_name,
                    "required": is_required,
                    "level": skill.get("level"),
                })

        # Check experience requirements
        vacancy_experience = vacancy_requirements.get("experience", {}) or {}
        resume_experience_months = resume_data.get("totalExperienceMonths") or resume_data.get("total_experience_months", 0)
        
        required_years_min = vacancy_experience.get("yearsMin") or vacancy_experience.get("years_min", 0)
        if required_years_min and resume_experience_months:
            resume_years = resume_experience_months / 12
            if resume_years < required_years_min:
                gaps["experience_gaps"].append({
                    "type": "insufficient_years",
                    "required": required_years_min,
                    "actual": round(resume_years, 1),
                })

        # Check must-have experience
        must_have = vacancy_experience.get("mustHave") or vacancy_experience.get("must_have", [])
        if must_have:
            resume_exp_text = " ".join([
                f"{e.get('position', '')} {e.get('responsibilities', '')} {e.get('achievements', '')}"
                for e in resume_data.get("experience", []) or []
            ]).lower()
            
            for requirement in must_have:
                # Simple check - could be improved with NLP
                if requirement.lower() not in resume_exp_text:
                    gaps["experience_gaps"].append({
                        "type": "missing_must_have",
                        "requirement": requirement,
                    })

        # Check languages
        vacancy_languages = vacancy_requirements.get("languages", []) or []
        resume_languages = {
            (lang.get("name", "").lower(), lang.get("code", "").lower())
            for lang in resume_data.get("languages", []) or []
        }
        resume_lang_names = {name for name, code in resume_languages}
        resume_lang_codes = {code for name, code in resume_languages if code}

        for lang in vacancy_languages:
            lang_name = (lang.get("name", "") or "").lower()
            lang_code = (lang.get("code", "") or "").lower()
            is_required = lang.get("isRequired") or lang.get("is_required", True)
            
            if lang_name and lang_name not in resume_lang_names and lang_code not in resume_lang_codes:
                gaps["language_gaps"].append({
                    "language": lang.get("name"),
                    "required_level": lang.get("proficiency"),
                    "is_required": is_required,
                })

        return gaps

    async def identify_strengths(
        self,
        resume_data: dict[str, Any],
        vacancy_data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Identifies candidate strengths for this vacancy.

        Args:
            resume_data: Parsed resume data
            vacancy_data: Vacancy data

        Returns:
            Dict with identified strengths
        """
        strengths = {
            "matching_skills": [],
            "relevant_experience": [],
            "additional_value": [],
        }

        # Extract resume skills
        resume_skills = {}
        for skill in resume_data.get("skills", []) or []:
            if skill.get("name"):
                resume_skills[skill["name"].lower()] = skill

        # Check matching skills
        vacancy_requirements = vacancy_data.get("requirements", {}) or {}
        vacancy_skills = vacancy_requirements.get("skills", []) or []
        
        for v_skill in vacancy_skills:
            skill_name = v_skill.get("name", "")
            if skill_name and skill_name.lower() in resume_skills:
                r_skill = resume_skills[skill_name.lower()]
                strengths["matching_skills"].append({
                    "skill": skill_name,
                    "level": r_skill.get("level"),
                    "years": r_skill.get("yearsOfExperience") or r_skill.get("years_of_experience"),
                })

        # Check relevant experience
        resume_experience = resume_data.get("experience", []) or []
        vacancy_core = vacancy_data.get("core", {}) or {}
        target_position = (vacancy_core.get("jobTitle") or vacancy_core.get("job_title", "")).lower()

        for exp in resume_experience:
            position = (exp.get("position", "") or "").lower()
            # Simple relevance check - could be improved
            if target_position and any(word in position for word in target_position.split()):
                strengths["relevant_experience"].append({
                    "position": exp.get("position"),
                    "company": exp.get("companyName") or exp.get("company_name"),
                    "duration_months": exp.get("durationMonths") or exp.get("duration_months"),
                })

        return strengths

    async def generate_interview_questions(
        self,
        resume_data: dict[str, Any],
        vacancy_data: dict[str, Any],
        gaps: dict[str, Any],
    ) -> list[dict[str, str]]:
        """
        Generates targeted interview questions based on gaps.

        Args:
            resume_data: Parsed resume data
            vacancy_data: Vacancy data
            gaps: Identified gaps from analyze_gaps

        Returns:
            List of interview questions with topics
        """
        if not self.api_key:
            logger.warning("OpenRouter API key not configured, returning empty questions")
            return []

        # Build context for LLM
        vacancy_core = vacancy_data.get("core", {}) or {}
        job_title = vacancy_core.get("jobTitle") or vacancy_core.get("job_title", "")
        
        company = vacancy_data.get("company", {}) or {}
        company_name = company.get("name", "")
        activity_sphere = company.get("activitySphere") or company.get("activity_sphere") or {}
        sphere_name = activity_sphere.get("sphere", {}).get("name", "")

        candidate_name = ""
        personal = resume_data.get("personal", {}) or {}
        if personal.get("firstName") or personal.get("first_name"):
            candidate_name = f"{personal.get('firstName') or personal.get('first_name', '')} {personal.get('lastName') or personal.get('last_name', '')}".strip()

        prompt = f"""Сгенерируй 2-3 узкоспециализированных вопроса для первичного контакта рекрутера с кандидатом.

ВАКАНСИЯ: {job_title}
КОМПАНИЯ: {company_name}
СФЕРА: {sphere_name}

ВЫЯВЛЕННЫЕ ПРОБЕЛЫ (GAPS):
"""
        
        if gaps.get("missing_skills"):
            required_missing = [s for s in gaps["missing_skills"] if s.get("required")]
            if required_missing:
                skills_list = ", ".join([s["skill"] for s in required_missing[:5]])
                prompt += f"\n- Отсутствующие обязательные навыки: {skills_list}"

        if gaps.get("experience_gaps"):
            for gap in gaps["experience_gaps"][:3]:
                if gap.get("type") == "insufficient_years":
                    prompt += f"\n- Недостаточный опыт: требуется {gap['required']} лет, у кандидата {gap['actual']}"
                elif gap.get("type") == "missing_must_have":
                    prompt += f"\n- Отсутствует обязательный опыт: {gap['requirement']}"

        if gaps.get("language_gaps"):
            for gap in gaps["language_gaps"][:2]:
                if gap.get("is_required"):
                    prompt += f"\n- Не указан язык: {gap['language']} ({gap.get('required_level', '')})"

        prompt += """

ПРАВИЛА:
1. Вопросы должны быть КОНКРЕТНЫМИ и УЗКОСПЕЦИАЛИЗИРОВАННЫМИ
2. НЕ задавай общие вопросы типа "Расскажите о себе" или "Почему хотите работать у нас"
3. Вопросы должны помочь УТОЧНИТЬ пробелы - возможно кандидат имеет этот опыт, но не указал в резюме
4. Вопросы должны быть краткими и прямыми
5. Формулируй вежливо, но по делу

Верни JSON массив:
[
  {"topic": "краткая тема", "question": "текст вопроса"}
]

ТОЛЬКО JSON, без markdown."""

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": 0.7,
                        "max_tokens": 1000,
                    },
                )
                response.raise_for_status()
                data = response.json()

                content = data["choices"][0]["message"]["content"]
                
                # Parse JSON
                content = content.strip()
                if content.startswith("```"):
                    lines = content.split("\n")
                    if lines[-1].strip() == "```":
                        content = "\n".join(lines[1:-1])
                    else:
                        content = "\n".join(lines[1:])

                questions = json.loads(content)
                return questions[:3]  # Max 3 questions

        except Exception as e:
            logger.error(f"Failed to generate interview questions: {e}")
            # Return fallback questions based on gaps
            fallback = []
            if gaps.get("missing_skills"):
                skill = gaps["missing_skills"][0]["skill"]
                fallback.append({
                    "topic": f"Навык: {skill}",
                    "question": f"Есть ли у вас опыт работы с {skill}? Если да, расскажите о конкретных проектах."
                })
            return fallback


matching_service = MatchingService()
