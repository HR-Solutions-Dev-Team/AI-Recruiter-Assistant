"""
Сервис для обогащения вакансий через LLM.
Генерирует контекстные вопросы по незаполненным полям.
Оптимизировано для google/gemini-2.5-flash.
"""

import json
import logging
from typing import Any

import httpx
from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger(__name__)


class EnrichmentOption(BaseModel):
    """Вариант ответа на вопрос."""

    value: str
    description: str | None = None


class EnrichmentQuestion(BaseModel):
    """Вопрос для обогащения вакансии."""

    field_path: str
    question_text: str
    options: list[EnrichmentOption]
    allow_custom: bool = True
    depends_on: str | None = None


class EnrichmentAnswerResult(BaseModel):
    """Результат обработки ответа."""

    field_path: str
    updated_value: Any
    new_completion_percent: int


class QAHistoryItem(BaseModel):
    """Элемент истории вопрос-ответ."""
    
    question: str
    answer: str
    field_path: str


def _safe_get(d: dict, *keys: str) -> Any:
    """Безопасно получает вложенное значение из словаря."""
    result = d
    for key in keys:
        if result is None or not isinstance(result, dict):
            return None
        result = result.get(key)
    return result


# ============================================================================
# КАТЕГОРИИ ВОПРОСОВ (для выбора пользователем)
# ============================================================================

QUESTION_CATEGORIES = {
    "business_context": {
        "name": "Бизнес-контекст",
        "description": "Почему открыта вакансия, какую проблему решаем",
        "fields": [
            "hiringContext.businessProblem",
            "hiringContext.triggerEvent", 
            "hiringContext.expectedImpact",
        ],
    },
    "success_criteria": {
        "name": "Критерии успеха",
        "description": "KPI, milestones, ожидания от кандидата",
        "fields": [
            "successCriteria.onboardingMilestones",
            "successCriteria.shortTermKPIs",
        ],
    },
    "ideal_candidate": {
        "name": "Идеальный кандидат",
        "description": "Опыт, достижения, бэкграунд",
        "fields": [
            "differentiators.industryExpertise",
            "differentiators.scaleExperience",
            "differentiators.achievementMarkers",
            "differentiators.companyBackground",
        ],
    },
    "requirements": {
        "name": "Требования",
        "description": "Обязательные навыки и опыт",
        "fields": [
            "dealbreakers.absoluteRequirements",
            "dealbreakers.experienceMinimums",
            "dealbreakers.nonNegotiables",
            "dealbreakers.redFlags",
            "requirements.skills",
        ],
    },
    "responsibilities": {
        "name": "Обязанности",
        "description": "Зоны ответственности и задачи",
        "fields": [
            "responsibilities.criticalTasks",
            "responsibilities.zones",
        ],
    },
    "basics": {
        "name": "Базовая информация",
        "description": "Уровень, отрасль, условия",
        "fields": [
            "core.careerLevel.code",
            "core.industry",
            "workConditions.salary",
            "workConditions.location",
            "orgStructure.reportsTo",
        ],
    },
}


# ============================================================================
# ПРИОРИТЕТЫ ПОЛЕЙ
# ============================================================================

