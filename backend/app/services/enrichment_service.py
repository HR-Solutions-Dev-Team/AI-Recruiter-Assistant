"""
Сервис для обогащения вакансий через LLM.
Генерирует контекстные вопросы по незаполненным полям.
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


# Группы зависимых полей (нельзя спрашивать вместе)
DEPENDENCY_GROUPS = [
    # Сфера деятельности - иерархия
    {"company.activitySphere.sphere", "company.activitySphere.subSphere"},
    # Industry - иерархия
    {"core.industry"},
    # Hiring Context - связанные поля
    {"hiringContext.businessProblem", "hiringContext.expectedImpact"},
    # Success Criteria - последовательность
    {"successCriteria.onboardingMilestones", "successCriteria.shortTermKPIs"},
    # Differentiators - связанные поля
    {"differentiators.industryExpertise", "differentiators.scaleExperience"},
]


def _get_dependency_group(field_path: str) -> set[str] | None:
    """Возвращает группу зависимостей для поля."""
    for group in DEPENDENCY_GROUPS:
        if field_path in group:
            return group
    return None


def _are_fields_independent(field1: str, field2: str) -> bool:
    """Проверяет, что два поля независимы (можно спрашивать вместе)."""
    group1 = _get_dependency_group(field1)
    group2 = _get_dependency_group(field2)

    # Если оба поля в одной группе зависимостей - они зависимы
    if group1 and group2 and group1 == group2:
        return False

    # Проверяем прямую зависимость через depends_on
    for field_info in FIELD_PRIORITIES:
        if field_info["path"] == field1 and field_info.get("depends_on") == field2:
            return False
        if field_info["path"] == field2 and field_info.get("depends_on") == field1:
            return False

    return True


class EnrichmentAnswerResult(BaseModel):
    """Результат обработки ответа."""

    field_path: str
    updated_value: Any
    new_completion_percent: int


def _safe_get(d: dict, *keys: str) -> Any:
    """Безопасно получает вложенное значение из словаря."""
    result = d
    for key in keys:
        if result is None or not isinstance(result, dict):
            return None
        result = result.get(key)
    return result


# ============================================================================
# ПРИОРИТЕТЫ ПОЛЕЙ ДЛЯ EXECUTIVE SEARCH
# ============================================================================
# Переориентировано с массового подбора на headhunting редких специалистов.
# Фокус: бизнес-контекст → KPI → дифференциаторы → отсечки → детали.
# Skills понижены в приоритете (для exec search они вторичны).
# ============================================================================

FIELD_PRIORITIES: list[dict[str, Any]] = [
    # =========================================================================
    # PRIORITY 1: КРИТИЧНО — Бизнес-контекст (без этого не начинаем поиск)
    # =========================================================================
    {
        "path": "hiringContext.businessProblem",
        "priority": 1,
        "description": "Какую бизнес-проблему должен решить этот человек? Конкретно и измеримо.",
        "check": lambda d: bool(_safe_get(d, "hiringContext", "businessProblem")),
        "question_hint": "executive_context",
    },
    {
        "path": "hiringContext.triggerEvent",
        "priority": 1,
        "description": "Что послужило причиной открытия вакансии? (рост, замена, новое направление, кризис)",
        "check": lambda d: bool(_safe_get(d, "hiringContext", "triggerEvent", "type")),
        "question_hint": "executive_context",
    },
    {
        "path": "successCriteria.onboardingMilestones",
        "priority": 1,
        "description": "Конкретные milestones первых 90 дней. Что человек ДОЛЖЕН сделать?",
        "check": lambda d: len(_safe_get(d, "successCriteria", "onboardingMilestones") or []) >= 2,
        "question_hint": "executive_kpi",
    },
    {
        "path": "differentiators.industryExpertise",
        "priority": 1,
        "description": "Какая отраслевая экспертиза критична? Почему именно она важна?",
        "check": lambda d: bool(_safe_get(d, "differentiators", "industryExpertise", "industries")),
        "question_hint": "executive_differentiator",
    },

    # =========================================================================
    # PRIORITY 2: ВЫСОКИЙ — Формирование профиля идеального кандидата
    # =========================================================================
    {
        "path": "dealbreakers.absoluteRequirements",
        "priority": 2,
        "description": "Абсолютные требования без исключений (сертификации, допуски, гражданство)",
        "check": lambda d: bool(_safe_get(d, "dealbreakers", "absoluteRequirements")),
        "question_hint": "executive_dealbreaker",
    },
    {
        "path": "responsibilities.criticalTasks",
        "priority": 2,
        "description": "Критические задачи первых 90 дней с индикаторами успеха",
        "check": lambda d: len(_safe_get(d, "responsibilities", "criticalTasks") or []) >= 2,
        "question_hint": "executive_tasks",
    },
    {
        "path": "differentiators.scaleExperience",
        "priority": 2,
        "description": "С каким масштабом должен был работать? (команда, бюджет, объёмы данных)",
        "check": lambda d: bool(_safe_get(d, "differentiators", "scaleExperience")),
        "question_hint": "executive_scale",
    },
    {
        "path": "successCriteria.shortTermKPIs",
        "priority": 2,
        "description": "Измеримые KPI на 6 месяцев (текущее значение → целевое)",
        "check": lambda d: len(_safe_get(d, "successCriteria", "shortTermKPIs") or []) >= 2,
        "depends_on": "successCriteria.onboardingMilestones",
        "question_hint": "executive_kpi",
    },
    {
        "path": "differentiators.achievementMarkers",
        "priority": 2,
        "description": "Конкретные достижения, которые хотим видеть в опыте кандидата",
        "check": lambda d: len(_safe_get(d, "differentiators", "achievementMarkers") or []) >= 2,
        "question_hint": "executive_differentiator",
    },
    {
        "path": "hiringContext.expectedImpact",
        "priority": 2,
        "description": "Какой конкретный результат ожидается от найма этого человека?",
        "check": lambda d: bool(_safe_get(d, "hiringContext", "expectedImpact")),
        "depends_on": "hiringContext.businessProblem",
        "question_hint": "executive_context",
    },
    {
        "path": "dealbreakers.experienceMinimums",
        "priority": 2,
        "description": "Минимальные пороги опыта (общий, в домене, в руководстве)",
        "check": lambda d: bool(_safe_get(d, "dealbreakers", "experienceMinimums", "totalYears")),
        "question_hint": "executive_dealbreaker",
    },

    # =========================================================================
    # PRIORITY 3: СТАНДАРТНЫЙ — Детализация профиля
    # =========================================================================
    {
        "path": "core.careerLevel.code",
        "priority": 3,
        "description": "Уровень позиции в карьерной иерархии",
        "check": lambda d: bool(_safe_get(d, "core", "careerLevel", "code")),
        "question_hint": "basic_info",
    },
    {
        "path": "dealbreakers.nonNegotiables",
        "priority": 3,
        "description": "Требования, которые не обсуждаются и не компенсируются другими качествами",
        "check": lambda d: bool(_safe_get(d, "dealbreakers", "nonNegotiables")),
        "question_hint": "executive_dealbreaker",
    },
    {
        "path": "requirements.experience.scaleIndicators",
        "priority": 3,
        "description": "Индикаторы масштаба опыта (команда, бюджет, проекты)",
        "check": lambda d: bool(_safe_get(d, "requirements", "experience", "scaleIndicators")),
        "question_hint": "executive_scale",
    },
    {
        "path": "responsibilities.zones",
        "priority": 3,
        "description": "Зоны ответственности (минимум 3 для exec search)",
        "check": lambda d: len(_safe_get(d, "responsibilities", "zones") or []) >= 3,
        "question_hint": "executive_tasks",
    },
    {
        "path": "requirements.skills",
        "priority": 3,  # ПОНИЖЕН с 1 до 3 для executive search
        "description": "Ключевые навыки (для exec search вторичны — следуют из опыта)",
        "check": lambda d: len(_safe_get(d, "requirements", "skills") or []) >= 3,
        "question_hint": "basic_info",
    },
    {
        "path": "differentiators.companyBackground",
        "priority": 3,
        "description": "Предпочтительный бэкграунд по типам компаний (FAANG, стартапы, enterprise)",
        "check": lambda d: bool(_safe_get(d, "differentiators", "companyBackground", "preferred")),
        "question_hint": "executive_differentiator",
    },
    {
        "path": "dealbreakers.redFlags",
        "priority": 3,
        "description": "Что точно НЕ подходит (антипаттерны, warning signs)",
        "check": lambda d: bool(_safe_get(d, "dealbreakers", "redFlags")),
        "question_hint": "executive_dealbreaker",
    },

    # =========================================================================
    # PRIORITY 4: ПОДДЕРЖИВАЮЩИЙ — Дополнительная информация
    # =========================================================================
    {
        "path": "core.industry",
        "priority": 4,
        "description": "Отрасль вакансии",
        "check": lambda d: bool(_safe_get(d, "core", "industry", "name")),
        "question_hint": "basic_info",
    },
    {
        "path": "workConditions.salary",
        "priority": 4,
        "description": "Зарплатная вилка (для exec search часто обсуждается индивидуально)",
        "check": lambda d: bool(_safe_get(d, "workConditions", "salary")),
        "question_hint": "basic_info",
    },
    {
        "path": "workConditions.location",
        "priority": 4,
        "description": "Локация и формат работы",
        "check": lambda d: bool(_safe_get(d, "workConditions", "location")),
        "question_hint": "basic_info",
    },
    {
        "path": "company.activitySphere.sphere",
        "priority": 4,
        "description": "Основная сфера деятельности компании",
        "check": lambda d: bool(_safe_get(d, "company", "activitySphere", "sphere")),
        "question_hint": "basic_info",
    },
    {
        "path": "requirements.experience",
        "priority": 4,
        "description": "Общие требования к опыту работы",
        "check": lambda d: bool(_safe_get(d, "requirements", "experience", "yearsMin")),
        "question_hint": "basic_info",
    },
    {
        "path": "orgStructure.reportsTo",
        "priority": 4,
        "description": "Кому подчиняется позиция",
        "check": lambda d: bool(_safe_get(d, "orgStructure", "reportsTo")),
        "question_hint": "basic_info",
    },
    {
        "path": "core.synonyms",
        "priority": 4,
        "description": "Альтернативные названия позиции",
        "check": lambda d: bool(_safe_get(d, "core", "synonyms")),
        "question_hint": "basic_info",
    },
    {
        "path": "requirements.languages",
        "priority": 4,
        "description": "Требования к языкам",
        "check": lambda d: bool(_safe_get(d, "requirements", "languages")),
        "question_hint": "basic_info",
    },
]


# ============================================================================
# ПРОМПТЫ ДЛЯ EXECUTIVE SEARCH
# ============================================================================
# Адаптированы для глубокого понимания бизнес-контекста и формирования
# "узкого горлышка" для поиска редких специалистов.
# ============================================================================

QUESTION_GENERATION_PROMPT = """HR-эксперт по поиску редких специалистов.

