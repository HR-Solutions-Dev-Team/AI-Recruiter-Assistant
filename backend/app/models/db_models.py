"""
SQLAlchemy ORM models for database tables.
Maps to the normalized vacancy schema in PostgreSQL.
"""

from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# ============ DICTIONARIES ============


class DictIndustry(Base):
    """Industries dictionary (OKVED-based)."""
    __tablename__ = "dict_industries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str | None] = mapped_column(String(10), unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("dict_industries.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class DictActivitySphere(Base):
    """Activity spheres dictionary (hierarchical)."""
    __tablename__ = "dict_activity_spheres"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    level: Mapped[int] = mapped_column(Integer, nullable=False)  # 1=sphere, 2=sub, 3=spec
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("dict_activity_spheres.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class DictSkill(Base):
    """Skills dictionary."""
    __tablename__ = "dict_skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # hard, soft, management, digital_tool
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class DictLanguage(Base):
    """Languages dictionary."""
    __tablename__ = "dict_languages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class DictBusinessFunction(Base):
    """Business functions dictionary."""
    __tablename__ = "dict_business_functions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class DictRoleFamily(Base):
    """Role families dictionary."""
    __tablename__ = "dict_role_families"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# ============ USERS ============


class Recruiter(Base):
    """Recruiters table."""
    __tablename__ = "recruiters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    vacancies: Mapped[list["Vacancy"]] = relationship(back_populates="recruiter")


# ============ VACANCY (MAIN) ============


class Vacancy(Base):
    """Main vacancies table (core data only)."""
    __tablename__ = "vacancies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    recruiter_id: Mapped[int | None] = mapped_column(ForeignKey("recruiters.id"))
    
    # Core fields
    job_title: Mapped[str] = mapped_column(String(200), nullable=False)
    synonyms: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    career_level_code: Mapped[str | None] = mapped_column(String(20))
    experience_years_min: Mapped[int | None] = mapped_column(Integer)
    experience_years_max: Mapped[int | None] = mapped_column(Integer)
    industry_id: Mapped[int | None] = mapped_column(ForeignKey("dict_industries.id"))
    
    # Metadata
    status: Mapped[str] = mapped_column(String(20), default="draft")
    priority: Mapped[str | None] = mapped_column(String(20))
    deadline: Mapped[date | None] = mapped_column(Date)
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    recruiter: Mapped["Recruiter | None"] = relationship(back_populates="vacancies")
    industry: Mapped["DictIndustry | None"] = relationship()
    
    company: Mapped["VacancyCompany | None"] = relationship(back_populates="vacancy", uselist=False, cascade="all, delete-orphan")
    classification: Mapped["VacancyClassification | None"] = relationship(back_populates="vacancy", uselist=False, cascade="all, delete-orphan")
    work_conditions: Mapped["VacancyWorkConditions | None"] = relationship(back_populates="vacancy", uselist=False, cascade="all, delete-orphan")
    requirements: Mapped["VacancyRequirements | None"] = relationship(back_populates="vacancy", uselist=False, cascade="all, delete-orphan")
    responsibilities: Mapped["VacancyResponsibilities | None"] = relationship(back_populates="vacancy", uselist=False, cascade="all, delete-orphan")
    org_structure: Mapped["VacancyOrgStructure | None"] = relationship(back_populates="vacancy", uselist=False, cascade="all, delete-orphan")
    executive_search: Mapped["VacancyExecutiveSearch | None"] = relationship(back_populates="vacancy", uselist=False, cascade="all, delete-orphan")
    full_text: Mapped["VacancyFullText | None"] = relationship(back_populates="vacancy", uselist=False, cascade="all, delete-orphan")
    weights: Mapped["VacancyWeights | None"] = relationship(back_populates="vacancy", uselist=False, cascade="all, delete-orphan")
    
    skills: Mapped[list["VacancySkill"]] = relationship(back_populates="vacancy", cascade="all, delete-orphan")
    languages: Mapped[list["VacancyLanguage"]] = relationship(back_populates="vacancy", cascade="all, delete-orphan")


# ============ VACANCY RELATED TABLES (1:1) ============


class VacancyCompany(Base):
    """Company information (1:1 with vacancy)."""
    __tablename__ = "vacancy_companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vacancy_id: Mapped[int] = mapped_column(ForeignKey("vacancies.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    name: Mapped[str | None] = mapped_column(String(255))
    external_id: Mapped[str | None] = mapped_column(String(100))
    type: Mapped[str | None] = mapped_column(String(50))
    size: Mapped[str | None] = mapped_column(String(20))
    industry_id: Mapped[int | None] = mapped_column(ForeignKey("dict_industries.id"))
    okved: Mapped[str | None] = mapped_column(String(20))
    activity_sphere: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    public_links: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    vacancy: Mapped["Vacancy"] = relationship(back_populates="company")


class VacancyClassification(Base):
    """Classification (1:1 with vacancy)."""
    __tablename__ = "vacancy_classifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vacancy_id: Mapped[int] = mapped_column(ForeignKey("vacancies.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    business_function_id: Mapped[int | None] = mapped_column(ForeignKey("dict_business_functions.id"))
    role_family_id: Mapped[int | None] = mapped_column(ForeignKey("dict_role_families.id"))
    org_level_code: Mapped[str | None] = mapped_column(String(20))
    business_model: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    project_type: Mapped[str | None] = mapped_column(String(100))
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    vacancy: Mapped["Vacancy"] = relationship(back_populates="classification")


class VacancyWorkConditions(Base):
    """Work conditions (1:1 with vacancy)."""
    __tablename__ = "vacancy_work_conditions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vacancy_id: Mapped[int] = mapped_column(ForeignKey("vacancies.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # Employment
    employment_type: Mapped[str | None] = mapped_column(String(50))
    schedule_type: Mapped[str | None] = mapped_column(String(50))
    work_hours: Mapped[str | None] = mapped_column(String(100))
    
    # Salary
    salary_min: Mapped[float | None] = mapped_column(Numeric(15, 2))
    salary_max: Mapped[float | None] = mapped_column(Numeric(15, 2))
    salary_currency: Mapped[str] = mapped_column(String(10), default="RUB")
    salary_period: Mapped[str] = mapped_column(String(20), default="month")
    salary_comment: Mapped[str | None] = mapped_column(Text)
    
    # Location
    location_city: Mapped[str | None] = mapped_column(String(100))
    location_region: Mapped[str | None] = mapped_column(String(100))
    location_country: Mapped[str | None] = mapped_column(String(100))
    remote_type: Mapped[str | None] = mapped_column(String(20))
    relocation_support: Mapped[bool | None] = mapped_column(Boolean)
    visa_support: Mapped[bool | None] = mapped_column(Boolean)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    vacancy: Mapped["Vacancy"] = relationship(back_populates="work_conditions")


class VacancyRequirements(Base):
    """Requirements (1:1 with vacancy)."""
    __tablename__ = "vacancy_requirements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vacancy_id: Mapped[int] = mapped_column(ForeignKey("vacancies.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    education: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    experience: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    vacancy: Mapped["Vacancy"] = relationship(back_populates="requirements")


class VacancyResponsibilities(Base):
    """Responsibilities (1:1 with vacancy)."""
    __tablename__ = "vacancy_responsibilities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vacancy_id: Mapped[int] = mapped_column(ForeignKey("vacancies.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    scope: Mapped[str | None] = mapped_column(Text)
    zones: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    critical_tasks: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB)
    process_ownership: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    decision_authority: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    competency_model: Mapped[str | None] = mapped_column(String(255))
    business_processes: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    vacancy: Mapped["Vacancy"] = relationship(back_populates="responsibilities")


