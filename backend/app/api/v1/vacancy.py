"""
API эндпоинты для работы с вакансиями.
"""

import logging
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile, status
from pydantic import BaseModel, Field

from app.api.deps import CurrentUserId, DB, Redis
from app.repositories.vacancy_repository import VacancyRepository
from app.services.enrichment_service import enrichment_service
from app.services.file_parser import FileParserError, file_parser_service
from app.services.session import SessionService, SessionStatus, VacancySession
from app.services.vacancy_parser import vacancy_parser_service
from app.services.weights_service import weights_service

logger = logging.getLogger(__name__)

router = APIRouter()
session_service = SessionService()


# ============ Request/Response Models ============


class CreateSessionResponse(BaseModel):
    """Ответ на создание сессии."""

    session_id: str
    status: str


class UploadTextRequest(BaseModel):
    """Запрос на загрузку текста вакансии."""

    text: str
    hints: dict[str, str] | None = None


class SessionResponse(BaseModel):
    """Ответ с данными сессии."""

    session_id: str
    status: str
    completion_percent: int
    parsed_data: dict[str, Any] | None = None
    confidence: float | None = None
    warnings: list[str] | None = None
    missing_fields: list[str] | None = None


class ParseResponse(BaseModel):
    """Ответ после парсинга."""

    session_id: str
    status: str
    completion_percent: int
    parsed_data: dict[str, Any]
    confidence: float
    warnings: list[str] | None = None
    missing_fields: list[str] | None = None


class EnrichmentOptionResponse(BaseModel):
    """Вариант ответа."""

    value: str
    description: str | None = None


class EnrichmentQuestionResponse(BaseModel):
    """Вопрос для обогащения вакансии."""

    field_path: str
    question_text: str
    options: list[EnrichmentOptionResponse]
    allow_custom: bool = True
    has_more_questions: bool = True


class NextQuestionResponse(BaseModel):
    """Ответ с вопросами или индикатором завершения."""

    questions: list[EnrichmentQuestionResponse] = []
    is_complete: bool = False
    completion_percent: int


class SubmitAnswerRequest(BaseModel):
    """Запрос на отправку ответа."""

    field_path: str
    answer: str
    skip: bool = False


class SubmitAnswerResponse(BaseModel):
    """Ответ после обработки ответа пользователя (включает следующие вопросы)."""

    success: bool
    completion_percent: int
    updated_field: str | None = None
    # Буфер вопросов - до 3 независимых вопросов за раз
    next_questions: list[EnrichmentQuestionResponse] = []
    is_complete: bool = False


class BatchAnswerItem(BaseModel):
    """Один ответ в пачке."""

    field_path: str
    answer: str
    skip: bool = False


class BatchAnswerRequest(BaseModel):
    """Запрос на отправку пачки ответов."""

    answers: list[BatchAnswerItem]


class BatchAnswerResponse(BaseModel):
    """Ответ после обработки пачки ответов."""

    success: bool
    completion_percent: int
    processed_count: int
    # Буфер вопросов - до 3 независимых вопросов за раз
    next_questions: list[EnrichmentQuestionResponse] = []
    is_complete: bool = False


class CalculateWeightsResponse(BaseModel):
    """Ответ с рассчитанными весами критериев (баллы 0-10)."""

    weights: dict[str, int]  # баллы 0-10 для каждой категории


# ============ Helper Functions ============


def session_to_response(session: VacancySession) -> SessionResponse:
    """Конвертирует сессию в response модель."""
    return SessionResponse(
        session_id=session.session_id,
        status=session.status,
        completion_percent=session.get_completion_percent(),
        parsed_data=session.parsed_data,
        confidence=session.confidence,
        warnings=session.warnings,
        missing_fields=session.missing_fields,
    )


# ============ Endpoints ============


@router.post("/session", response_model=CreateSessionResponse)
async def create_session(
    user_id: CurrentUserId,
    redis: Redis,
) -> CreateSessionResponse:
    """
    Создаёт новую сессию для создания вакансии.

    Сессия хранится в Redis и используется для сохранения
    промежуточных данных между шагами.
    """
    session = await session_service.create_session(user_id)

    return CreateSessionResponse(
        session_id=session.session_id,
        status=session.status,
    )