Вакансия: {job_title}
Заполняемое поле: {field_path}
Описание поля: {field_description}

Задай ПРЯМОЙ вопрос для заполнения ЭТОГО КОНКРЕТНОГО поля. Вопрос должен напрямую относиться к полю.

ПРИМЕРЫ ПРАВИЛЬНЫХ ВОПРОСОВ ПО ПОЛЯМ:
- core.careerLevel.code → "Какой уровень позиции: Junior, Middle, Senior, Lead или Director?"
- workConditions.salary → "Какая зарплатная вилка для этой позиции?"
- workConditions.location → "Где будет работать сотрудник и в каком формате?"
- requirements.skills → "Какие ключевые навыки обязательны для этой роли?"
- orgStructure.reportsTo → "Кому будет подчиняться этот сотрудник?"
- hiringContext.businessProblem → "Какую бизнес-проблему должен решить этот человек?"
- responsibilities.zones → "Какие основные зоны ответственности у этой роли?"

СТРОГИЕ ПРАВИЛА:
- Вопрос ПРЯМО относится к полю {field_path}
- Варианты ответов — конкретные значения для этого поля
- 10-15 слов максимум в варианте
- БЕЗ абстрактных вопросов про "развитие" или "видение"
- На русском

JSON: {{"question": "...", "options": [{{"value": "..."}}]}}"""


ANSWER_PROCESSING_PROMPT = """Преобразуй ответ пользователя в структурированные данные для Executive Search вакансии.

