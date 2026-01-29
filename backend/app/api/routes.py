from fastapi import APIRouter, HTTPException

from app.models.vacancy import ParseVacancyRequest, ParseVacancyResponse
from app.services.vacancy_parser import vacancy_parser_service

router = APIRouter()


@router.get("/health")
def healthcheck() -> dict:
    return {"status": "ok"}


@router.post("/vacancy/parse", response_model=ParseVacancyResponse)
async def parse_vacancy(request: ParseVacancyRequest) -> ParseVacancyResponse:
    """
    Парсит текст вакансии и извлекает структурированные данные.

    Использует LLM (OpenRouter API) для анализа текста и заполнения
    схемы VacancyInput. Предназначен для первого шага создания вакансии —
    загрузки исходного текста.

    Args:
        request: Текст вакансии и опциональные подсказки

    Returns:
        Структурированные данные вакансии с оценкой уверенности
    """
    try:
        result = await vacancy_parser_service.parse(
            text=request.text,
            hints=request.hints,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse vacancy: {str(e)}",
        )
