"""
Celery tasks for resume-vacancy matching.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.celery_app import celery_app
from app.core.config import settings
from app.repositories.resume_repository import ResumeRepository
from app.services.embedding_service import embedding_service
from app.services.matching_service import matching_service

logger = logging.getLogger(__name__)


@asynccontextmanager
async def get_task_db_session():
    """Create a new database session for Celery task with its own engine."""
    # Create fresh engine for this event loop
    engine = create_async_engine(
        settings.database_url,
        echo=False,
        pool_pre_ping=True,
        pool_size=2,
        max_overflow=3,
    )
    session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    
    async with session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
    
    await engine.dispose()


def run_async(coro):
    """Run async coroutine in sync context."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def _process_resume_matching_async(resume_id: int) -> dict[str, Any]:
    """
    Async implementation of resume matching.
    
    1. Get resume data and create embedding if not exists
    2. Get all active vacancies
    3. For each vacancy:
       - Create vacancy embedding if not exists
       - Calculate weighted match score
       - Analyze gaps
       - Generate interview questions
       - Save match result
    """
    results = {
        "resume_id": resume_id,
        "processed_vacancies": 0,
        "matches": [],
        "errors": [],
    }

    async with get_task_db_session() as db:
        repo = ResumeRepository(db)
        
        # Get resume
        resume = await repo.get_by_id(resume_id)
        if not resume:
            results["errors"].append(f"Resume {resume_id} not found")
            return results

        # Convert resume to dict for embedding/matching
        resume_data = _resume_to_dict(resume)
        
        # Get or create resume embedding
        resume_embedding = await repo.get_embedding(resume_id)
        if not resume_embedding:
            logger.info(f"Creating embedding for resume {resume_id}")
            try:
                resume_embedding = await embedding_service.create_resume_embedding(resume_data)
                await repo.save_embedding(resume_id, resume_embedding)
            except Exception as e:
                results["errors"].append(f"Failed to create resume embedding: {e}")
                return results

        # Get all active vacancies
        vacancies = await repo.get_all_active_vacancies()
        logger.info(f"Processing {len(vacancies)} vacancies for resume {resume_id}")

        for vacancy in vacancies:
            try:
                # Get vacancy with weights
                vacancy_full, weights = await repo.get_vacancy_with_weights(vacancy.id)
                if not vacancy_full:
                    continue

                vacancy_data = _vacancy_to_dict(vacancy_full)

                # Get or create vacancy embedding
                vacancy_embedding = await repo.get_vacancy_embedding(vacancy.id)
                if not vacancy_embedding:
                    logger.info(f"Creating embedding for vacancy {vacancy.id}")
                    vacancy_embedding = await embedding_service.create_vacancy_embedding(vacancy_data)
                    await repo.save_vacancy_embedding(vacancy.id, vacancy_embedding)

                # Calculate match score with weights
                match_score, cosine_sim, weighted_scores = matching_service.calculate_match_score(
                    resume_embedding,
                    vacancy_embedding,
                    weights,
                )

                # Analyze gaps
                gaps = await matching_service.analyze_gaps(resume_data, vacancy_data)

                # Identify strengths
                strengths = await matching_service.identify_strengths(resume_data, vacancy_data)

                # Generate interview questions (only if score is reasonable)
                interview_questions = []
                if match_score >= 30:  # Only generate questions for potential matches
                    interview_questions = await matching_service.generate_interview_questions(
                        resume_data, vacancy_data, gaps
                    )

                # Save match
                await repo.save_match(
                    resume_id=resume_id,
                    vacancy_id=vacancy.id,
                    match_score=match_score,
                    cosine_similarity=cosine_sim,
                    weighted_scores=weighted_scores,
                    gaps_analysis=gaps,
                    strengths=strengths,
                    interview_questions=interview_questions,
                )

                results["processed_vacancies"] += 1
                results["matches"].append({
                    "vacancy_id": vacancy.id,
                    "vacancy_title": vacancy.job_title,
                    "match_score": match_score,
                })

                logger.info(f"Resume {resume_id} <-> Vacancy {vacancy.id}: {match_score}%")

            except Exception as e:
                logger.error(f"Error processing vacancy {vacancy.id}: {e}")
                results["errors"].append(f"Vacancy {vacancy.id}: {str(e)}")

    return results