@router.get("/session/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    user_id: CurrentUserId,
    redis: Redis,
) -> SessionResponse:
    """
    Получает текущее состояние сессии.
    """
    session = await session_service.get_session(session_id, user_id)

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    return session_to_response(session)


@router.post("/session/{session_id}/upload-text", response_model=ParseResponse)
async def upload_text(
    session_id: str,
    request: UploadTextRequest,
    user_id: CurrentUserId,
    redis: Redis,
) -> ParseResponse:
    """
    Загружает текст вакансии и парсит его.

    Текст анализируется через LLM (Claude 3.5 Haiku) и
    извлекаются структурированные данные.
    """
    session = await session_service.get_session(session_id, user_id)

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    try:
        # Парсим текст через LLM
        result = await vacancy_parser_service.parse(
            text=request.text,
            hints=request.hints,
        )

        # Обновляем сессию
        session = await session_service.update_session(
            session_id,
            user_id,
            status=SessionStatus.PARSED,
            original_text=request.text,
            parsed_data=result.data.model_dump(by_alias=True),
            confidence=result.confidence,
            warnings=result.warnings,
            missing_fields=result.missing_fields,
        )

        return ParseResponse(
            session_id=session.session_id,
            status=session.status,
            completion_percent=session.get_completion_percent(),
            parsed_data=session.parsed_data,
            confidence=session.confidence,
            warnings=session.warnings,
            missing_fields=session.missing_fields,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse vacancy: {str(e)}",
        )


@router.post("/session/{session_id}/upload-file", response_model=ParseResponse)
async def upload_file(
    session_id: str,
    user_id: CurrentUserId,
    redis: Redis,
    file: UploadFile = File(...),
    hints: str | None = Form(None),
) -> ParseResponse:
    """
    Загружает файл вакансии (TXT, DOCX, PDF) и парсит его.

    Файл конвертируется в текст, затем анализируется через LLM.
    """
    session = await session_service.get_session(session_id, user_id)

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    try:
        # Читаем и парсим файл
        content = await file.read()
        text = file_parser_service.parse(content, file.filename or "unknown.txt")

        # Парсим hints из JSON строки
        hints_dict = None
        if hints:
            import json

            try:
                hints_dict = json.loads(hints)
            except json.JSONDecodeError:
                pass

        # Парсим текст через LLM
        result = await vacancy_parser_service.parse(
            text=text,
            hints=hints_dict,
        )

        # Обновляем сессию
        session = await session_service.update_session(
            session_id,
            user_id,
            status=SessionStatus.PARSED,
            original_text=text,
            parsed_data=result.data.model_dump(by_alias=True),
            confidence=result.confidence,
            warnings=result.warnings,
            missing_fields=result.missing_fields,
        )

        return ParseResponse(
            session_id=session.session_id,
            status=session.status,
            completion_percent=session.get_completion_percent(),
            parsed_data=session.parsed_data,
            confidence=session.confidence,
            warnings=session.warnings,
            missing_fields=session.missing_fields,
        )

    except FileParserError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process file: {str(e)}",
        )


@router.post("/session/{session_id}/enrichment/next-question", response_model=NextQuestionResponse)
async def get_next_questions_endpoint(
    session_id: str,
    user_id: CurrentUserId,
    redis: Redis,
) -> NextQuestionResponse:
    """
    Получает до 3 независимых вопросов для обогащения вакансии.

    Возвращает буфер вопросов для показа по одному без ожидания.
    """
    session = await session_service.get_session(session_id, user_id)

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    if not session.parsed_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session has no parsed data",
        )

    # Получаем список уже спрошенных полей из сессии
    asked_fields = session.parsed_data.get("_asked_fields") or []

    try:
        questions = await enrichment_service.get_next_questions(
            vacancy_data=session.parsed_data,
            asked_fields=asked_fields,
            max_questions=3,
        )

        completion_percent = session.get_completion_percent()

        if not questions:
            return NextQuestionResponse(
                questions=[],
                is_complete=True,
                completion_percent=completion_percent,
            )

        return NextQuestionResponse(
            questions=[
                EnrichmentQuestionResponse(
                    field_path=q.field_path,
                    question_text=q.question_text,
                    options=[
                        EnrichmentOptionResponse(value=opt.value, description=opt.description)
                        for opt in q.options
                    ],
                    allow_custom=q.allow_custom,
                    has_more_questions=True,
                )
                for q in questions
            ],
            is_complete=False,
            completion_percent=completion_percent,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate question: {str(e)}",
        )