class VacancyOrgStructure(Base):
    """Org structure (1:1 with vacancy)."""
    __tablename__ = "vacancy_org_structures"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vacancy_id: Mapped[int] = mapped_column(ForeignKey("vacancies.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    reports_to: Mapped[str | None] = mapped_column(String(255))
    subordinates_count: Mapped[int | None] = mapped_column(Integer)
    org_unit: Mapped[str | None] = mapped_column(String(255))
    team_roles: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    cross_functional_links: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    vacancy: Mapped["Vacancy"] = relationship(back_populates="org_structure")


class VacancyExecutiveSearch(Base):
    """Executive search data (1:1 with vacancy)."""
    __tablename__ = "vacancy_executive_search"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vacancy_id: Mapped[int] = mapped_column(ForeignKey("vacancies.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    hiring_context: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    success_criteria: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    differentiators: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    dealbreakers: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    search_difficulty: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    vacancy: Mapped["Vacancy"] = relationship(back_populates="executive_search")


class VacancyFullText(Base):
    """Full text (1:1 with vacancy)."""
    __tablename__ = "vacancy_full_texts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vacancy_id: Mapped[int] = mapped_column(ForeignKey("vacancies.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    full_text: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(String(20))
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    vacancy: Mapped["Vacancy"] = relationship(back_populates="full_text")


class VacancyWeights(Base):
    """Weights (1:1 with vacancy)."""
    __tablename__ = "vacancy_weights"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vacancy_id: Mapped[int] = mapped_column(ForeignKey("vacancies.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    weight_core: Mapped[int] = mapped_column(Integer, default=6)
    weight_company: Mapped[int] = mapped_column(Integer, default=5)
    weight_work_conditions: Mapped[int] = mapped_column(Integer, default=5)
    weight_requirements: Mapped[int] = mapped_column(Integer, default=6)
    weight_responsibilities: Mapped[int] = mapped_column(Integer, default=5)
    weight_hiring_context: Mapped[int] = mapped_column(Integer, default=5)
    weight_success_criteria: Mapped[int] = mapped_column(Integer, default=5)
    weight_differentiators: Mapped[int] = mapped_column(Integer, default=5)
    weight_dealbreakers: Mapped[int] = mapped_column(Integer, default=5)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    vacancy: Mapped["Vacancy"] = relationship(back_populates="weights")


# ============ JUNCTION TABLES (Many-to-Many) ============


class VacancySkill(Base):
    """Vacancy <-> Skills junction table."""
    __tablename__ = "vacancy_skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vacancy_id: Mapped[int] = mapped_column(ForeignKey("vacancies.id", ondelete="CASCADE"), nullable=False)
    skill_id: Mapped[int | None] = mapped_column(ForeignKey("dict_skills.id"))
    
    skill_name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, default=True)
    level: Mapped[str | None] = mapped_column(String(20))
    comment: Mapped[str | None] = mapped_column(Text)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    vacancy: Mapped["Vacancy"] = relationship(back_populates="skills")
    skill: Mapped["DictSkill | None"] = relationship()


class VacancyLanguage(Base):
    """Vacancy <-> Languages junction table."""
    __tablename__ = "vacancy_languages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vacancy_id: Mapped[int] = mapped_column(ForeignKey("vacancies.id", ondelete="CASCADE"), nullable=False)
    language_id: Mapped[int | None] = mapped_column(ForeignKey("dict_languages.id"))
    
    language_name: Mapped[str] = mapped_column(String(100), nullable=False)
    language_code: Mapped[str | None] = mapped_column(String(10))
    proficiency: Mapped[str | None] = mapped_column(String(10))
    is_required: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    vacancy: Mapped["Vacancy"] = relationship(back_populates="languages")
    language: Mapped["DictLanguage | None"] = relationship()


# ============ RESUME (MAIN) ============


class Resume(Base):
    """Main resumes table."""
    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Personal info
    first_name: Mapped[str | None] = mapped_column(String(100))
    last_name: Mapped[str | None] = mapped_column(String(100))
    middle_name: Mapped[str | None] = mapped_column(String(100))
    birth_date: Mapped[date | None] = mapped_column(Date)
    gender: Mapped[str | None] = mapped_column(String(10))
    photo_url: Mapped[str | None] = mapped_column(Text)
    
    # Desired position
    desired_position: Mapped[str | None] = mapped_column(String(255))
    desired_salary_min: Mapped[float | None] = mapped_column(Numeric(15, 2))
    desired_salary_max: Mapped[float | None] = mapped_column(Numeric(15, 2))
    desired_salary_currency: Mapped[str] = mapped_column(String(10), default="RUB")
    
    # Location preferences
    city: Mapped[str | None] = mapped_column(String(100))
    region: Mapped[str | None] = mapped_column(String(100))
    country: Mapped[str | None] = mapped_column(String(100), default="Россия")
    willing_to_relocate: Mapped[bool] = mapped_column(Boolean, default=False)
    willing_to_travel: Mapped[bool] = mapped_column(Boolean, default=False)
    travel_time_percent: Mapped[int | None] = mapped_column(Integer)
    
    # Employment preferences
    employment_type: Mapped[str | None] = mapped_column(String(50))
    schedule_type: Mapped[str | None] = mapped_column(String(50))
    remote_preference: Mapped[str | None] = mapped_column(String(20))
    
    # Professional summary
    summary: Mapped[str | None] = mapped_column(Text)
    total_experience_months: Mapped[int | None] = mapped_column(Integer)
    
    # Metadata
    source: Mapped[str | None] = mapped_column(String(50))
    source_url: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="active")
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    contacts: Mapped["ResumeContacts | None"] = relationship(back_populates="resume", uselist=False, cascade="all, delete-orphan")
    experiences: Mapped[list["ResumeExperience"]] = relationship(back_populates="resume", cascade="all, delete-orphan")
    education: Mapped[list["ResumeEducation"]] = relationship(back_populates="resume", cascade="all, delete-orphan")
    skills: Mapped[list["ResumeSkill"]] = relationship(back_populates="resume", cascade="all, delete-orphan")
    languages: Mapped[list["ResumeLanguage"]] = relationship(back_populates="resume", cascade="all, delete-orphan")
    certificates: Mapped[list["ResumeCertificate"]] = relationship(back_populates="resume", cascade="all, delete-orphan")
    full_text: Mapped["ResumeFullText | None"] = relationship(back_populates="resume", uselist=False, cascade="all, delete-orphan")
    vector: Mapped["ResumeVector | None"] = relationship(back_populates="resume", uselist=False, cascade="all, delete-orphan")
    vacancy_matches: Mapped[list["ResumeVacancyMatch"]] = relationship(back_populates="resume", cascade="all, delete-orphan")


# ============ RESUME RELATED TABLES ============


class ResumeContacts(Base):
    """Resume contacts (1:1 with resume)."""
    __tablename__ = "resume_contacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50))
    phone_secondary: Mapped[str | None] = mapped_column(String(50))
    telegram: Mapped[str | None] = mapped_column(String(100))
    whatsapp: Mapped[str | None] = mapped_column(String(50))
    linkedin_url: Mapped[str | None] = mapped_column(Text)
    github_url: Mapped[str | None] = mapped_column(Text)
    portfolio_url: Mapped[str | None] = mapped_column(Text)
    other_contacts: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    resume: Mapped["Resume"] = relationship(back_populates="contacts")


class ResumeExperience(Base):
    """Work experience records."""
    __tablename__ = "resume_experiences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False)
    
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    company_industry: Mapped[str | None] = mapped_column(String(100))
    company_size: Mapped[str | None] = mapped_column(String(50))
    company_url: Mapped[str | None] = mapped_column(Text)
    
    position: Mapped[str] = mapped_column(String(255), nullable=False)
    department: Mapped[str | None] = mapped_column(String(255))
    
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)
    duration_months: Mapped[int | None] = mapped_column(Integer)
    
    location_city: Mapped[str | None] = mapped_column(String(100))
    location_country: Mapped[str | None] = mapped_column(String(100))
    
    responsibilities: Mapped[str | None] = mapped_column(Text)
    achievements: Mapped[str | None] = mapped_column(Text)
    technologies: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    resume: Mapped["Resume"] = relationship(back_populates="experiences")


class ResumeEducation(Base):
    """Education records."""
    __tablename__ = "resume_education"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False)
    
    institution_name: Mapped[str] = mapped_column(String(255), nullable=False)
    institution_type: Mapped[str | None] = mapped_column(String(50))
    
    faculty: Mapped[str | None] = mapped_column(String(255))
    specialization: Mapped[str | None] = mapped_column(String(255))
    degree: Mapped[str | None] = mapped_column(String(50))
    
    start_year: Mapped[int | None] = mapped_column(Integer)
    end_year: Mapped[int | None] = mapped_column(Integer)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)
    
    location_city: Mapped[str | None] = mapped_column(String(100))
    location_country: Mapped[str | None] = mapped_column(String(100))
    
    description: Mapped[str | None] = mapped_column(Text)
    gpa: Mapped[float | None] = mapped_column(Numeric(3, 2))
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    resume: Mapped["Resume"] = relationship(back_populates="education")


class ResumeSkill(Base):
    """Resume skills."""
    __tablename__ = "resume_skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False)
    skill_id: Mapped[int | None] = mapped_column(ForeignKey("dict_skills.id"))
    
    skill_name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(50), default="hard")
    level: Mapped[str | None] = mapped_column(String(20))
    years_of_experience: Mapped[int | None] = mapped_column(Integer)
    last_used_year: Mapped[int | None] = mapped_column(Integer)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    resume: Mapped["Resume"] = relationship(back_populates="skills")
    skill: Mapped["DictSkill | None"] = relationship()


