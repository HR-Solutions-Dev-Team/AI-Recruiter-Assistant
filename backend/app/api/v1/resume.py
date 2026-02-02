"""
API endpoints for resume operations.
"""

import logging
from typing import Any

from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status
from pydantic import BaseModel, Field

from app.api.deps import CurrentUserId, DB
from app.repositories.resume_repository import ResumeRepository
from app.services.file_parser import FileParserError, file_parser_service
from app.services.resume_parser import resume_parser_service
from app.tasks.matching_tasks import process_resume_matching

logger = logging.getLogger(__name__)

router = APIRouter()


# ============ Request/Response Models ============


class ResumeUploadResponse(BaseModel):
    """Response after resume upload."""
    id: int
    status: str = "processing"
    message: str = "Resume uploaded and parsing started"
    candidate_name: str | None = Field(None, alias="candidateName")
    desired_position: str | None = Field(None, alias="desiredPosition")
    confidence: float

    class Config:
        populate_by_name = True


class ResumeListItem(BaseModel):
    """Resume item for list view."""
    id: int
    first_name: str | None = Field(None, alias="firstName")
    last_name: str | None = Field(None, alias="lastName")
    desired_position: str | None = Field(None, alias="desiredPosition")
    city: str | None = None
    email: str | None = None
    phone: str | None = None
    total_experience_months: int | None = Field(None, alias="totalExperienceMonths")
    skills_count: int = Field(0, alias="skillsCount")
    status: str
    created_at: str = Field(..., alias="createdAt")

    class Config:
        populate_by_name = True


class ResumeListResponse(BaseModel):
    """Response with list of resumes."""
    items: list[ResumeListItem]
    total: int
    skip: int
    limit: int


class MatchInfo(BaseModel):
    """Match information for display."""
    vacancy_id: int = Field(..., alias="vacancyId")
    vacancy_title: str = Field(..., alias="vacancyTitle")
    match_score: float = Field(..., alias="matchScore")
    interview_questions: list[dict[str, str]] = Field([], alias="interviewQuestions")
    gaps_summary: list[str] = Field([], alias="gapsSummary")
    strengths_summary: list[str] = Field([], alias="strengthsSummary")

    class Config:
        populate_by_name = True


class CandidateForVacancy(BaseModel):
    """Candidate info for vacancy view."""
    resume_id: int = Field(..., alias="resumeId")
    first_name: str | None = Field(None, alias="firstName")
    last_name: str | None = Field(None, alias="lastName")
    desired_position: str | None = Field(None, alias="desiredPosition")
    city: str | None = None
    email: str | None = None
    match_score: float = Field(..., alias="matchScore")
    interview_questions: list[dict[str, str]] = Field([], alias="interviewQuestions")
    gaps_summary: list[str] = Field([], alias="gapsSummary")
    strengths_summary: list[str] = Field([], alias="strengthsSummary")

    class Config:
        populate_by_name = True


class VacancyCandidatesResponse(BaseModel):
    """Response with candidates for a vacancy."""
    vacancy_id: int = Field(..., alias="vacancyId")
    vacancy_title: str = Field(..., alias="vacancyTitle")
    candidates: list[CandidateForVacancy]
    total: int


# ============ Helper Functions ============


def _format_gaps_summary(gaps: dict[str, Any]) -> list[str]:
    """Format gaps analysis into summary strings."""
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
            summary.append(f"Нет опыта: {gap.get('requirement', '')[:50]}")
    
    lang_gaps = gaps.get("language_gaps", [])
    for gap in lang_gaps[:1]:
        if gap.get("is_required"):
            summary.append(f"Не указан язык: {gap.get('language', '')}")
    
    return summary


def _format_strengths_summary(strengths: dict[str, Any]) -> list[str]:
    """Format strengths into summary strings."""
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


# ============ Endpoints ============