@router.post("/session/{session_id}/enrichment/answer", response_model=SubmitAnswerResponse)
async def submit_answer(
    session_id: str,
    request: SubmitAnswerRequest,
    user_id: CurrentUserId,
    redis: Redis,
) -> SubmitAnswerResponse:
    """
    Отправляет ответ на вопрос обогащения.

    Обновляет данные вакансии и сразу возвращает следующий вопрос.
    Это оптимизация для уменьшения количества API-вызовов.
    """
    session = await session_service.get_session(session_id, user_id)

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    if not session.parsed_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session has no parsed data",
        )

    # Добавляем поле в список спрошенных (даже если пропущено)
    asked_fields = session.parsed_data.get("_asked_fields") or []
    if request.field_path not in asked_fields:
        asked_fields.append(request.field_path)

    updated_data = session.parsed_data.copy()
    updated_data["_asked_fields"] = asked_fields

    # Если не пропуск - обрабатываем ответ
    if not request.skip:
        try:
            updated_data = await enrichment_service.process_answer(
                vacancy_data=updated_data,
                field_path=request.field_path,
                answer=request.answer,
            )
            # Сохраняем asked_fields
            updated_data["_asked_fields"] = asked_fields
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process answer: {str(e)}",
            )

    # Обновляем сессию
    session = await session_service.update_session(
        session_id,
        user_id,
        parsed_data=updated_data,
        status=SessionStatus.CLARIFYING,
    )

    completion_percent = session.get_completion_percent()

    # Генерируем до 3 независимых вопросов параллельно (буферизация)
    next_questions_response: list[EnrichmentQuestionResponse] = []
    is_complete = False

    try:
        next_questions = await enrichment_service.get_next_questions(
            vacancy_data=updated_data,
            asked_fields=asked_fields,
            max_questions=3,
        )

        if not next_questions:
            is_complete = True
        else:
            next_questions_response = [
                EnrichmentQuestionResponse(
                    field_path=q.field_path,
                    question_text=q.question_text,
                    options=[
                        EnrichmentOptionResponse(value=opt.value, description=opt.description)
                        for opt in q.options
                    ],
                    allow_custom=q.allow_custom,
                    has_more_questions=True,
                )
                for q in next_questions
            ]
    except Exception as e:
        logger.error(f"Failed to generate next questions: {e}")

    return SubmitAnswerResponse(
        success=True,
        completion_percent=completion_percent,
        updated_field=request.field_path if not request.skip else None,
        next_questions=next_questions_response,
        is_complete=is_complete,
    )