def _resume_to_dict(resume) -> dict[str, Any]:
    """Convert Resume ORM object to dict for processing."""
    data = {
        "personal": {
            "firstName": resume.first_name,
            "lastName": resume.last_name,
            "middleName": resume.middle_name,
            "birthDate": resume.birth_date.isoformat() if resume.birth_date else None,
            "gender": resume.gender,
        },
        "contacts": {},
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
        "fullText": {
            "text": resume.full_text.full_text if resume.full_text else None,
        },
        "experience": [],
        "education": [],
        "skills": [],
        "languages": [],
        "certificates": [],
    }

    if resume.contacts:
        data["contacts"] = {
            "email": resume.contacts.email,
            "phone": resume.contacts.phone,
            "telegram": resume.contacts.telegram,
            "linkedinUrl": resume.contacts.linkedin_url,
            "githubUrl": resume.contacts.github_url,
        }

    for exp in resume.experiences or []:
        data["experience"].append({
            "companyName": exp.company_name,
            "companyIndustry": exp.company_industry,
            "position": exp.position,
            "startDate": exp.start_date.isoformat() if exp.start_date else None,
            "endDate": exp.end_date.isoformat() if exp.end_date else None,
            "isCurrent": exp.is_current,
            "durationMonths": exp.duration_months,
            "responsibilities": exp.responsibilities,
            "achievements": exp.achievements,
            "technologies": exp.technologies,
        })

    for edu in resume.education or []:
        data["education"].append({
            "institutionName": edu.institution_name,
            "faculty": edu.faculty,
            "specialization": edu.specialization,
            "degree": edu.degree,
            "startYear": edu.start_year,
            "endYear": edu.end_year,
        })

    for skill in resume.skills or []:
        data["skills"].append({
            "name": skill.skill_name,
            "category": skill.category,
            "level": skill.level,
            "yearsOfExperience": skill.years_of_experience,
        })

    for lang in resume.languages or []:
        data["languages"].append({
            "name": lang.language_name,
            "code": lang.language_code,
            "proficiency": lang.proficiency,
            "isNative": lang.is_native,
        })

    return data


def _vacancy_to_dict(vacancy) -> dict[str, Any]:
    """Convert Vacancy ORM object to dict for processing."""
    data = {
        "core": {
            "jobTitle": vacancy.job_title,
            "synonyms": vacancy.synonyms,
            "careerLevel": {
                "code": vacancy.career_level_code,
                "experienceYearsMin": vacancy.experience_years_min,
                "experienceYearsMax": vacancy.experience_years_max,
            } if vacancy.career_level_code else None,
        },
        "company": {},
        "requirements": {
            "skills": [],
            "languages": [],
            "experience": {},
        },
        "responsibilities": {},
        "workConditions": {},
    }

    if vacancy.company:
        data["company"] = {
            "name": vacancy.company.name,
            "type": vacancy.company.type,
            "size": vacancy.company.size,
            "activitySphere": vacancy.company.activity_sphere,
        }

    if vacancy.requirements:
        data["requirements"]["experience"] = vacancy.requirements.experience or {}
        data["requirements"]["education"] = vacancy.requirements.education or {}

    for skill in vacancy.skills or []:
        data["requirements"]["skills"].append({
            "name": skill.skill_name,
            "category": skill.category,
            "isRequired": skill.is_required,
            "level": skill.level,
        })

    for lang in vacancy.languages or []:
        data["requirements"]["languages"].append({
            "name": lang.language_name,
            "code": lang.language_code,
            "proficiency": lang.proficiency,
            "isRequired": lang.is_required,
        })

    if vacancy.responsibilities:
        data["responsibilities"] = {
            "scope": vacancy.responsibilities.scope,
            "zones": vacancy.responsibilities.zones,
        }

    if vacancy.work_conditions:
        data["workConditions"] = {
            "location": {
                "city": vacancy.work_conditions.location_city,
                "region": vacancy.work_conditions.location_region,
                "country": vacancy.work_conditions.location_country,
                "remote": vacancy.work_conditions.remote_type,
            },
            "employmentType": {"name": vacancy.work_conditions.employment_type},
            "schedule": {"name": vacancy.work_conditions.schedule_type},
        }

    return data


