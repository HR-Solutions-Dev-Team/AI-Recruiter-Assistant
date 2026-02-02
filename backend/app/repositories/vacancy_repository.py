"""
Repository for vacancy database operations.
"""

import logging
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.db_models import (
    Vacancy,
    VacancyCompany,
    VacancyClassification,
    VacancyWorkConditions,
    VacancyRequirements,
    VacancyResponsibilities,
    VacancyOrgStructure,
    VacancyExecutiveSearch,
    VacancyFullText,
    VacancyWeights,
    VacancySkill,
    VacancyLanguage,
)

logger = logging.getLogger(__name__)


class VacancyRepository:
    """Repository for vacancy CRUD operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        status: str | None = None,
    ) -> list[Vacancy]:
        """
        Get list of vacancies with related data.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            status: Filter by status (optional)
        
        Returns:
            List of Vacancy objects with loaded relationships
        """
        query = (
            select(Vacancy)
            .options(
                selectinload(Vacancy.company),
                selectinload(Vacancy.work_conditions),
            )
            .order_by(Vacancy.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        
        if status:
            query = query.where(Vacancy.status == status)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_id(self, vacancy_id: int) -> Vacancy | None:
        """
        Get vacancy by ID with all related data.
        
        Args:
            vacancy_id: Vacancy ID
            
        Returns:
            Vacancy object with all relationships loaded, or None
        """
        query = (
            select(Vacancy)
            .options(
                selectinload(Vacancy.company),
                selectinload(Vacancy.classification),
                selectinload(Vacancy.work_conditions),
                selectinload(Vacancy.requirements),
                selectinload(Vacancy.responsibilities),
                selectinload(Vacancy.org_structure),
                selectinload(Vacancy.executive_search),
                selectinload(Vacancy.full_text),
                selectinload(Vacancy.weights),
                selectinload(Vacancy.skills),
                selectinload(Vacancy.languages),
            )
            .where(Vacancy.id == vacancy_id)
        )
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_from_parsed_data(
        self,
        parsed_data: dict[str, Any],
        weights: dict[str, int] | None = None,
        recruiter_id: int | None = None,
    ) -> Vacancy:
        """
        Create vacancy from parsed VacancyInput data.
        
        Args:
            parsed_data: Parsed vacancy data (VacancyInput format)
            weights: Criteria weights (0-10 scale)
            recruiter_id: Recruiter ID (optional)
            
        Returns:
            Created Vacancy object
        """
        # Extract core data
        core = parsed_data.get("core") or {}
        career_level = core.get("careerLevel") or {}
        
        # Create main vacancy record
        metadata = parsed_data.get("metadata") or {}
        vacancy = Vacancy(
            recruiter_id=recruiter_id,
            job_title=core.get("jobTitle") or "Untitled",
            synonyms=core.get("synonyms"),
            career_level_code=career_level.get("code"),
            experience_years_min=career_level.get("experienceYearsMin"),
            experience_years_max=career_level.get("experienceYearsMax"),
            status=metadata.get("status") or "draft",
            priority=metadata.get("priority"),
            tags=metadata.get("tags"),
        )
        
        self.db.add(vacancy)
        await self.db.flush()  # Get vacancy.id
        
        # Create company record
        company_data = parsed_data.get("company")
        if company_data:
            company = VacancyCompany(
                vacancy_id=vacancy.id,
                name=company_data.get("name"),
                external_id=company_data.get("externalId"),
                type=company_data.get("type"),
                size=company_data.get("size"),
                okved=company_data.get("okved"),
                activity_sphere=company_data.get("activitySphere"),
                public_links=company_data.get("publicLinks"),
            )
            self.db.add(company)
        
        # Create classification record
        classification_data = parsed_data.get("classification")
        if classification_data:
            org_level = classification_data.get("orgLevel") or {}
            classification = VacancyClassification(
                vacancy_id=vacancy.id,
                org_level_code=org_level.get("code") if org_level else None,
                business_model=classification_data.get("businessModel"),
                project_type=classification_data.get("projectType"),
            )
            self.db.add(classification)
        
        # Create work conditions record
        work_conditions_data = parsed_data.get("workConditions")
        if work_conditions_data:
            salary = work_conditions_data.get("salary", {}) or {}
            location = work_conditions_data.get("location", {}) or {}
            employment = work_conditions_data.get("employmentType", {}) or {}
            schedule = work_conditions_data.get("schedule", {}) or {}
            
            work_conditions = VacancyWorkConditions(
                vacancy_id=vacancy.id,
                employment_type=employment.get("name") if isinstance(employment, dict) else employment,
                schedule_type=schedule.get("name") if isinstance(schedule, dict) else schedule,
                work_hours=work_conditions_data.get("workHours"),
                salary_min=salary.get("amountMin"),
                salary_max=salary.get("amountMax"),
                salary_currency=salary.get("currency", "RUB"),
                salary_period=salary.get("period", "month"),
                salary_comment=salary.get("comment"),
                location_city=location.get("city"),
                location_region=location.get("region"),
                location_country=location.get("country"),
                remote_type=location.get("remote"),
                relocation_support=location.get("relocationSupport"),
                visa_support=location.get("visaSupport"),
            )
            self.db.add(work_conditions)
        
        # Create requirements record
        requirements_data = parsed_data.get("requirements")
        if requirements_data:
            requirements = VacancyRequirements(
                vacancy_id=vacancy.id,
                education=requirements_data.get("education"),
                experience=requirements_data.get("experience"),
            )
            self.db.add(requirements)
            
            # Create skills records
            skills_data = requirements_data.get("skills", []) or []
            for skill in skills_data:
                vacancy_skill = VacancySkill(
                    vacancy_id=vacancy.id,
                    skill_name=skill.get("name", "Unknown"),
                    category=skill.get("category", "hard"),
                    is_required=skill.get("isRequired", True),
                    level=skill.get("level"),
                    comment=skill.get("comment"),
                )
                self.db.add(vacancy_skill)
            
            # Create languages records
            languages_data = requirements_data.get("languages", []) or []
            for lang in languages_data:
                vacancy_language = VacancyLanguage(
                    vacancy_id=vacancy.id,
                    language_name=lang.get("name", "Unknown"),
                    language_code=lang.get("code"),
                    proficiency=lang.get("proficiency"),
                    is_required=lang.get("isRequired", True),
                )
                self.db.add(vacancy_language)
        
        # Create responsibilities record
        responsibilities_data = parsed_data.get("responsibilities")
        if responsibilities_data:
            responsibilities = VacancyResponsibilities(
                vacancy_id=vacancy.id,
                scope=responsibilities_data.get("scope"),
                zones=responsibilities_data.get("zones"),
                critical_tasks=responsibilities_data.get("criticalTasks"),
                process_ownership=responsibilities_data.get("processOwnership"),
                decision_authority=responsibilities_data.get("decisionAuthority"),
                competency_model=responsibilities_data.get("competencyModel"),
                business_processes=responsibilities_data.get("businessProcesses"),
            )
            self.db.add(responsibilities)
        
        # Create org structure record
        org_structure_data = parsed_data.get("orgStructure")
        if org_structure_data:
            org_structure = VacancyOrgStructure(
                vacancy_id=vacancy.id,
                reports_to=org_structure_data.get("reportsTo"),
                subordinates_count=org_structure_data.get("subordinatesCount"),
                org_unit=org_structure_data.get("orgUnit"),
                team_roles=org_structure_data.get("teamRoles"),
                cross_functional_links=org_structure_data.get("crossFunctionalLinks"),
            )
            self.db.add(org_structure)
        
        # Create executive search record (all JSONB fields)
        hiring_context = parsed_data.get("hiringContext")
        success_criteria = parsed_data.get("successCriteria")
        differentiators = parsed_data.get("differentiators")
        dealbreakers = parsed_data.get("dealbreakers")
        search_difficulty = parsed_data.get("searchDifficulty")
        
        if any([hiring_context, success_criteria, differentiators, dealbreakers, search_difficulty]):
            executive_search = VacancyExecutiveSearch(
                vacancy_id=vacancy.id,
                hiring_context=hiring_context,
                success_criteria=success_criteria,
                differentiators=differentiators,
                dealbreakers=dealbreakers,
                search_difficulty=search_difficulty,
            )
            self.db.add(executive_search)
        
        # Create full text record
        full_text_data = parsed_data.get("fullText")
        if full_text_data:
            full_text = VacancyFullText(
                vacancy_id=vacancy.id,
                full_text=full_text_data.get("text"),
                source=full_text_data.get("source"),
            )
            self.db.add(full_text)
        
        # Create weights record
        if weights:
            vacancy_weights = VacancyWeights(
                vacancy_id=vacancy.id,
                weight_core=weights.get("core", 6),
                weight_company=weights.get("company", 5),
                weight_work_conditions=weights.get("workConditions", 5),
                weight_requirements=weights.get("requirements", 6),
                weight_responsibilities=weights.get("responsibilities", 5),
                weight_hiring_context=weights.get("hiringContext", 5),
                weight_success_criteria=weights.get("successCriteria", 5),
                weight_differentiators=weights.get("differentiators", 5),
                weight_dealbreakers=weights.get("dealbreakers", 5),
            )
            self.db.add(vacancy_weights)
        
        await self.db.commit()
        
        # Reload with all relationships
        vacancy_result = await self.get_by_id(vacancy.id)
        if vacancy_result is None:
            raise ValueError(f"Failed to retrieve created vacancy with id={vacancy.id}")
        return vacancy_result

    async def delete(self, vacancy_id: int) -> bool:
        """
        Delete vacancy by ID.
        
        Args:
            vacancy_id: Vacancy ID
            
        Returns:
            True if deleted, False if not found
        """
        vacancy = await self.get_by_id(vacancy_id)
        if vacancy:
            await self.db.delete(vacancy)
            await self.db.commit()
            return True
        return False

    async def count(self, status: str | None = None) -> int:
        """
        Count total vacancies.
        
        Args:
            status: Filter by status (optional)
            
        Returns:
            Total count
        """
        from sqlalchemy import func
        
        query = select(func.count(Vacancy.id))
        if status:
            query = query.where(Vacancy.status == status)
        
        result = await self.db.execute(query)
        return result.scalar() or 0