@router.post("/session/{session_id}/enrichment/batch-answer", response_model=BatchAnswerResponse)
async def batch_submit_answers(
    session_id: str,
    request: BatchAnswerRequest,
    user_id: CurrentUserId,
    redis: Redis,
) -> BatchAnswerResponse:
    """
    Отправляет пачку ответов за один запрос.

    Используется для оптимизации - ответы накапливаются локально
    и отправляются когда буфер вопросов опустеет.
    """
    session = await session_service.get_session(session_id, user_id)

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    if not session.parsed_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session has no parsed data",
        )

    # Получаем текущие asked_fields
    asked_fields = session.parsed_data.get("_asked_fields") or []
    updated_data = session.parsed_data.copy()

    processed_count = 0

    # Обрабатываем все ответы последовательно
    for answer_item in request.answers:
        # Добавляем поле в список спрошенных
        if answer_item.field_path not in asked_fields:
            asked_fields.append(answer_item.field_path)

        # Если не пропуск - обрабатываем ответ
        if not answer_item.skip and answer_item.answer:
            try:
                updated_data = await enrichment_service.process_answer(
                    vacancy_data=updated_data,
                    field_path=answer_item.field_path,
                    answer=answer_item.answer,
                )
            except Exception as e:
                logger.error(f"Failed to process answer for {answer_item.field_path}: {e}")
                # Продолжаем с остальными ответами

        processed_count += 1

    # Сохраняем asked_fields
    updated_data["_asked_fields"] = asked_fields

    # Обновляем сессию один раз после всех ответов
    session = await session_service.update_session(
        session_id,
        user_id,
        parsed_data=updated_data,
        status=SessionStatus.CLARIFYING,
    )

    completion_percent = session.get_completion_percent()

    # Генерируем новые вопросы
    next_questions_response: list[EnrichmentQuestionResponse] = []
    is_complete = False

    try:
        next_questions = await enrichment_service.get_next_questions(
            vacancy_data=updated_data,
            asked_fields=asked_fields,
            max_questions=3,
        )

        if not next_questions:
            is_complete = True
        else:
            next_questions_response = [
                EnrichmentQuestionResponse(
                    field_path=q.field_path,
                    question_text=q.question_text,
                    options=[
                        EnrichmentOptionResponse(value=opt.value, description=opt.description)
                        for opt in q.options
                    ],
                    allow_custom=q.allow_custom,
                    has_more_questions=True,
                )
                for q in next_questions
            ]
    except Exception as e:
        logger.error(f"Failed to generate next questions: {e}")

    return BatchAnswerResponse(
        success=True,
        completion_percent=completion_percent,
        processed_count=processed_count,
        next_questions=next_questions_response,
        is_complete=is_complete,
    )


@router.delete("/session/{session_id}")
async def delete_session(
    session_id: str,
    user_id: CurrentUserId,
    redis: Redis,
) -> dict:
    """
    Удаляет сессию.
    """
    deleted = await session_service.delete_session(session_id, user_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    return {"status": "deleted"}


@router.post("/session/{session_id}/calculate-weights", response_model=CalculateWeightsResponse)
async def calculate_criteria_weights(
    session_id: str,
    user_id: CurrentUserId,
    redis: Redis,
) -> CalculateWeightsResponse:
    """
    Рассчитывает веса критериев отбора для вакансии через LLM.

    Анализирует данные вакансии и определяет приоритеты категорий
    на основе типа позиции, уровня, отрасли и других факторов.

    Используется при переходе на страницу редактирования (EditStep)
    после завершения обогащения вакансии (ChatStep).
    """
    session = await session_service.get_session(session_id, user_id)

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    if not session.parsed_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session has no parsed data",
        )

    try:
        result = await weights_service.calculate_weights(
            vacancy_data=session.parsed_data,
        )

        return CalculateWeightsResponse(
            weights=result.weights,
        )

    except Exception as e:
        logger.error(f"Failed to calculate weights: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate weights: {str(e)}",
        )


# ============ Vacancy CRUD Models ============


class VacancyListItem(BaseModel):
    """Vacancy item for list view."""

    id: int
    job_title: str
    company_name: str | None = None
    location_city: str | None = None
    status: str
    salary_min: float | None = None
    salary_max: float | None = None
    salary_currency: str = "RUB"
    created_at: str


class VacancyListResponse(BaseModel):
    """Response with list of vacancies."""

    items: list[VacancyListItem]
    total: int
    skip: int
    limit: int


class SaveVacancyRequest(BaseModel):
    """Request to save vacancy from session."""

    session_id: str = Field(..., description="Session ID with parsed vacancy data")
    weights: dict[str, int] | None = Field(None, description="Criteria weights (0-10)")


class SaveVacancyResponse(BaseModel):
    """Response after saving vacancy."""

    id: int
    job_title: str
    status: str
    message: str = "Vacancy saved successfully"


# ============ Vacancy CRUD Endpoints ============