FIELD_PRIORITIES: list[dict[str, Any]] = [
    # Priority 1: Бизнес-контекст
    {
        "path": "hiringContext.businessProblem",
        "priority": 1,
        "label": "Бизнес-проблема",
        "check": lambda d: bool(_safe_get(d, "hiringContext", "businessProblem")),
    },
    {
        "path": "hiringContext.triggerEvent",
        "priority": 1,
        "label": "Причина открытия",
        "check": lambda d: bool(_safe_get(d, "hiringContext", "triggerEvent", "type")),
    },
    {
        "path": "successCriteria.onboardingMilestones",
        "priority": 1,
        "label": "Milestones 90 дней",
        "check": lambda d: len(_safe_get(d, "successCriteria", "onboardingMilestones") or []) >= 2,
    },
    {
        "path": "differentiators.industryExpertise",
        "priority": 1,
        "label": "Отраслевая экспертиза",
        "check": lambda d: bool(_safe_get(d, "differentiators", "industryExpertise", "industries")),
    },
    # Priority 2: Профиль кандидата
    {
        "path": "dealbreakers.absoluteRequirements",
        "priority": 2,
        "label": "Абсолютные требования",
        "check": lambda d: bool(_safe_get(d, "dealbreakers", "absoluteRequirements")),
    },
    {
        "path": "responsibilities.criticalTasks",
        "priority": 2,
        "label": "Критические задачи",
        "check": lambda d: len(_safe_get(d, "responsibilities", "criticalTasks") or []) >= 2,
    },
    {
        "path": "differentiators.scaleExperience",
        "priority": 2,
        "label": "Масштаб опыта",
        "check": lambda d: bool(_safe_get(d, "differentiators", "scaleExperience")),
    },
    {
        "path": "successCriteria.shortTermKPIs",
        "priority": 2,
        "label": "KPI на 6 месяцев",
        "check": lambda d: len(_safe_get(d, "successCriteria", "shortTermKPIs") or []) >= 2,
        "depends_on": "successCriteria.onboardingMilestones",
    },
    {
        "path": "differentiators.achievementMarkers",
        "priority": 2,
        "label": "Достижения кандидата",
        "check": lambda d: len(_safe_get(d, "differentiators", "achievementMarkers") or []) >= 2,
    },
    {
        "path": "hiringContext.expectedImpact",
        "priority": 2,
        "label": "Ожидаемый результат",
        "check": lambda d: bool(_safe_get(d, "hiringContext", "expectedImpact")),
        "depends_on": "hiringContext.businessProblem",
    },
    {
        "path": "dealbreakers.experienceMinimums",
        "priority": 2,
        "label": "Минимальный опыт",
        "check": lambda d: bool(_safe_get(d, "dealbreakers", "experienceMinimums", "totalYears")),
    },
    # Priority 3: Детализация
    {
        "path": "core.careerLevel.code",
        "priority": 3,
        "label": "Уровень позиции",
        "check": lambda d: bool(_safe_get(d, "core", "careerLevel", "code")),
    },
    {
        "path": "dealbreakers.nonNegotiables",
        "priority": 3,
        "label": "Не обсуждаемые требования",
        "check": lambda d: bool(_safe_get(d, "dealbreakers", "nonNegotiables")),
    },
    {
        "path": "responsibilities.zones",
        "priority": 3,
        "label": "Зоны ответственности",
        "check": lambda d: len(_safe_get(d, "responsibilities", "zones") or []) >= 3,
    },
    {
        "path": "requirements.skills",
        "priority": 3,
        "label": "Ключевые навыки",
        "check": lambda d: len(_safe_get(d, "requirements", "skills") or []) >= 3,
    },
    {
        "path": "differentiators.companyBackground",
        "priority": 3,
        "label": "Предпочтительный бэкграунд",
        "check": lambda d: bool(_safe_get(d, "differentiators", "companyBackground", "preferred")),
    },
    {
        "path": "dealbreakers.redFlags",
        "priority": 3,
        "label": "Red flags",
        "check": lambda d: bool(_safe_get(d, "dealbreakers", "redFlags")),
    },
    # Priority 4: Дополнительно
    {
        "path": "core.industry",
        "priority": 4,
        "label": "Отрасль",
        "check": lambda d: bool(_safe_get(d, "core", "industry", "name")),
    },
    {
        "path": "workConditions.salary",
        "priority": 4,
        "label": "Зарплата",
        "check": lambda d: bool(_safe_get(d, "workConditions", "salary")),
    },
    {
        "path": "workConditions.location",
        "priority": 4,
        "label": "Локация",
        "check": lambda d: bool(_safe_get(d, "workConditions", "location")),
    },
    {
        "path": "orgStructure.reportsTo",
        "priority": 4,
        "label": "Подчинение",
        "check": lambda d: bool(_safe_get(d, "orgStructure", "reportsTo")),
    },
    {
        "path": "requirements.languages",
        "priority": 4,
        "label": "Языки",
        "check": lambda d: bool(_safe_get(d, "requirements", "languages")),
    },
]