@router.post("/upload", response_model=ResumeUploadResponse)
async def upload_resume(
    user_id: CurrentUserId,
    db: DB,
    file: UploadFile = File(...),
) -> ResumeUploadResponse:
    """
    Upload and parse a resume file (PDF, DOCX).
    
    The resume is parsed immediately, saved to database,
    and matching with all vacancies is started in background.
    """
    # Validate file
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided",
        )
    
    file_ext = file.filename.lower().split(".")[-1]
    if file_ext not in ["pdf", "docx", "doc", "txt"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file format. Use PDF, DOCX, or TXT.",
        )

    try:
        # Read and parse file
        content = await file.read()
        text = file_parser_service.parse(content, file.filename)

        # Parse resume text with LLM
        parse_result = await resume_parser_service.parse(text)

        # Save to database
        repo = ResumeRepository(db)
        resume = await repo.create_from_parsed_data(
            parsed_data=parse_result.data.model_dump(by_alias=True),
            source_file_name=file.filename,
            source_file_type=file_ext,
        )

        # Start background matching task
        process_resume_matching.delay(resume.id)

        # Build response
        candidate_name = None
        if resume.first_name or resume.last_name:
            candidate_name = f"{resume.first_name or ''} {resume.last_name or ''}".strip()

        return ResumeUploadResponse(
            id=resume.id,
            status="processing",
            message="Резюме загружено. Выполняется сопоставление с вакансиями...",
            candidate_name=candidate_name,
            desired_position=resume.desired_position,
            confidence=parse_result.confidence,
        )

    except FileParserError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to upload resume: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process resume: {str(e)}",
        )


@router.get("", response_model=ResumeListResponse)
async def get_resumes(
    user_id: CurrentUserId,
    db: DB,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status_filter: str | None = Query(None, alias="status"),
) -> ResumeListResponse:
    """Get list of all resumes."""
    repo = ResumeRepository(db)
    
    resumes = await repo.get_all(skip=skip, limit=limit, status=status_filter)
    total = await repo.count(status=status_filter)
    
    items = []
    for r in resumes:
        items.append(ResumeListItem(
            id=r.id,
            first_name=r.first_name,
            last_name=r.last_name,
            desired_position=r.desired_position,
            city=r.city,
            email=r.contacts.email if r.contacts else None,
            phone=r.contacts.phone if r.contacts else None,
            total_experience_months=r.total_experience_months,
            skills_count=len(r.skills) if r.skills else 0,
            status=r.status,
            created_at=r.created_at.isoformat() if r.created_at else "",
        ))
    
    return ResumeListResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{resume_id}")
