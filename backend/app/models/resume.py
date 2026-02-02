"""
Pydantic models for Resume parsing and validation.
Defines the structure for parsed resume data.
"""

from datetime import date
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ============ ENUMS ============


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class EmploymentType(str, Enum):
    FULL_TIME = "full-time"
    PART_TIME = "part-time"
    CONTRACT = "contract"
    FREELANCE = "freelance"
    INTERNSHIP = "internship"


class ScheduleType(str, Enum):
    STANDARD = "5/2"
    SHIFT = "2/2"
    FLEXIBLE = "flexible"
    REMOTE_ASYNC = "remote-async"


class RemotePreference(str, Enum):
    OFFICE = "office"
    REMOTE = "remote"
    HYBRID = "hybrid"


class EducationLevel(str, Enum):
    SECONDARY = "secondary"
    VOCATIONAL = "vocational"
    BACHELOR = "bachelor"
    MASTER = "master"
    PHD = "phd"
    MBA = "mba"


class SkillCategory(str, Enum):
    HARD = "hard"
    SOFT = "soft"
    MANAGEMENT = "management"
    DIGITAL_TOOL = "digital_tool"


class SkillLevel(str, Enum):
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class LanguageProficiency(str, Enum):
    A1 = "A1"
    A2 = "A2"
    B1 = "B1"
    B2 = "B2"
    C1 = "C1"
    C2 = "C2"
    NATIVE = "native"


# ============ NESTED MODELS ============


class PersonalInfo(BaseModel):
    """Personal information block."""
    first_name: str | None = Field(None, alias="firstName", description="First name")
    last_name: str | None = Field(None, alias="lastName", description="Last name")
    middle_name: str | None = Field(None, alias="middleName", description="Middle name/patronymic")
    birth_date: date | None = Field(None, alias="birthDate", description="Date of birth")
    gender: Gender | None = None
    photo_url: str | None = Field(None, alias="photoUrl")

    class Config:
        populate_by_name = True


class Contacts(BaseModel):
    """Contact information."""
    email: str | None = None
    phone: str | None = None
    phone_secondary: str | None = Field(None, alias="phoneSecondary")
    telegram: str | None = None
    whatsapp: str | None = None
    linkedin_url: str | None = Field(None, alias="linkedinUrl")
    github_url: str | None = Field(None, alias="githubUrl")
    portfolio_url: str | None = Field(None, alias="portfolioUrl")
    other: dict[str, str] | None = None

    class Config:
        populate_by_name = True


class DesiredPosition(BaseModel):
    """Desired job position."""
    title: str | None = None
    salary_min: float | None = Field(None, alias="salaryMin")
    salary_max: float | None = Field(None, alias="salaryMax")
    salary_currency: str = Field("RUB", alias="salaryCurrency")

    class Config:
        populate_by_name = True


class LocationPreferences(BaseModel):
    """Location and relocation preferences."""
    city: str | None = None
    region: str | None = None
    country: str | None = "Россия"
    willing_to_relocate: bool = Field(False, alias="willingToRelocate")
    willing_to_travel: bool = Field(False, alias="willingToTravel")
    travel_time_percent: int | None = Field(None, alias="travelTimePercent")

    class Config:
        populate_by_name = True


class EmploymentPreferences(BaseModel):
    """Employment type preferences."""
    employment_type: EmploymentType | None = Field(None, alias="employmentType")
    schedule_type: ScheduleType | None = Field(None, alias="scheduleType")
    remote_preference: RemotePreference | None = Field(None, alias="remotePreference")

    class Config:
        populate_by_name = True


class WorkExperience(BaseModel):
    """Single work experience entry."""
    company_name: str = Field(..., alias="companyName")
    company_industry: str | None = Field(None, alias="companyIndustry")
    company_size: str | None = Field(None, alias="companySize")
    company_url: str | None = Field(None, alias="companyUrl")
    
    position: str
    department: str | None = None
    
    start_date: date | None = Field(None, alias="startDate")
    end_date: date | None = Field(None, alias="endDate")
    is_current: bool = Field(False, alias="isCurrent")
    duration_months: int | None = Field(None, alias="durationMonths")
    
    location_city: str | None = Field(None, alias="locationCity")
    location_country: str | None = Field(None, alias="locationCountry")
    
    responsibilities: str | None = None
    achievements: str | None = None
    technologies: list[str] | None = None

    class Config:
        populate_by_name = True