# ============================================================================
# ОПТИМИЗИРОВАННЫЙ ПРОМПТ (короткий и точный)
# ============================================================================

QUESTION_GENERATION_PROMPT = """Ты — HR-эксперт по Executive Search. Помоги рекрутеру собрать информацию для поиска РЕДКОГО специалиста.

ВАКАНСИЯ: {job_title}
{vacancy_summary}

ИСТОРИЯ ОТВЕТОВ:
{qa_history}

ЗАДАЧА: Сгенерируй {num_questions} уточняющих вопроса для полей: {field_paths}

ПРАВИЛА:
- Вопросы должны быть конкретными и помогать отличить идеального кандидата от среднего
- Опции — это примеры ответов, не ограничивай ими рекрутера
- Учитывай уже полученные ответы, не повторяй вопросы
- Отвечай ТОЛЬКО JSON без markdown

ФОРМАТ:
{{"questions": [
  {{"field_path": "...", "question": "...", "options": [{{"value": "...", "description": "..."}}]}}
]}}"""


ANSWER_PROCESSING_PROMPT = """Преобразуй ответ рекрутера в структурированные данные.

Поле: {field_path}
Ответ: {answer}

Верни JSON: {{"value": ...}}

Типы данных:
- triggerEvent: {{"type": "growth|replacement|new_direction|crisis", "description": "..."}}
- onboardingMilestones: [{{"milestone": "...", "timeframe": "30_days|60_days|90_days", "measureOfSuccess": "..."}}]
- shortTermKPIs: [{{"metric": "...", "currentValue": "...", "targetValue": "..."}}]
- industryExpertise: {{"industries": ["..."], "whyMatters": "..."}}
- scaleExperience: {{"teamSize": {{"min": N}}, "dataVolume": "...", "usersScale": "..."}}
- achievementMarkers: [{{"achievement": "...", "importance": "must_have|strong_plus|nice_to_have"}}]
- absoluteRequirements: [{{"requirement": "...", "reason": "..."}}]
- experienceMinimums: {{"totalYears": N, "domainYears": N, "leadershipYears": N}}
- criticalTasks: [{{"task": "...", "deadline": "30|60|90 дней", "successIndicator": "..."}}]
- zones/redFlags/nonNegotiables: ["..."]
- careerLevel.code: "intern|junior|middle|senior|lead|head|director|c-level"
- Простые строки: {{"value": "..."}}"""