async def get_resume(
    resume_id: int,
    user_id: CurrentUserId,
    db: DB,
) -> dict[str, Any]:
    """Get single resume by ID with all details."""
    repo = ResumeRepository(db)
    resume = await repo.get_by_id(resume_id)
    
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found",
        )
    
    # Build response
    result: dict[str, Any] = {
        "id": resume.id,
        "personal": {
            "firstName": resume.first_name,
            "lastName": resume.last_name,
            "middleName": resume.middle_name,
            "birthDate": resume.birth_date.isoformat() if resume.birth_date else None,
            "gender": resume.gender,
        },
        "desiredPosition": {
            "title": resume.desired_position,
            "salaryMin": float(resume.desired_salary_min) if resume.desired_salary_min else None,
            "salaryMax": float(resume.desired_salary_max) if resume.desired_salary_max else None,
            "salaryCurrency": resume.desired_salary_currency,
        },
        "location": {
            "city": resume.city,
            "region": resume.region,
            "country": resume.country,
            "willingToRelocate": resume.willing_to_relocate,
            "willingToTravel": resume.willing_to_travel,
        },
        "employment": {
            "employmentType": resume.employment_type,
            "scheduleType": resume.schedule_type,
            "remotePreference": resume.remote_preference,
        },
        "summary": resume.summary,
        "totalExperienceMonths": resume.total_experience_months,
        "status": resume.status,
        "createdAt": resume.created_at.isoformat() if resume.created_at else None,
    }

    if resume.contacts:
        result["contacts"] = {
            "email": resume.contacts.email,
            "phone": resume.contacts.phone,
            "phoneSecondary": resume.contacts.phone_secondary,
            "telegram": resume.contacts.telegram,
            "whatsapp": resume.contacts.whatsapp,
            "linkedinUrl": resume.contacts.linkedin_url,
            "githubUrl": resume.contacts.github_url,
            "portfolioUrl": resume.contacts.portfolio_url,
        }

    result["experience"] = [
        {
            "companyName": exp.company_name,
            "companyIndustry": exp.company_industry,
            "position": exp.position,
            "department": exp.department,
            "startDate": exp.start_date.isoformat() if exp.start_date else None,
            "endDate": exp.end_date.isoformat() if exp.end_date else None,
            "isCurrent": exp.is_current,
            "durationMonths": exp.duration_months,
            "locationCity": exp.location_city,
            "responsibilities": exp.responsibilities,
            "achievements": exp.achievements,
            "technologies": exp.technologies,
        }
        for exp in (resume.experiences or [])
    ]

    result["education"] = [
        {
            "institutionName": edu.institution_name,
            "institutionType": edu.institution_type,
            "faculty": edu.faculty,
            "specialization": edu.specialization,
            "degree": edu.degree,
            "startYear": edu.start_year,
            "endYear": edu.end_year,
            "isCurrent": edu.is_current,
        }
        for edu in (resume.education or [])
    ]

    result["skills"] = [
        {
            "name": skill.skill_name,
            "category": skill.category,
            "level": skill.level,
            "yearsOfExperience": skill.years_of_experience,
        }
        for skill in (resume.skills or [])
    ]

    result["languages"] = [
        {
            "name": lang.language_name,
            "code": lang.language_code,
            "proficiency": lang.proficiency,
            "isNative": lang.is_native,
        }
        for lang in (resume.languages or [])
    ]

    result["certificates"] = [
        {
            "name": cert.name,
            "issuingOrganization": cert.issuing_organization,
            "issueDate": cert.issue_date.isoformat() if cert.issue_date else None,
            "expiryDate": cert.expiry_date.isoformat() if cert.expiry_date else None,
            "credentialUrl": cert.credential_url,
        }
        for cert in (resume.certificates or [])
    ]

    if resume.full_text:
        result["fullText"] = {
            "sourceFileName": resume.full_text.source_file_name,
            "sourceFileType": resume.full_text.source_file_type,
        }

    return result


@router.get("/{resume_id}/matches", response_model=list[MatchInfo])
async def get_resume_matches(
    resume_id: int,
    user_id: CurrentUserId,
    db: DB,
    min_score: float = Query(0, ge=0, le=100),
) -> list[MatchInfo]:
    """Get all vacancy matches for a resume."""
    repo = ResumeRepository(db)
    
    # Verify resume exists
    resume = await repo.get_by_id(resume_id)
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found",
        )
    
    matches = await repo.get_matches_for_resume(resume_id, min_score=min_score)
    
    result = []
    for match in matches:
        # Get vacancy title
        vacancy, _ = await repo.get_vacancy_with_weights(match.vacancy_id)
        vacancy_title = vacancy.job_title if vacancy else "Unknown"
        
        result.append(MatchInfo(
            vacancy_id=match.vacancy_id,
            vacancy_title=vacancy_title,
            match_score=float(match.match_score),
            interview_questions=match.interview_questions or [],
            gaps_summary=_format_gaps_summary(match.gaps_analysis or {}),
            strengths_summary=_format_strengths_summary(match.strengths or {}),
        ))
    
    return result


@router.delete("/{resume_id}")
async def delete_resume(
    resume_id: int,
    user_id: CurrentUserId,
    db: DB,
) -> dict[str, str]:
    """Delete resume by ID."""
    repo = ResumeRepository(db)
    deleted = await repo.delete(resume_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found",
        )
    
    return {"status": "deleted"}