@celery_app.task(bind=True, name="app.tasks.matching_tasks.process_resume_matching")
def process_resume_matching(self, resume_id: int) -> dict[str, Any]:
    """
    Celery task: Process resume matching with all vacancies.
    
    This task:
    1. Creates resume embedding if not exists
    2. Matches against all active vacancies
    3. Calculates weighted scores
    4. Generates interview questions
    5. Saves results to database
    
    Args:
        resume_id: Resume ID to process
        
    Returns:
        Dict with processing results
    """
    logger.info(f"Starting matching task for resume {resume_id}")
    
    try:
        result = run_async(_process_resume_matching_async(resume_id))
        logger.info(f"Completed matching for resume {resume_id}: {result['processed_vacancies']} vacancies processed")
        return result
    except Exception as e:
        logger.error(f"Matching task failed for resume {resume_id}: {e}")
        raise


@celery_app.task(bind=True, name="app.tasks.matching_tasks.process_vacancy_matching")
def process_vacancy_matching(self, vacancy_id: int) -> dict[str, Any]:
    """
    Celery task: Process vacancy matching with all resumes.
    
    Useful when a new vacancy is created and you want to find matching candidates.
    
    Args:
        vacancy_id: Vacancy ID to process
        
    Returns:
        Dict with processing results
    """
    logger.info(f"Starting matching task for vacancy {vacancy_id}")
    
    async def _process():
        results = {
            "vacancy_id": vacancy_id,
            "processed_resumes": 0,
            "matches": [],
            "errors": [],
        }

        async with get_task_db_session() as db:
            repo = ResumeRepository(db)
            
            # Get vacancy with weights
            vacancy, weights = await repo.get_vacancy_with_weights(vacancy_id)
            if not vacancy:
                results["errors"].append(f"Vacancy {vacancy_id} not found")
                return results

            vacancy_data = _vacancy_to_dict(vacancy)

            # Get or create vacancy embedding
            vacancy_embedding = await repo.get_vacancy_embedding(vacancy_id)
            if not vacancy_embedding:
                vacancy_embedding = await embedding_service.create_vacancy_embedding(vacancy_data)
                await repo.save_vacancy_embedding(vacancy_id, vacancy_embedding)

            # Get all active resumes
            resumes = await repo.get_all(status="active")
            logger.info(f"Processing {len(resumes)} resumes for vacancy {vacancy_id}")

            for resume in resumes:
                try:
                    resume_data = _resume_to_dict(resume)

                    # Get or create resume embedding
                    resume_embedding = await repo.get_embedding(resume.id)
                    if not resume_embedding:
                        resume_embedding = await embedding_service.create_resume_embedding(resume_data)
                        await repo.save_embedding(resume.id, resume_embedding)

                    # Calculate match score
                    match_score, cosine_sim, weighted_scores = matching_service.calculate_match_score(
                        resume_embedding, vacancy_embedding, weights
                    )

                    # Analyze gaps
                    gaps = await matching_service.analyze_gaps(resume_data, vacancy_data)
                    strengths = await matching_service.identify_strengths(resume_data, vacancy_data)

                    # Generate questions
                    interview_questions = []
                    if match_score >= 30:
                        interview_questions = await matching_service.generate_interview_questions(
                            resume_data, vacancy_data, gaps
                        )

                    # Save match
                    await repo.save_match(
                        resume_id=resume.id,
                        vacancy_id=vacancy_id,
                        match_score=match_score,
                        cosine_similarity=cosine_sim,
                        weighted_scores=weighted_scores,
                        gaps_analysis=gaps,
                        strengths=strengths,
                        interview_questions=interview_questions,
                    )

                    results["processed_resumes"] += 1
                    results["matches"].append({
                        "resume_id": resume.id,
                        "match_score": match_score,
                    })

                except Exception as e:
                    logger.error(f"Error processing resume {resume.id}: {e}")
                    results["errors"].append(f"Resume {resume.id}: {str(e)}")

        return results

    try:
        result = run_async(_process())
        logger.info(f"Completed matching for vacancy {vacancy_id}: {result['processed_resumes']} resumes processed")
        return result
    except Exception as e:
        logger.error(f"Matching task failed for vacancy {vacancy_id}: {e}")
        raise