@router.get("", response_model=VacancyListResponse)
async def get_vacancies(
    user_id: CurrentUserId,
    db: DB,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Max records to return"),
    status_filter: str | None = Query(None, alias="status", description="Filter by status"),
) -> VacancyListResponse:
    """
    Get list of vacancies.
    
    Returns paginated list with basic info for list view.
    """
    repo = VacancyRepository(db)
    
    vacancies = await repo.get_all(skip=skip, limit=limit, status=status_filter)
    total = await repo.count(status=status_filter)
    
    items = []
    for v in vacancies:
        items.append(VacancyListItem(
            id=v.id,
            job_title=v.job_title,
            company_name=v.company.name if v.company else None,
            location_city=v.work_conditions.location_city if v.work_conditions else None,
            status=v.status,
            salary_min=float(v.work_conditions.salary_min) if v.work_conditions and v.work_conditions.salary_min else None,
            salary_max=float(v.work_conditions.salary_max) if v.work_conditions and v.work_conditions.salary_max else None,
            salary_currency=v.work_conditions.salary_currency if v.work_conditions else "RUB",
            created_at=v.created_at.isoformat() if v.created_at else "",
        ))
    
    return VacancyListResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.post("", response_model=SaveVacancyResponse)
async def save_vacancy(
    request: SaveVacancyRequest,
    user_id: CurrentUserId,
    db: DB,
    redis: Redis,
) -> SaveVacancyResponse:
    """
    Save vacancy from session to database.
    
    Takes session_id, retrieves parsed data from Redis,
    and persists to PostgreSQL.
    """
    # Get session data
    session = await session_service.get_session(request.session_id, user_id)
    
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )
    
    if not session.parsed_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session has no parsed data",
        )
    
    try:
        repo = VacancyRepository(db)
        
        # Create vacancy from parsed data
        vacancy = await repo.create_from_parsed_data(
            parsed_data=session.parsed_data,
            weights=request.weights,
            recruiter_id=None,  # TODO: link to recruiter when auth is fully implemented
        )
        
        # Delete session after successful save
        await session_service.delete_session(request.session_id, user_id)
        
        return SaveVacancyResponse(
            id=vacancy.id,
            job_title=vacancy.job_title,
            status=vacancy.status,
        )
    
    except Exception as e:
        logger.error(f"Failed to save vacancy: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save vacancy: {str(e)}",
        )


