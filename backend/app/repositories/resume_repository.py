"""
Repository for resume database operations.
"""

import logging
from datetime import date
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.db_models import (
    Resume,
    ResumeContacts,
    ResumeExperience,
    ResumeEducation,
    ResumeSkill,
    ResumeLanguage,
    ResumeCertificate,
    ResumeFullText,
    ResumeVector,
    ResumeVacancyMatch,
    Vacancy,
    VacancyWeights,
)

logger = logging.getLogger(__name__)


class ResumeRepository:
    """Repository for resume CRUD operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        status: str | None = None,
    ) -> list[Resume]:
        """Get list of resumes with related data."""
        query = (
            select(Resume)
            .options(
                selectinload(Resume.contacts),
                selectinload(Resume.skills),
            )
            .order_by(Resume.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        
        if status:
            query = query.where(Resume.status == status)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_id(self, resume_id: int) -> Resume | None:
        """Get resume by ID with all related data."""
        query = (
            select(Resume)
            .options(
                selectinload(Resume.contacts),
                selectinload(Resume.experiences),
                selectinload(Resume.education),
                selectinload(Resume.skills),
                selectinload(Resume.languages),
                selectinload(Resume.certificates),
                selectinload(Resume.full_text),
                selectinload(Resume.vector),
                selectinload(Resume.vacancy_matches),
            )
            .where(Resume.id == resume_id)
        )
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_from_parsed_data(
        self,
        parsed_data: dict[str, Any],
        source_file_name: str | None = None,
        source_file_type: str | None = None,
    ) -> Resume:
        """
        Create resume from parsed ResumeInput data.
        
        Args:
            parsed_data: Parsed resume data (ResumeInput format)
            source_file_name: Original file name
            source_file_type: File type (pdf, docx)
            
        Returns:
            Created Resume object
        """
        # Extract personal data
        personal = parsed_data.get("personal") or {}
        location = parsed_data.get("location") or {}
        employment = parsed_data.get("employment") or {}
        desired = parsed_data.get("desiredPosition") or parsed_data.get("desired_position") or {}

        # Parse birth date if string
        birth_date = personal.get("birthDate") or personal.get("birth_date")
        if isinstance(birth_date, str):
            try:
                birth_date = date.fromisoformat(birth_date)
            except ValueError:
                birth_date = None

        # Create main resume record
        resume = Resume(
            first_name=personal.get("firstName") or personal.get("first_name"),
            last_name=personal.get("lastName") or personal.get("last_name"),
            middle_name=personal.get("middleName") or personal.get("middle_name"),
            birth_date=birth_date,
            gender=personal.get("gender"),
            photo_url=personal.get("photoUrl") or personal.get("photo_url"),
            
            desired_position=desired.get("title"),
            desired_salary_min=desired.get("salaryMin") or desired.get("salary_min"),
            desired_salary_max=desired.get("salaryMax") or desired.get("salary_max"),
            desired_salary_currency=desired.get("salaryCurrency") or desired.get("salary_currency", "RUB"),
            
            city=location.get("city"),
            region=location.get("region"),
            country=location.get("country", "Россия"),
            willing_to_relocate=location.get("willingToRelocate") or location.get("willing_to_relocate", False),
            willing_to_travel=location.get("willingToTravel") or location.get("willing_to_travel", False),
            travel_time_percent=location.get("travelTimePercent") or location.get("travel_time_percent"),
            
            employment_type=employment.get("employmentType") or employment.get("employment_type"),
            schedule_type=employment.get("scheduleType") or employment.get("schedule_type"),
            remote_preference=employment.get("remotePreference") or employment.get("remote_preference"),
            
            summary=parsed_data.get("summary"),
            total_experience_months=parsed_data.get("totalExperienceMonths") or parsed_data.get("total_experience_months"),
            
            source="file",
            status="active",
        )
        
        self.db.add(resume)
        await self.db.flush()  # Get resume.id

        # Create contacts record
        contacts_data = parsed_data.get("contacts")
        if contacts_data:
            contacts = ResumeContacts(
                resume_id=resume.id,
                email=contacts_data.get("email"),
                phone=contacts_data.get("phone"),
                phone_secondary=contacts_data.get("phoneSecondary") or contacts_data.get("phone_secondary"),
                telegram=contacts_data.get("telegram"),
                whatsapp=contacts_data.get("whatsapp"),
                linkedin_url=contacts_data.get("linkedinUrl") or contacts_data.get("linkedin_url"),
                github_url=contacts_data.get("githubUrl") or contacts_data.get("github_url"),
                portfolio_url=contacts_data.get("portfolioUrl") or contacts_data.get("portfolio_url"),
                other_contacts=contacts_data.get("other"),
            )
            self.db.add(contacts)

        # Create experience records
        experience_data = parsed_data.get("experience", []) or []
        for exp in experience_data:
            start_date = exp.get("startDate") or exp.get("start_date")
            end_date = exp.get("endDate") or exp.get("end_date")
            
            if isinstance(start_date, str):
                try:
                    start_date = date.fromisoformat(start_date)
                except ValueError:
                    start_date = None
            if isinstance(end_date, str):
                try:
                    end_date = date.fromisoformat(end_date)
                except ValueError:
                    end_date = None

            experience = ResumeExperience(
                resume_id=resume.id,
                company_name=exp.get("companyName") or exp.get("company_name", "Unknown"),
                company_industry=exp.get("companyIndustry") or exp.get("company_industry"),
                company_size=exp.get("companySize") or exp.get("company_size"),
                company_url=exp.get("companyUrl") or exp.get("company_url"),
                position=exp.get("position", "Unknown"),
                department=exp.get("department"),
                start_date=start_date,
                end_date=end_date,
                is_current=exp.get("isCurrent") or exp.get("is_current", False),
                duration_months=exp.get("durationMonths") or exp.get("duration_months"),
                location_city=exp.get("locationCity") or exp.get("location_city"),
                location_country=exp.get("locationCountry") or exp.get("location_country"),
                responsibilities=exp.get("responsibilities"),
                achievements=exp.get("achievements"),
                technologies=exp.get("technologies"),
            )
            self.db.add(experience)

        # Create education records
        education_data = parsed_data.get("education", []) or []
        for edu in education_data:
            education = ResumeEducation(
                resume_id=resume.id,
                institution_name=edu.get("institutionName") or edu.get("institution_name", "Unknown"),
                institution_type=edu.get("institutionType") or edu.get("institution_type"),
                faculty=edu.get("faculty"),
                specialization=edu.get("specialization"),
                degree=edu.get("degree"),
                start_year=edu.get("startYear") or edu.get("start_year"),
                end_year=edu.get("endYear") or edu.get("end_year"),
                is_current=edu.get("isCurrent") or edu.get("is_current", False),
                location_city=edu.get("locationCity") or edu.get("location_city"),
                location_country=edu.get("locationCountry") or edu.get("location_country"),
                description=edu.get("description"),
                gpa=edu.get("gpa"),
            )
            self.db.add(education)

        # Create skills records
        skills_data = parsed_data.get("skills", []) or []
        for skill in skills_data:
            resume_skill = ResumeSkill(
                resume_id=resume.id,
                skill_name=skill.get("name", "Unknown"),
                category=skill.get("category", "hard"),
                level=skill.get("level"),
                years_of_experience=skill.get("yearsOfExperience") or skill.get("years_of_experience"),
                last_used_year=skill.get("lastUsedYear") or skill.get("last_used_year"),
            )
            self.db.add(resume_skill)

        # Create languages records
        languages_data = parsed_data.get("languages", []) or []
        for lang in languages_data:
            resume_language = ResumeLanguage(
                resume_id=resume.id,
                language_name=lang.get("name", "Unknown"),
                language_code=lang.get("code"),
                proficiency=lang.get("proficiency"),
                is_native=lang.get("isNative") or lang.get("is_native", False),
            )
            self.db.add(resume_language)

        # Create certificates records
        certificates_data = parsed_data.get("certificates", []) or []
        for cert in certificates_data:
            issue_date = cert.get("issueDate") or cert.get("issue_date")
            expiry_date = cert.get("expiryDate") or cert.get("expiry_date")
            
            if isinstance(issue_date, str):
                try:
                    issue_date = date.fromisoformat(issue_date)
                except ValueError:
                    issue_date = None
            if isinstance(expiry_date, str):
                try:
                    expiry_date = date.fromisoformat(expiry_date)
                except ValueError:
                    expiry_date = None

            certificate = ResumeCertificate(
                resume_id=resume.id,
                name=cert.get("name", "Unknown"),
                issuing_organization=cert.get("issuingOrganization") or cert.get("issuing_organization"),
                issue_date=issue_date,
                expiry_date=expiry_date,
                credential_id=cert.get("credentialId") or cert.get("credential_id"),
                credential_url=cert.get("credentialUrl") or cert.get("credential_url"),
                description=cert.get("description"),
            )
            self.db.add(certificate)

        # Create full text record
        full_text_data = parsed_data.get("fullText") or parsed_data.get("full_text")
        if full_text_data:
            full_text = ResumeFullText(
                resume_id=resume.id,
                full_text=full_text_data.get("text"),
                source_file_name=source_file_name,
                source_file_type=source_file_type,
            )
            self.db.add(full_text)

        await self.db.commit()
        
        # Reload with all relationships
        return await self.get_by_id(resume.id)

    async def save_embedding(
        self,
        resume_id: int,
        embedding: list[float],
        model_name: str = "text-embedding-3-small",
    ) -> None:
        """Save resume embedding vector."""
        # Use raw SQL for pgvector
        await self.db.execute(
            text("""
                INSERT INTO resume_vectors (resume_id, embedding, model_name)
                VALUES (:resume_id, :embedding, :model_name)
                ON CONFLICT (resume_id) 
                DO UPDATE SET embedding = :embedding, model_name = :model_name, updated_at = CURRENT_TIMESTAMP
            """),
            {
                "resume_id": resume_id,
                "embedding": str(embedding),  # pgvector accepts string format
                "model_name": model_name,
            }
        )
        await self.db.commit()

    async def get_embedding(self, resume_id: int) -> list[float] | None:
        """Get resume embedding vector."""
        result = await self.db.execute(
            text("SELECT embedding FROM resume_vectors WHERE resume_id = :resume_id"),
            {"resume_id": resume_id}
        )
        row = result.fetchone()
        if row and row[0]:
            # pgvector returns as string, parse it
            embedding_str = str(row[0])
            if embedding_str.startswith('[') and embedding_str.endswith(']'):
                return [float(x) for x in embedding_str[1:-1].split(',')]
        return None

    async def save_vacancy_embedding(
        self,
        vacancy_id: int,
        embedding: list[float],
        model_name: str = "text-embedding-3-small",
    ) -> None:
        """Save vacancy embedding vector."""
        await self.db.execute(
            text("""
                INSERT INTO vacancy_vectors (vacancy_id, embedding, model_name)
                VALUES (:vacancy_id, :embedding, :model_name)
                ON CONFLICT (vacancy_id) 
                DO UPDATE SET embedding = :embedding, model_name = :model_name, updated_at = CURRENT_TIMESTAMP
            """),
            {
                "vacancy_id": vacancy_id,
                "embedding": str(embedding),
                "model_name": model_name,
            }
        )
        await self.db.commit()

    async def get_vacancy_embedding(self, vacancy_id: int) -> list[float] | None:
        """Get vacancy embedding vector."""
        result = await self.db.execute(
            text("SELECT embedding FROM vacancy_vectors WHERE vacancy_id = :vacancy_id"),
            {"vacancy_id": vacancy_id}
        )
        row = result.fetchone()
        if row and row[0]:
            embedding_str = str(row[0])
            if embedding_str.startswith('[') and embedding_str.endswith(']'):
                return [float(x) for x in embedding_str[1:-1].split(',')]
        return None

    async def save_match(
        self,
        resume_id: int,
        vacancy_id: int,
        match_score: float,
        cosine_similarity: float,
        weighted_scores: dict[str, Any],
        gaps_analysis: dict[str, Any],
        strengths: dict[str, Any],
        interview_questions: list[dict[str, str]],
    ) -> ResumeVacancyMatch:
        """Save or update resume-vacancy match."""
        # Check if match exists
        result = await self.db.execute(
            select(ResumeVacancyMatch).where(
                ResumeVacancyMatch.resume_id == resume_id,
                ResumeVacancyMatch.vacancy_id == vacancy_id,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.match_score = match_score
            existing.cosine_similarity = cosine_similarity
            existing.weighted_scores = weighted_scores
            existing.gaps_analysis = gaps_analysis
            existing.strengths = strengths
            existing.interview_questions = interview_questions
            await self.db.commit()
            return existing
        else:
            match = ResumeVacancyMatch(
                resume_id=resume_id,
                vacancy_id=vacancy_id,
                match_score=match_score,
                cosine_similarity=cosine_similarity,
                weighted_scores=weighted_scores,
                gaps_analysis=gaps_analysis,
                strengths=strengths,
                interview_questions=interview_questions,
            )
            self.db.add(match)
            await self.db.commit()
            return match

    async def get_matches_for_resume(
        self,
        resume_id: int,
        min_score: float = 0,
    ) -> list[ResumeVacancyMatch]:
        """Get all vacancy matches for a resume."""
        query = (
            select(ResumeVacancyMatch)
            .where(ResumeVacancyMatch.resume_id == resume_id)
            .where(ResumeVacancyMatch.match_score >= min_score)
            .order_by(ResumeVacancyMatch.match_score.desc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_matches_for_vacancy(
        self,
        vacancy_id: int,
        min_score: float = 0,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get all resume matches for a vacancy with resume data."""
        query = (
            select(ResumeVacancyMatch, Resume)
            .join(Resume, Resume.id == ResumeVacancyMatch.resume_id)
            .options(selectinload(Resume.contacts))
            .where(ResumeVacancyMatch.vacancy_id == vacancy_id)
            .where(ResumeVacancyMatch.match_score >= min_score)
            .order_by(ResumeVacancyMatch.match_score.desc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        
        matches = []
        for match, resume in result.all():
            matches.append({
                "match": match,
                "resume": resume,
            })
        return matches

    async def get_all_active_vacancies(self) -> list[Vacancy]:
        """Get all active vacancies for matching."""
        query = (
            select(Vacancy)
            .options(selectinload(Vacancy.weights))
            .where(Vacancy.status.in_(["active", "draft", "published"]))
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_vacancy_with_weights(self, vacancy_id: int) -> tuple[Vacancy | None, dict[str, int]]:
        """Get vacancy with its weights."""
        query = (
            select(Vacancy)
            .options(
                selectinload(Vacancy.weights),
                selectinload(Vacancy.company),
                selectinload(Vacancy.requirements),
                selectinload(Vacancy.skills),
                selectinload(Vacancy.languages),
                selectinload(Vacancy.responsibilities),
                selectinload(Vacancy.work_conditions),
            )
            .where(Vacancy.id == vacancy_id)
        )
        result = await self.db.execute(query)
        vacancy = result.scalar_one_or_none()
        
        if not vacancy:
            return None, {}

        # Extract weights
        weights = {}
        if vacancy.weights:
            weights = {
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

        return vacancy, weights

    async def delete(self, resume_id: int) -> bool:
        """Delete resume by ID."""
        resume = await self.get_by_id(resume_id)
        if resume:
            await self.db.delete(resume)
            await self.db.commit()
            return True
        return False

    async def count(self, status: str | None = None) -> int:
        """Count total resumes."""
        from sqlalchemy import func
        
        query = select(func.count(Resume.id))
        if status:
            query = query.where(Resume.status == status)
        
        result = await self.db.execute(query)
        return result.scalar() or 0