Поле: {field_path}
Ответ пользователя: {answer}
Текущие данные вакансии: {vacancy_data}

Верни ТОЛЬКО валидный JSON с обновлённым значением для этого поля.

ПРАВИЛА ПРЕОБРАЗОВАНИЯ:

1. Для простых строковых полей:
   {{"value": "строка"}}

2. Для hiringContext.triggerEvent:
   {{"value": {{"type": "growth|replacement|new_direction|crisis|transformation|m_and_a|restructuring", "description": "детали"}}}}

3. Для successCriteria.onboardingMilestones (массив milestones):
   {{"value": [{{"milestone": "описание", "timeframe": "30_days|60_days|90_days", "measureOfSuccess": "критерий успеха"}}]}}

4. Для successCriteria.shortTermKPIs (массив KPI):
   {{"value": [{{"metric": "название метрики", "currentValue": "текущее", "targetValue": "целевое"}}]}}

5. Для differentiators.industryExpertise:
   {{"value": {{"industries": ["индустрия1", "индустрия2"], "whyMatters": "почему важно"}}}}

6. Для differentiators.scaleExperience:
   {{"value": {{"teamSize": {{"min": число, "description": "пояснение"}}, "dataVolume": "объём", "usersScale": "масштаб"}}}}

7. Для differentiators.achievementMarkers (массив достижений):
   {{"value": [{{"achievement": "описание достижения", "importance": "must_have|strong_plus|nice_to_have"}}]}}