@router.get("/{vacancy_id}")
async def get_vacancy(
    vacancy_id: int,
    user_id: CurrentUserId,
    db: DB,
) -> dict[str, Any]:
    """
    Get single vacancy by ID with all details.
    """
    repo = VacancyRepository(db)
    vacancy = await repo.get_by_id(vacancy_id)
    
    if vacancy is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vacancy not found",
        )
    
    # Build response with all data
    result: dict[str, Any] = {
        "id": vacancy.id,
        "core": {
            "jobTitle": vacancy.job_title,
            "synonyms": vacancy.synonyms,
            "careerLevel": {
                "code": vacancy.career_level_code,
                "experienceYearsMin": vacancy.experience_years_min,
                "experienceYearsMax": vacancy.experience_years_max,
            } if vacancy.career_level_code else None,
        },
        "status": vacancy.status,
        "priority": vacancy.priority,
        "tags": vacancy.tags,
        "createdAt": vacancy.created_at.isoformat() if vacancy.created_at else None,
    }
    
    if vacancy.company:
        result["company"] = {
            "name": vacancy.company.name,
            "type": vacancy.company.type,
            "size": vacancy.company.size,
            "activitySphere": vacancy.company.activity_sphere,
            "publicLinks": vacancy.company.public_links,
        }
    
    if vacancy.work_conditions:
        wc = vacancy.work_conditions
        result["workConditions"] = {
            "employmentType": {"name": wc.employment_type} if wc.employment_type else None,
            "schedule": {"name": wc.schedule_type} if wc.schedule_type else None,
            "workHours": wc.work_hours,
            "salary": {
                "amountMin": float(wc.salary_min) if wc.salary_min else None,
                "amountMax": float(wc.salary_max) if wc.salary_max else None,
                "currency": wc.salary_currency,
                "period": wc.salary_period,
                "comment": wc.salary_comment,
            },
            "location": {
                "city": wc.location_city,
                "region": wc.location_region,
                "country": wc.location_country,
                "remote": wc.remote_type,
                "relocationSupport": wc.relocation_support,
                "visaSupport": wc.visa_support,
            },
        }
    
    if vacancy.requirements:
        result["requirements"] = {
            "education": vacancy.requirements.education,
            "experience": vacancy.requirements.experience,
        }
    
    if vacancy.skills:
        result["requirements"] = result.get("requirements", {})
        result["requirements"]["skills"] = [
            {
                "name": s.skill_name,
                "category": s.category,
                "isRequired": s.is_required,
                "level": s.level,
                "comment": s.comment,
            }
            for s in vacancy.skills
        ]
    
    if vacancy.languages:
        result["requirements"] = result.get("requirements", {})
        result["requirements"]["languages"] = [
            {
                "name": lang.language_name,
                "code": lang.language_code,
                "proficiency": lang.proficiency,
                "isRequired": lang.is_required,
            }
            for lang in vacancy.languages
        ]
    
    if vacancy.responsibilities:
        result["responsibilities"] = {
            "scope": vacancy.responsibilities.scope,
            "zones": vacancy.responsibilities.zones,
            "criticalTasks": vacancy.responsibilities.critical_tasks,
            "processOwnership": vacancy.responsibilities.process_ownership,
            "decisionAuthority": vacancy.responsibilities.decision_authority,
            "businessProcesses": vacancy.responsibilities.business_processes,
        }
    
    if vacancy.org_structure:
        result["orgStructure"] = {
            "reportsTo": vacancy.org_structure.reports_to,
            "subordinatesCount": vacancy.org_structure.subordinates_count,
            "orgUnit": vacancy.org_structure.org_unit,
            "teamRoles": vacancy.org_structure.team_roles,
            "crossFunctionalLinks": vacancy.org_structure.cross_functional_links,
        }
    
    if vacancy.executive_search:
        result["hiringContext"] = vacancy.executive_search.hiring_context
        result["successCriteria"] = vacancy.executive_search.success_criteria
        result["differentiators"] = vacancy.executive_search.differentiators
        result["dealbreakers"] = vacancy.executive_search.dealbreakers
        result["searchDifficulty"] = vacancy.executive_search.search_difficulty
    
    if vacancy.full_text:
        result["fullText"] = {
            "text": vacancy.full_text.full_text,
            "source": vacancy.full_text.source,
        }
    
    if vacancy.weights:
        result["weights"] = {
            "core": vacancy.weights.weight_core,
            "company": vacancy.weights.weight_company,
            "workConditions": vacancy.weights.weight_work_conditions,
            "requirements": vacancy.weights.weight_requirements,
            "responsibilities": vacancy.weights.weight_responsibilities,
            "hiringContext": vacancy.weights.weight_hiring_context,
            "successCriteria": vacancy.weights.weight_success_criteria,
            "differentiators": vacancy.weights.weight_differentiators,
            "dealbreakers": vacancy.weights.weight_dealbreakers,
        }
    
    return result


@router.delete("/{vacancy_id}")
async def delete_vacancy(
    vacancy_id: int,
    user_id: CurrentUserId,
    db: DB,
) -> dict[str, str]:
    """
    Delete vacancy by ID.
    """
    repo = VacancyRepository(db)
    deleted = await repo.delete(vacancy_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vacancy not found",
        )
    
    return {"status": "deleted"}


# ============ Candidates for Vacancy ============


class CandidateMatch(BaseModel):
    """Candidate match info for vacancy view."""
    
    resume_id: int = Field(..., alias="resumeId")
    first_name: str | None = Field(None, alias="firstName")
    last_name: str | None = Field(None, alias="lastName")
    desired_position: str | None = Field(None, alias="desiredPosition")
    city: str | None = None
    email: str | None = None
    phone: str | None = None
    match_score: float = Field(..., alias="matchScore")
    interview_questions: list[dict[str, str]] = Field(default_factory=list, alias="interviewQuestions")
    gaps_summary: list[str] = Field(default_factory=list, alias="gapsSummary")
    strengths_summary: list[str] = Field(default_factory=list, alias="strengthsSummary")

    model_config = {"populate_by_name": True}