class Education(BaseModel):
    """Single education entry."""
    institution_name: str = Field(..., alias="institutionName")
    institution_type: str | None = Field(None, alias="institutionType")
    
    faculty: str | None = None
    specialization: str | None = None
    degree: EducationLevel | None = None
    
    start_year: int | None = Field(None, alias="startYear")
    end_year: int | None = Field(None, alias="endYear")
    is_current: bool = Field(False, alias="isCurrent")
    
    location_city: str | None = Field(None, alias="locationCity")
    location_country: str | None = Field(None, alias="locationCountry")
    
    description: str | None = None
    gpa: float | None = None

    class Config:
        populate_by_name = True


class Skill(BaseModel):
    """Single skill entry."""
    name: str
    category: SkillCategory = SkillCategory.HARD
    level: SkillLevel | None = None
    years_of_experience: int | None = Field(None, alias="yearsOfExperience")
    last_used_year: int | None = Field(None, alias="lastUsedYear")

    class Config:
        populate_by_name = True


class Language(BaseModel):
    """Single language entry."""
    name: str
    code: str | None = None
    proficiency: LanguageProficiency | None = None
    is_native: bool = Field(False, alias="isNative")

    class Config:
        populate_by_name = True


class Certificate(BaseModel):
    """Single certificate entry."""
    name: str
    issuing_organization: str | None = Field(None, alias="issuingOrganization")
    issue_date: date | None = Field(None, alias="issueDate")
    expiry_date: date | None = Field(None, alias="expiryDate")
    credential_id: str | None = Field(None, alias="credentialId")
    credential_url: str | None = Field(None, alias="credentialUrl")
    description: str | None = None

    class Config:
        populate_by_name = True


# ============ MAIN RESUME MODEL ============


class ResumeInput(BaseModel):
    """
    Main resume input model.
    Represents the complete parsed structure of a resume.
    """
    # Personal information
    personal: PersonalInfo | None = None
    contacts: Contacts | None = None
    
    # Position preferences
    desired_position: DesiredPosition | None = Field(None, alias="desiredPosition")
    location: LocationPreferences | None = None
    employment: EmploymentPreferences | None = None
    
    # Professional summary
    summary: str | None = None
    total_experience_months: int | None = Field(None, alias="totalExperienceMonths")
    
    # Experience and education
    experience: list[WorkExperience] | None = None
    education: list[Education] | None = None
    
    # Skills and languages
    skills: list[Skill] | None = None
    languages: list[Language] | None = None
    
    # Certifications
    certificates: list[Certificate] | None = None
    
    # Full text (for reference)
    full_text: dict[str, Any] | None = Field(None, alias="fullText")

    class Config:
        populate_by_name = True


# ============ RESPONSE MODELS ============


class ParseResumeResponse(BaseModel):
    """Response from resume parsing."""
    data: ResumeInput
    confidence: float = Field(..., ge=0, le=1, description="Parsing confidence score")
    warnings: list[str] | None = None
    missing_fields: list[str] | None = Field(None, alias="missingFields")

    class Config:
        populate_by_name = True


class ResumeMatchResult(BaseModel):
    """Result of resume-vacancy matching."""
    resume_id: int = Field(..., alias="resumeId")
    vacancy_id: int = Field(..., alias="vacancyId")
    match_score: float = Field(..., alias="matchScore", ge=0, le=100)
    cosine_similarity: float = Field(..., alias="cosineSimilarity")
    weighted_scores: dict[str, dict[str, float]] = Field(..., alias="weightedScores")
    gaps_analysis: dict[str, Any] = Field(..., alias="gapsAnalysis")
    strengths: dict[str, Any] | None = None
    interview_questions: list[dict[str, str]] = Field(..., alias="interviewQuestions")

    class Config:
        populate_by_name = True