8. Для dealbreakers.absoluteRequirements (массив требований):
   {{"value": [{{"requirement": "требование", "reason": "причина"}}]}}

9. Для dealbreakers.experienceMinimums:
   {{"value": {{"totalYears": число, "domainYears": число, "leadershipYears": число}}}}

10. Для responsibilities.criticalTasks (массив задач):
    {{"value": [{{"task": "описание задачи", "deadline": "30|60|90 дней", "successIndicator": "индикатор успеха"}}]}}

11. Для массивов строк (zones, redFlags, nonNegotiables):
    {{"value": ["элемент1", "элемент2", "элемент3"]}}

12. Для core.careerLevel.code:
    {{"value": "intern|junior|middle|senior|lead|head|director|c-level"}}

Пример для differentiators.industryExpertise:
{{"value": {{"industries": ["FinTech", "Banking"], "whyMatters": "Нужно понимание PCI DSS и работа с транзакционными данными"}}}}

Пример для successCriteria.onboardingMilestones:
{{"value": [{{"milestone": "Провести аудит текущей инфраструктуры", "timeframe": "30_days", "measureOfSuccess": "Документ с findings и roadmap"}}]}}

JSON:"""


class EnrichmentService:
    """Сервис для обогащения вакансий через LLM."""

    def __init__(self) -> None:
        self.api_key = settings.openrouter_api_key
        self.model = settings.openrouter_model
        self.base_url = settings.openrouter_base_url

    def get_available_categories(self) -> dict[str, dict[str, Any]]:
        """
        Возвращает доступные категории вопросов для UI выбора приоритетов.
        
        Returns:
            Словарь категорий с name, description и списком fields
        """
        categories = {
            "executive_context": {
                "name": "Бизнес-контекст",
                "description": "Зачем нужен этот человек и какую проблему он решит",
                "fields": [],
            },
            "executive_kpi": {
                "name": "KPI и результаты",
                "description": "Milestones первых 90 дней и метрики успеха",
                "fields": [],
            },
            "executive_differentiator": {
                "name": "Профиль кандидата",
                "description": "Что отличает идеального кандидата от просто подходящего",
                "fields": [],
            },
            "executive_dealbreaker": {
                "name": "Критические требования",
                "description": "Абсолютные требования и отсечки без исключений",
                "fields": [],
            },
            "executive_tasks": {
                "name": "Задачи и обязанности",
                "description": "Критические задачи и зоны ответственности",
                "fields": [],
            },
            "executive_scale": {
                "name": "Масштаб опыта",
                "description": "Размер команд, бюджеты, объёмы с которыми работал",
                "fields": [],
            },
            "basic_info": {
                "name": "Базовая информация",
                "description": "Зарплата, локация, отрасль, опыт работы",
                "fields": [],
            },
            "standard": {
                "name": "Прочие поля",
                "description": "Дополнительная информация о вакансии",
                "fields": [],
            },
        }
        
        # Группируем поля по категориям
        for field_info in FIELD_PRIORITIES:
            hint = field_info.get("question_hint", "standard")
            if hint in categories:
                categories[hint]["fields"].append(field_info["path"])
            else:
                categories["standard"]["fields"].append(field_info["path"])
        
        # Удаляем пустые категории
        return {k: v for k, v in categories.items() if v["fields"]}

    async def get_next_question(
        self,
        vacancy_data: dict[str, Any],
        asked_fields: list[str] | None = None,
    ) -> EnrichmentQuestion | None:
        """
        Определяет следующее незаполненное поле и генерирует вопрос.

        Args:
            vacancy_data: Текущие данные вакансии
            asked_fields: Поля, по которым уже задавали вопросы (включая пропущенные)

        Returns:
            EnrichmentQuestion или None если все поля заполнены
        """
        asked_fields = asked_fields or []

        # Находим первое незаполненное поле по приоритету
        for field_info in FIELD_PRIORITIES:
            field_path = field_info["path"]

            # Пропускаем уже спрошенные поля
            if field_path in asked_fields:
                continue

            # Проверяем заполненность
            if field_info["check"](vacancy_data):
                continue

            # Проверяем зависимости
            depends_on = field_info.get("depends_on")
            if depends_on:
                # Находим зависимое поле и проверяем его заполненность
                dep_field = next(
                    (f for f in FIELD_PRIORITIES if f["path"] == depends_on), None
                )
                if dep_field and not dep_field["check"](vacancy_data):
                    continue

            # Генерируем вопрос через LLM
            try:
                question = await self._generate_question(
                    vacancy_data=vacancy_data,
                    field_path=field_path,
                    field_description=field_info["description"],
                )
                if question:
                    question.depends_on = depends_on
                    return question
            except Exception as e:
                logger.error(f"Failed to generate question for {field_path}: {e}")
                continue

        return None

    async def get_next_questions(
        self,
        vacancy_data: dict[str, Any],
        asked_fields: list[str] | None = None,
        qa_history: list[dict[str, str]] | None = None,
        priority_categories: list[str] | None = None,
        max_questions: int = 2,
    ) -> list[EnrichmentQuestion]:
        """
        Генерирует до max_questions независимых вопросов за один вызов.

        Вопросы выбираются так, чтобы они не были зависимы друг от друга
        (например, нельзя спрашивать sphere и subSphere одновременно).

        Args:
            vacancy_data: Текущие данные вакансии
            asked_fields: Поля, по которым уже задавали вопросы
            qa_history: История вопросов-ответов для контекста
            priority_categories: Приоритетные категории вопросов
            max_questions: Максимальное количество вопросов (до 2)

        Returns:
            Список независимых вопросов (может быть пустым)
        """
        asked_fields = asked_fields or []
        qa_history = qa_history or []
        priority_categories = priority_categories or []
        questions: list[EnrichmentQuestion] = []
        selected_fields: list[str] = []

        # Собираем кандидатов на вопросы
        candidates: list[dict[str, Any]] = []

        for field_info in FIELD_PRIORITIES:
            field_path = field_info["path"]

            # Пропускаем уже спрошенные поля
            if field_path in asked_fields:
                continue

            # Проверяем заполненность
            if field_info["check"](vacancy_data):
                continue

            # Проверяем зависимости от других полей
            depends_on = field_info.get("depends_on")
            if depends_on:
                dep_field = next(
                    (f for f in FIELD_PRIORITIES if f["path"] == depends_on), None
                )
                if dep_field and not dep_field["check"](vacancy_data):
                    continue

            candidates.append(field_info)

        # Сортируем кандидатов по приоритетным категориям
        # Поля из выбранных категорий идут первыми
        if priority_categories:
            def get_category_priority(field_info: dict[str, Any]) -> int:
                hint = field_info.get("question_hint", "standard")
                if hint in priority_categories:
                    # Возвращаем индекс в списке приоритетов (меньше = выше приоритет)
                    return priority_categories.index(hint)
                # Поля не из приоритетных категорий идут в конец
                return len(priority_categories) + field_info.get("priority", 99)
            
            candidates.sort(key=get_category_priority)

        # Выбираем независимые поля
        for candidate in candidates:
            if len(selected_fields) >= max_questions:
                break

            field_path = candidate["path"]

            # Проверяем независимость от уже выбранных полей
            is_independent = all(
                _are_fields_independent(field_path, selected)
                for selected in selected_fields
            )

            if is_independent:
                selected_fields.append(field_path)

        # Генерируем вопросы параллельно через asyncio
        import asyncio

        async def generate_for_field(field_path: str) -> EnrichmentQuestion | None:
            field_info = next(
                (f for f in FIELD_PRIORITIES if f["path"] == field_path), None
            )
            if not field_info:
                return None
            try:
                question = await self._generate_question(
                    vacancy_data=vacancy_data,
                    field_path=field_path,
                    field_description=field_info["description"],
                )
                if question:
                    question.depends_on = field_info.get("depends_on")
                return question
            except Exception as e:
                logger.error(f"Failed to generate question for {field_path}: {e}")
                return None

        # Запускаем генерацию параллельно
        results = await asyncio.gather(
            *[generate_for_field(fp) for fp in selected_fields],
            return_exceptions=True,
        )

        # Собираем успешные результаты
        for result in results:
            if isinstance(result, EnrichmentQuestion):
                questions.append(result)

        return questions

    async def process_answer(
        self,
        vacancy_data: dict[str, Any],
        field_path: str,
        answer: str,
    ) -> dict[str, Any]:
        """
        Обрабатывает ответ пользователя и обновляет данные вакансии.

        Args:
            vacancy_data: Текущие данные вакансии
            field_path: Путь к полю
            answer: Ответ пользователя

        Returns:
            Обновлённые данные вакансии
        """
        try:
            processed_value = await self._process_answer_with_llm(
                vacancy_data=vacancy_data,
                field_path=field_path,
                answer=answer,
            )

            # Обновляем данные вакансии
            updated_data = self._update_vacancy_data(
                vacancy_data=vacancy_data,
                field_path=field_path,
                value=processed_value,
            )

            return updated_data

        except Exception as e:
            logger.error(f"Failed to process answer for {field_path}: {e}")
            # В случае ошибки пробуем простое присвоение
            return self._update_vacancy_data(
                vacancy_data=vacancy_data,
                field_path=field_path,
                value=answer,
            )

    async def _generate_question(
        self,
        vacancy_data: dict[str, Any],
        field_path: str,
        field_description: str,
    ) -> EnrichmentQuestion | None:
        """Генерирует вопрос через LLM для Executive Search."""
        # Извлекаем job_title для контекста
        job_title = _safe_get(vacancy_data, "core", "jobTitle") or "не указано"

        prompt = QUESTION_GENERATION_PROMPT.format(
            vacancy_data=json.dumps(vacancy_data, ensure_ascii=False, indent=2),
            field_path=field_path,
            field_description=field_description,
            job_title=job_title,
        )

        response = await self._call_llm(prompt)
        if not response:
            return None

        try:
            data = json.loads(response)
            options = [
                EnrichmentOption(
                    value=opt.get("value", ""),
                    description=opt.get("description"),
                )
                for opt in data.get("options", [])
            ]

            return EnrichmentQuestion(
                field_path=field_path,
                question_text=data.get("question", f"Укажите значение для {field_path}"),
                options=options,
                allow_custom=True,
            )
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return None

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
            vacancy_data=json.dumps(vacancy_data, ensure_ascii=False, indent=2),
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
                        "temperature": 0.3,
                        "max_tokens": 1000,
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
        return content

    def _update_vacancy_data(
        self,
        vacancy_data: dict[str, Any],
        field_path: str,
        value: Any,
    ) -> dict[str, Any]:
        """Обновляет данные вакансии по пути к полю. Поддерживает Executive Search поля."""
        import copy

        updated = copy.deepcopy(vacancy_data)
        parts = field_path.split(".")

        # Навигация до родительского объекта
        current = updated
        for part in parts[:-1]:
            if part not in current or current[part] is None:
                current[part] = {}
            current = current[part]

        # Устанавливаем значение
        final_key = parts[-1]

        # Специальная обработка для некоторых полей
        if field_path == "core.careerLevel.code" and isinstance(value, str):
            current[final_key] = value

        elif field_path.endswith(".sphere") or field_path.endswith(".subSphere"):
            if isinstance(value, str):
                current[final_key] = {"name": value}
            else:
                current[final_key] = value

        # Executive Search: triggerEvent
        elif field_path == "hiringContext.triggerEvent":
            if isinstance(value, str):
                current[final_key] = {"type": value, "description": ""}
            else:
                current[final_key] = value

        # Executive Search: industryExpertise
        elif field_path == "differentiators.industryExpertise":
            if isinstance(value, list):
                current[final_key] = {"industries": value, "whyMatters": ""}
            elif isinstance(value, str):
                current[final_key] = {"industries": [value], "whyMatters": ""}
            else:
                current[final_key] = value

        # Executive Search: scaleExperience
        elif field_path == "differentiators.scaleExperience":
            if isinstance(value, str):
                current[final_key] = {"teamSize": {"description": value}}
            else:
                current[final_key] = value

        # Executive Search: experienceMinimums
        elif field_path == "dealbreakers.experienceMinimums":
            if isinstance(value, int):
                current[final_key] = {"totalYears": value}
            elif isinstance(value, str) and value.isdigit():
                current[final_key] = {"totalYears": int(value)}
            else:
                current[final_key] = value

        # Executive Search: массивы объектов (milestones, KPIs, achievements, requirements, tasks)
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
                # Если пришла строка, пробуем преобразовать в массив с одним элементом
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

        # Массивы строк
        elif field_path in [
            "responsibilities.zones",
            "dealbreakers.redFlags",
            "dealbreakers.nonNegotiables",
            "responsibilities.processOwnership",
            "differentiators.domainKnowledge",
            "successCriteria.longTermGoals",
        ]:
            if isinstance(value, str):
                # Разбиваем по запятой или новой строке
                items = [v.strip() for v in value.replace("\n", ",").split(",") if v.strip()]
                current[final_key] = items if items else [value]
            else:
                current[final_key] = value

        else:
            current[final_key] = value

        return updated


enrichment_service = EnrichmentService()
