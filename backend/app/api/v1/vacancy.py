"""
API эндпоинты для работы с вакансиями.
"""

from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel

from app.api.deps import CurrentUserId, Redis
from app.services.file_parser import FileParserError, file_parser_service
from app.services.session import SessionService, SessionStatus, VacancySession
from app.services.vacancy_parser import vacancy_parser_service

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