class ResumeLanguage(Base):
    """Resume languages."""
    __tablename__ = "resume_languages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False)
    language_id: Mapped[int | None] = mapped_column(ForeignKey("dict_languages.id"))
    
    language_name: Mapped[str] = mapped_column(String(100), nullable=False)
    language_code: Mapped[str | None] = mapped_column(String(10))
    proficiency: Mapped[str | None] = mapped_column(String(20))
    is_native: Mapped[bool] = mapped_column(Boolean, default=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    resume: Mapped["Resume"] = relationship(back_populates="languages")
    language: Mapped["DictLanguage | None"] = relationship()


class ResumeCertificate(Base):
    """Resume certificates."""
    __tablename__ = "resume_certificates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False)
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    issuing_organization: Mapped[str | None] = mapped_column(String(255))
    issue_date: Mapped[date | None] = mapped_column(Date)
    expiry_date: Mapped[date | None] = mapped_column(Date)
    credential_id: Mapped[str | None] = mapped_column(String(255))
    credential_url: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    resume: Mapped["Resume"] = relationship(back_populates="certificates")


class ResumeFullText(Base):
    """Full text content (1:1 with resume)."""
    __tablename__ = "resume_full_texts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    full_text: Mapped[str | None] = mapped_column(Text)
    source_file_name: Mapped[str | None] = mapped_column(String(255))
    source_file_type: Mapped[str | None] = mapped_column(String(20))
    source_file_size: Mapped[int | None] = mapped_column(Integer)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    resume: Mapped["Resume"] = relationship(back_populates="full_text")


class ResumeVector(Base):
    """Resume vector embeddings (1:1 with resume)."""
    __tablename__ = "resume_vectors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # Note: embedding column is vector(1536) in PostgreSQL
    # SQLAlchemy doesn't have native pgvector support, so we use raw SQL for vector operations
    model_name: Mapped[str] = mapped_column(String(100), default="text-embedding-3-small")
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    resume: Mapped["Resume"] = relationship(back_populates="vector")


class VacancyVector(Base):
    """Vacancy vector embeddings (1:1 with vacancy)."""
    __tablename__ = "vacancy_vectors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vacancy_id: Mapped[int] = mapped_column(ForeignKey("vacancies.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # Note: embedding column is vector(1536) in PostgreSQL
    model_name: Mapped[str] = mapped_column(String(100), default="text-embedding-3-small")
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    vacancy: Mapped["Vacancy"] = relationship()


class ResumeVacancyMatch(Base):
    """Resume-Vacancy matching results."""
    __tablename__ = "resume_vacancy_matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False)
    vacancy_id: Mapped[int] = mapped_column(ForeignKey("vacancies.id", ondelete="CASCADE"), nullable=False)
    
    # Overall match score (0-100)
    match_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    
    # Detailed weighted scores by category
    weighted_scores: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    
    # Raw cosine similarity
    cosine_similarity: Mapped[float | None] = mapped_column(Numeric(10, 8))
    
    # Generated interview questions
    interview_questions: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB)
    
    # Gap analysis
    gaps_analysis: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    
    # Candidate strengths
    strengths: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    resume: Mapped["Resume"] = relationship(back_populates="vacancy_matches")
    vacancy: Mapped["Vacancy"] = relationship()