class EnrichmentService:
    """Сервис для обогащения вакансий через LLM."""

    def __init__(self) -> None:
        self.api_key = settings.openrouter_api_key
        self.model = settings.openrouter_model
        self.base_url = settings.openrouter_base_url

    def get_available_categories(self) -> dict[str, dict]:
        """Возвращает доступные категории вопросов для UI."""
        return QUESTION_CATEGORIES

    async def get_next_questions(
        self,
        vacancy_data: dict[str, Any],
        asked_fields: list[str] | None = None,
        qa_history: list[dict[str, str]] | None = None,
        priority_categories: list[str] | None = None,
        max_questions: int = 2,
    ) -> list[EnrichmentQuestion]:
        """
        Генерирует до max_questions вопросов за один LLM вызов.
        
        Args:
            vacancy_data: Текущие данные вакансии
            asked_fields: Поля, по которым уже задавали вопросы
            qa_history: История вопрос-ответ для контекста
            priority_categories: Категории вопросов выбранные пользователем
            max_questions: Количество вопросов (по умолчанию 2)
        
        Returns:
            Список вопросов
        """
        asked_fields = asked_fields or []
        qa_history = qa_history or []
        
        # Находим незаполненные поля
        candidate_fields = self._get_candidate_fields(
            vacancy_data, asked_fields, priority_categories
        )
        
        if not candidate_fields:
            return []
        
        # Берём до max_questions полей
        fields_to_ask = candidate_fields[:max_questions]
        
        try:
            questions = await self._generate_questions_batch(
                vacancy_data=vacancy_data,
                field_paths=[f["path"] for f in fields_to_ask],
                qa_history=qa_history,
            )
            return questions
        except Exception as e:
            logger.error(f"Failed to generate questions: {e}")
            # Fallback: пропускаем и пробуем следующие поля
            return []

    def _get_candidate_fields(
        self,
        vacancy_data: dict[str, Any],
        asked_fields: list[str],
        priority_categories: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Возвращает список незаполненных полей для вопросов."""
        candidates = []
        
        # Если пользователь выбрал категории — фильтруем
        allowed_fields = None
        if priority_categories:
            allowed_fields = set()
            for cat_key in priority_categories:
                if cat_key in QUESTION_CATEGORIES:
                    allowed_fields.update(QUESTION_CATEGORIES[cat_key]["fields"])
        
        for field_info in FIELD_PRIORITIES:
            field_path = field_info["path"]
            
            # Фильтр по категориям
            if allowed_fields and field_path not in allowed_fields:
                continue
            
            # Пропускаем уже спрошенные
            if field_path in asked_fields:
                continue
            
            # Проверяем заполненность
            if field_info["check"](vacancy_data):
                continue
            
            # Проверяем зависимости
            depends_on = field_info.get("depends_on")
            if depends_on:
                dep_field = next(
                    (f for f in FIELD_PRIORITIES if f["path"] == depends_on), None
                )
                if dep_field and not dep_field["check"](vacancy_data):
                    continue
            
            candidates.append(field_info)
        
        return candidates

    async def _generate_questions_batch(
        self,
        vacancy_data: dict[str, Any],
        field_paths: list[str],
        qa_history: list[dict[str, str]],
    ) -> list[EnrichmentQuestion]:
        """Генерирует несколько вопросов за один LLM вызов."""
        
        job_title = _safe_get(vacancy_data, "core", "jobTitle") or "Вакансия"
        
        # Формируем краткое саммари вакансии
        vacancy_summary = self._build_vacancy_summary(vacancy_data)
        
        # Формируем историю Q-A
        qa_history_str = self._format_qa_history(qa_history)
        
        # Получаем labels полей
        field_labels = []
        for fp in field_paths:
            field_info = next((f for f in FIELD_PRIORITIES if f["path"] == fp), None)
            if field_info:
                field_labels.append(f"{fp} ({field_info['label']})")
            else:
                field_labels.append(fp)
        
        prompt = QUESTION_GENERATION_PROMPT.format(
            job_title=job_title,
            vacancy_summary=vacancy_summary,
            qa_history=qa_history_str or "Пока нет ответов",
            num_questions=len(field_paths),
            field_paths=", ".join(field_labels),
        )
        
        response = await self._call_llm(prompt)
        if not response:
            return []
        
        try:
            data = json.loads(response)
            questions = []
            
            for q_data in data.get("questions", []):
                field_path = q_data.get("field_path", "")
                if field_path not in field_paths:
                    # Если LLM вернул другое поле — игнорируем
                    continue
                
                options = [
                    EnrichmentOption(
                        value=opt.get("value", ""),
                        description=opt.get("description"),
                    )
                    for opt in q_data.get("options", [])
                ]
                
                questions.append(EnrichmentQuestion(
                    field_path=field_path,
                    question_text=q_data.get("question", f"Укажите {field_path}"),
                    options=options,
                    allow_custom=True,
                ))
            
            return questions
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return []

    def _build_vacancy_summary(self, vacancy_data: dict[str, Any]) -> str:
        """Строит краткое саммари заполненных полей вакансии."""
        parts = []
        
        # Core info
        career_level = _safe_get(vacancy_data, "core", "careerLevel", "code")
        if career_level:
            parts.append(f"Уровень: {career_level}")
        
        industry = _safe_get(vacancy_data, "core", "industry", "name")
        if industry:
            parts.append(f"Отрасль: {industry}")
        
        # Company
        company_name = _safe_get(vacancy_data, "company", "name")
        if company_name:
            parts.append(f"Компания: {company_name}")
        
        company_type = _safe_get(vacancy_data, "company", "type")
        if company_type:
            parts.append(f"Тип: {company_type}")
        
        # Business problem
        problem = _safe_get(vacancy_data, "hiringContext", "businessProblem")
        if problem:
            parts.append(f"Проблема: {problem[:100]}")
        
        # Skills count
        skills = _safe_get(vacancy_data, "requirements", "skills") or []
        if skills:
            parts.append(f"Навыков указано: {len(skills)}")
        
        if not parts:
            return "Данные пока минимальны"
        
        return "\n".join(parts)

    def _format_qa_history(self, qa_history: list[dict[str, str]]) -> str:
        """Форматирует историю Q-A для промпта."""
        if not qa_history:
            return ""
        
        lines = []
        for item in qa_history[-10:]:  # Последние 10 ответов
            q = item.get("question", "")[:80]
            a = item.get("answer", "")[:100]
            lines.append(f"Q: {q}\nA: {a}")
        
        return "\n".join(lines)

    async def get_next_question(
        self,
        vacancy_data: dict[str, Any],
        asked_fields: list[str] | None = None,
    ) -> EnrichmentQuestion | None:
        """
        Legacy метод для совместимости. Возвращает один вопрос.
        """
        questions = await self.get_next_questions(
            vacancy_data=vacancy_data,
            asked_fields=asked_fields,
            max_questions=1,
        )
        return questions[0] if questions else None

    async def process_answer(
        self,
        vacancy_data: dict[str, Any],
        field_path: str,
        answer: str,
    ) -> dict[str, Any]:
        """
        Обрабатывает ответ пользователя и обновляет данные вакансии.
        """
        try:
            processed_value = await self._process_answer_with_llm(
                vacancy_data=vacancy_data,
                field_path=field_path,
                answer=answer,
            )
            
            updated_data = self._update_vacancy_data(
                vacancy_data=vacancy_data,
                field_path=field_path,
                value=processed_value,
            )
            
            return updated_data
            
        except Exception as e:
            logger.error(f"Failed to process answer for {field_path}: {e}")
            # Fallback: простое присвоение
            return self._update_vacancy_data(
                vacancy_data=vacancy_data,
                field_path=field_path,
                value=answer,
            )

    async def _process_answer_with_llm(
        self,
        vacancy_data: dict[str, Any],
        field_path: str,
        answer: str,
    ) -> Any:
        """Преобразует ответ пользователя в структурированные данные."""
        prompt = ANSWER_PROCESSING_PROMPT.format(
            field_path=field_path,
            answer=answer,
        )
        
        response = await self._call_llm(prompt)
        if not response:
            return answer
        
        try:
            data = json.loads(response)
            return data.get("value", answer)
        except json.JSONDecodeError:
            return answer

    async def _call_llm(self, prompt: str) -> str | None:
        """Вызывает OpenRouter API с оптимизированными параметрами."""
        if not self.api_key:
            logger.error("OPENROUTER_API_KEY not configured")
            return None
        
        try:
            async with httpx.AsyncClient(timeout=25.0) as client:
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
                        "temperature": 0.2,  # Снижена для стабильности
                        "max_tokens": 1500,
                        "response_format": {"type": "json_object"},  # JSON mode
                    },
                )
                response.raise_for_status()
                data = response.json()
                
                if not data.get("choices"):
                    return None
                
                content = data["choices"][0].get("message", {}).get("content")
                return self._clean_json_response(content) if content else None
                
        except httpx.TimeoutException:
            logger.warning("LLM call timeout - skipping")
            return None
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
        return content

    def _update_vacancy_data(
        self,
        vacancy_data: dict[str, Any],
        field_path: str,
        value: Any,
    ) -> dict[str, Any]:
        """Обновляет данные вакансии по пути к полю."""
        import copy
        
        updated = copy.deepcopy(vacancy_data)
        parts = field_path.split(".")
        
        # Навигация до родительского объекта
        current = updated
        for part in parts[:-1]:
            if part not in current or current[part] is None:
                current[part] = {}
            current = current[part]
        
        final_key = parts[-1]
        
        # Специальная обработка для некоторых полей
        if field_path == "core.careerLevel.code" and isinstance(value, str):
            current[final_key] = value
            
        elif field_path.endswith(".sphere") or field_path.endswith(".subSphere"):
            if isinstance(value, str):
                current[final_key] = {"name": value}
            else:
                current[final_key] = value
                
        elif field_path == "hiringContext.triggerEvent":
            if isinstance(value, str):
                current[final_key] = {"type": value, "description": ""}
            else:
                current[final_key] = value
                
        elif field_path == "differentiators.industryExpertise":
            if isinstance(value, list):
                current[final_key] = {"industries": value, "whyMatters": ""}
            elif isinstance(value, str):
                current[final_key] = {"industries": [value], "whyMatters": ""}
            else:
                current[final_key] = value
                
        elif field_path == "differentiators.scaleExperience":
            if isinstance(value, str):
                current[final_key] = {"teamSize": {"description": value}}
            else:
                current[final_key] = value
                
        elif field_path == "dealbreakers.experienceMinimums":
            if isinstance(value, int):
                current[final_key] = {"totalYears": value}
            elif isinstance(value, str) and value.isdigit():
                current[final_key] = {"totalYears": int(value)}
            else:
                current[final_key] = value
                
        elif field_path in [
            "successCriteria.onboardingMilestones",
            "successCriteria.shortTermKPIs",
            "differentiators.achievementMarkers",
            "dealbreakers.absoluteRequirements",
            "responsibilities.criticalTasks",
        ]:
            if isinstance(value, list):
                current[final_key] = value
            elif isinstance(value, str):
                if field_path == "successCriteria.onboardingMilestones":
                    current[final_key] = [{"milestone": value, "timeframe": "90_days", "measureOfSuccess": ""}]
                elif field_path == "successCriteria.shortTermKPIs":
                    current[final_key] = [{"metric": value, "currentValue": "", "targetValue": ""}]
                elif field_path == "differentiators.achievementMarkers":
                    current[final_key] = [{"achievement": value, "importance": "must_have"}]
                elif field_path == "dealbreakers.absoluteRequirements":
                    current[final_key] = [{"requirement": value, "reason": ""}]
                elif field_path == "responsibilities.criticalTasks":
                    current[final_key] = [{"task": value, "deadline": "90 дней", "successIndicator": ""}]
            else:
                current[final_key] = value
                
        elif field_path in [
            "responsibilities.zones",
            "dealbreakers.redFlags",
            "dealbreakers.nonNegotiables",
            "responsibilities.processOwnership",
            "differentiators.domainKnowledge",
            "successCriteria.longTermGoals",
        ]:
            if isinstance(value, str):
                items = [v.strip() for v in value.replace("\n", ",").split(",") if v.strip()]
                current[final_key] = items if items else [value]
            else:
                current[final_key] = value
        else:
            current[final_key] = value
        
        return updated


enrichment_service = EnrichmentService()
