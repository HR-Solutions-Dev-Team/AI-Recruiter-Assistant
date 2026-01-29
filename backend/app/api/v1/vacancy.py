"""
API эндпоинты для работы с вакансиями.
"""

import logging
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

logger = logging.getLogger(__name__)
from pydantic import BaseModel

from app.api.deps import CurrentUserId, Redis
from app.services.file_parser import FileParserError, file_parser_service
from app.services.session import SessionService, SessionStatus, VacancySession
from app.services.vacancy_parser import vacancy_parser_service
from app.services.enrichment_service import enrichment_service, EnrichmentQuestion, EnrichmentOption

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