class VacancyCandidatesResponse(BaseModel):
    """Response with candidates for a vacancy."""
    
    vacancy_id: int = Field(..., alias="vacancyId")
    vacancy_title: str = Field(..., alias="vacancyTitle")
    candidates: list[CandidateMatch]
    total: int

    model_config = {"populate_by_name": True}


def _format_gaps_summary(gaps: dict[str, Any] | None) -> list[str]:
    """Format gaps analysis into summary strings."""
    if not gaps:
        return []
    
    summary = []
    
    missing_skills = gaps.get("missing_skills", [])
    required_missing = [s["skill"] for s in missing_skills if s.get("required")][:3]
    if required_missing:
        summary.append(f"Отсутствуют навыки: {', '.join(required_missing)}")
    
    exp_gaps = gaps.get("experience_gaps", [])
    for gap in exp_gaps[:2]:
        if gap.get("type") == "insufficient_years":
            summary.append(f"Недостаточно опыта: {gap.get('actual', 0)} из {gap.get('required', 0)} лет")
        elif gap.get("type") == "missing_must_have":
            req = gap.get('requirement', '')
            summary.append(f"Нет опыта: {req[:50]}...")
    
    return summary


def _format_strengths_summary(strengths: dict[str, Any] | None) -> list[str]:
    """Format strengths into summary strings."""
    if not strengths:
        return []
    
    summary = []
    
    matching = strengths.get("matching_skills", [])
    if matching:
        skill_names = [s["skill"] for s in matching[:5]]
        summary.append(f"Совпадающие навыки: {', '.join(skill_names)}")
    
    relevant_exp = strengths.get("relevant_experience", [])
    if relevant_exp:
        positions = [e["position"] for e in relevant_exp[:2]]
        summary.append(f"Релевантный опыт: {', '.join(positions)}")
    
    return summary


@router.get("/{vacancy_id}/candidates", response_model=VacancyCandidatesResponse)
async def get_vacancy_candidates(
    vacancy_id: int,
    user_id: CurrentUserId,
    db: DB,
    min_score: float = Query(0, ge=0, le=100, description="Minimum match score"),
    limit: int = Query(50, ge=1, le=100, description="Max candidates to return"),
) -> VacancyCandidatesResponse:
    """
    Get matched candidates for a vacancy.
    
    Returns list of resumes matched with this vacancy,
    sorted by match score descending.
    Includes interview questions and gap analysis for each candidate.
    """
    from app.repositories.resume_repository import ResumeRepository
    
    resume_repo = ResumeRepository(db)
    vacancy_repo = VacancyRepository(db)
    
    # Get vacancy
    vacancy = await vacancy_repo.get_by_id(vacancy_id)
    if not vacancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vacancy not found",
        )
    
    # Get matches
    matches = await resume_repo.get_matches_for_vacancy(
        vacancy_id=vacancy_id,
        min_score=min_score,
        limit=limit,
    )
    
    candidates = []
    for item in matches:
        match = item["match"]
        resume = item["resume"]
        
        # Get contact info
        email = None
        phone = None
        if resume.contacts:
            email = resume.contacts.email
            phone = resume.contacts.phone
        
        candidates.append(CandidateMatch(
            resume_id=resume.id,
            first_name=resume.first_name,
            last_name=resume.last_name,
            desired_position=resume.desired_position,
            city=resume.city,
            email=email,
            phone=phone,
            match_score=float(match.match_score),
            interview_questions=match.interview_questions or [],
            gaps_summary=_format_gaps_summary(match.gaps_analysis),
            strengths_summary=_format_strengths_summary(match.strengths),
        ))
    
    return VacancyCandidatesResponse(
        vacancy_id=vacancy_id,
        vacancy_title=vacancy.job_title,
        candidates=candidates,
        total=len(candidates),
    )
