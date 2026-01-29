"""
Pydantic модели для входных параметров вакансии.
Сгенерировано из schemas/vacancy-input.schema.json
Используется для парсинга текста вакансии через LLM и валидации API.
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


# ============ ENUMS ============


class CareerLevelCode(str, Enum):
    INTERN = "intern"
    JUNIOR = "junior"
    MIDDLE = "middle"
    SENIOR = "senior"
    LEAD = "lead"
    HEAD = "head"
    DIRECTOR = "director"
    C_LEVEL = "c-level"


class OrgLevelCode(str, Enum):
    IC = "ic"
    TEAM_LEAD = "team_lead"
    MANAGER = "manager"
    SENIOR_MANAGER = "senior_manager"
    DIRECTOR = "director"
    VP = "vp"
    C_LEVEL = "c_level"


class CompanyType(str, Enum):
    STARTUP = "startup"
    SME = "sme"
    ENTERPRISE = "enterprise"
    CORPORATION = "corporation"
    GOVERNMENT = "government"
    NGO = "ngo"
    CONSULTING = "consulting"


class CompanySize(str, Enum):
    XS = "1-10"
    S = "11-50"
    M = "51-200"
    L = "201-500"
    XL = "501-1000"
    XXL = "1001-5000"
    ENTERPRISE = "5000+"


class LinkType(str, Enum):
    SITE = "site"
    HH = "hh"
    LINKEDIN = "linkedin"
    HABR = "habr"
    GLASSDOOR = "glassdoor"
    GITHUB = "github"
    OTHER = "other"


class EmploymentType(str, Enum):
    FULL_TIME = "full-time"
    PART_TIME = "part-time"
    CONTRACT = "contract"
    FREELANCE = "freelance"
    INTERNSHIP = "internship"
    TEMPORARY = "temporary"


class ScheduleType(str, Enum):
    STANDARD = "5/2"
    SHIFT_2_2 = "2/2"
    FLEXIBLE = "flexible"
    SHIFT = "shift"
    REMOTE_ASYNC = "remote-async"
    HYBRID = "hybrid"


class Currency(str, Enum):
    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    KZT = "KZT"
    BYN = "BYN"
    UAH = "UAH"
    GEL = "GEL"
    AMD = "AMD"
    AZN = "AZN"


class SalaryPeriod(str, Enum):
    MONTH = "month"
    YEAR = "year"
    HOUR = "hour"
    PROJECT = "project"


class RemoteType(str, Enum):
    OFFICE = "office"
    REMOTE = "remote"
    HYBRID = "hybrid"
    RELOCATE = "relocate"


class EducationLevel(str, Enum):
    ANY = "any"
    SECONDARY = "secondary"
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


class VacancyStatus(str, Enum):
    DRAFT = "draft"
    REVIEW = "review"
    ACTIVE = "active"
    PAUSED = "paused"
    CLOSED = "closed"
    ARCHIVED = "archived"


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TextSource(str, Enum):
    MANUAL = "manual"
    GENERATED = "generated"
    IMPORTED = "imported"


class BusinessSegment(str, Enum):
    B2B = "B2B"
    B2C = "B2C"
    B2B2C = "B2B2C"
    B2G = "B2G"
    C2C = "C2C"
    D2C = "D2C"


# ============ NESTED MODELS ============


class CareerLevel(BaseModel):
    """Уровень позиции в карьерной иерархии"""

    code: Optional[CareerLevelCode] = None
    experience_years_min: Optional[int] = Field(None, ge=0, alias="experienceYearsMin")
    experience_years_max: Optional[int] = Field(None, ge=0, alias="experienceYearsMax")

    class Config:
        populate_by_name = True


class Industry(BaseModel):
    """Отрасль/индустрия"""

    id: Optional[str] = None
    name: Optional[str] = None
    sub_industry: Optional[str] = Field(None, alias="subIndustry")

    class Config:
        populate_by_name = True


class CompanyBenefit(BaseModel):
    """Бенефит компании"""

    id: Optional[str] = None
    name: Optional[str] = None


class CompanyLink(BaseModel):
    """Публичная ссылка компании"""

    type: LinkType
    url: str


class BusinessFunction(BaseModel):
    """Бизнес-функция"""

    id: Optional[str] = None
    name: Optional[str] = None


class RoleFamily(BaseModel):
    """Семейство ролей"""

    id: Optional[str] = None
    name: Optional[str] = None


class OrgLevel(BaseModel):
    """Организационный уровень"""

    code: Optional[OrgLevelCode] = None
    name: Optional[str] = None


class BusinessModel(BaseModel):
    """Бизнес-модель"""

    id: Optional[str] = None
    name: Optional[str] = None
    segment: Optional[BusinessSegment] = None


class EmploymentTypeInfo(BaseModel):
    """Тип занятости"""

    id: Optional[str] = None
    name: Optional[EmploymentType] = None


class ScheduleInfo(BaseModel):
    """График работы"""

    id: Optional[str] = None
    name: Optional[ScheduleType] = None


class Salary(BaseModel):
    """Компенсация"""

    amount_min: Optional[float] = Field(None, ge=0, alias="amountMin")
    amount_max: Optional[float] = Field(None, ge=0, alias="amountMax")
    currency: Optional[Currency] = Currency.RUB
    period: Optional[SalaryPeriod] = SalaryPeriod.MONTH
    comment: Optional[str] = None

    class Config:
        populate_by_name = True


class Location(BaseModel):
    """Локация"""

    city: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None
    remote: Optional[RemoteType] = None
    relocation_support: Optional[bool] = Field(None, alias="relocationSupport")
    visa_support: Optional[bool] = Field(None, alias="visaSupport")

    class Config:
        populate_by_name = True


class Education(BaseModel):
    """Требования к образованию"""

    level: Optional[EducationLevel] = None
    fields: Optional[list[str]] = None
    comment: Optional[str] = None


class Experience(BaseModel):
    """Требования к опыту"""

    years_min: Optional[int] = Field(None, ge=0, alias="yearsMin")
    years_max: Optional[int] = Field(None, ge=0, alias="yearsMax")
    domains: Optional[list[str]] = None
    must_have: Optional[list[str]] = Field(None, alias="mustHave")
    nice_to_have: Optional[list[str]] = Field(None, alias="niceToHave")

    class Config:
        populate_by_name = True


class Skill(BaseModel):
    """Навык или компетенция"""

    id: Optional[str] = None
    name: str
    category: SkillCategory
    is_required: Optional[bool] = Field(True, alias="isRequired")
    level: Optional[SkillLevel] = None
    comment: Optional[str] = None

    class Config:
        populate_by_name = True


class Language(BaseModel):
    """Требование к языку"""

    id: Optional[str] = None
    code: Optional[str] = None
    name: str
    proficiency: Optional[LanguageProficiency] = None
    is_required: Optional[bool] = Field(True, alias="isRequired")

    class Config:
        populate_by_name = True


class Subprocess(BaseModel):
    """Подпроцесс"""

    id: Optional[str] = None
    name: str


class BusinessProcess(BaseModel):
    """Бизнес-процесс с подпроцессами"""

    id: Optional[str] = None
    name: str
    subprocesses: Optional[list[Subprocess]] = None


# ============ MAIN BLOCKS ============


class VacancyCore(BaseModel):
    """
    Ядро вакансии (обязательный блок).
    Минимально необходимая информация для создания вакансии.
    """

    job_title: str = Field(
        ..., min_length=2, max_length=200, alias="jobTitle", description="Название должности/роли"
    )
    synonyms: Optional[list[str]] = Field(
        None, description="Альтернативные названия роли для расширения поиска"
    )
    career_level: Optional[CareerLevel] = Field(None, alias="careerLevel")
    industry: Optional[Industry] = None

    class Config:
        populate_by_name = True


class VacancyCompany(BaseModel):
    """Информация о компании-работодателе"""

    name: Optional[str] = None
    external_id: Optional[str] = Field(None, alias="externalId")
    type: Optional[CompanyType] = None
    size: Optional[CompanySize] = None
    industry_id: Optional[str] = Field(None, alias="industryId")
    okved: Optional[str] = None
    benefits: Optional[list[CompanyBenefit]] = None
    public_links: Optional[list[CompanyLink]] = Field(None, alias="publicLinks")

    class Config:
        populate_by_name = True


class VacancyClassification(BaseModel):
    """Детальная классификация позиции"""

    business_function: Optional[BusinessFunction] = Field(None, alias="businessFunction")
    role_family: Optional[RoleFamily] = Field(None, alias="roleFamily")
    org_level: Optional[OrgLevel] = Field(None, alias="orgLevel")
    business_model: Optional[BusinessModel] = Field(None, alias="businessModel")
    project_type: Optional[str] = Field(None, alias="projectType")

    class Config:
        populate_by_name = True


class VacancyWorkConditions(BaseModel):
    """Условия работы: формат, график и компенсация"""

    employment_type: Optional[EmploymentTypeInfo] = Field(None, alias="employmentType")
    schedule: Optional[ScheduleInfo] = None
    work_hours: Optional[str] = Field(None, alias="workHours")
    salary: Optional[Salary] = None
    location: Optional[Location] = None

    class Config:
        populate_by_name = True


class VacancyRequirements(BaseModel):
    """Требования к кандидату"""

    education: Optional[Education] = None
    experience: Optional[Experience] = None
    skills: Optional[list[Skill]] = None
    languages: Optional[list[Language]] = None


class VacancyResponsibilities(BaseModel):
    """Обязанности и зоны ответственности"""

    scope: Optional[str] = None
    zones: Optional[list[str]] = None
    competency_model: Optional[str] = Field(None, alias="competencyModel")
    business_processes: Optional[list[BusinessProcess]] = Field(None, alias="businessProcesses")

    class Config:
        populate_by_name = True


class VacancyOrgStructure(BaseModel):
    """Место роли в оргструктуре"""

    reports_to: Optional[str] = Field(None, alias="reportsTo")
    subordinates_count: Optional[int] = Field(None, ge=0, alias="subordinatesCount")
    org_unit: Optional[str] = Field(None, alias="orgUnit")
    team_roles: Optional[list[str]] = Field(None, alias="teamRoles")
    cross_functional_links: Optional[list[str]] = Field(None, alias="crossFunctionalLinks")

    class Config:
        populate_by_name = True


class VacancyFullText(BaseModel):
    """Полный текст вакансии (версионируемый)"""

    text: Optional[str] = None
    source: Optional[TextSource] = None


class VacancyMetadata(BaseModel):
    """Метаданные вакансии"""

    status: Optional[VacancyStatus] = VacancyStatus.DRAFT
    priority: Optional[Priority] = None
    deadline: Optional[str] = None
    tags: Optional[list[str]] = None


# ============ MAIN MODEL ============


class VacancyInput(BaseModel):
    """
    Полная структура входных параметров вакансии.
    Рассчитана на поиск редких и узкоспециализированных специалистов.
    """

    core: VacancyCore = Field(..., description="Ядро вакансии (обязательный блок)")
    company: Optional[VacancyCompany] = None
    classification: Optional[VacancyClassification] = None
    work_conditions: Optional[VacancyWorkConditions] = Field(None, alias="workConditions")
    requirements: Optional[VacancyRequirements] = None
    responsibilities: Optional[VacancyResponsibilities] = None
    org_structure: Optional[VacancyOrgStructure] = Field(None, alias="orgStructure")
    full_text: Optional[VacancyFullText] = Field(None, alias="fullText")
    metadata: Optional[VacancyMetadata] = None

    class Config:
        populate_by_name = True


# ============ API MODELS ============


class ParseVacancyRequest(BaseModel):
    """Запрос на парсинг текста вакансии"""

    text: str = Field(..., min_length=50, description="Исходный текст вакансии для парсинга")
    hints: Optional[dict[str, str]] = Field(
        None, description="Опциональные подсказки (company_name, industry)"
    )


class ParseVacancyResponse(BaseModel):
    """Ответ с распарсенной вакансией"""

    data: VacancyInput = Field(..., description="Распарсенные данные")
    confidence: float = Field(..., ge=0, le=1, description="Уверенность парсера (0-1)")
    warnings: Optional[list[str]] = Field(None, description="Предупреждения при парсинге")
    missing_fields: Optional[list[str]] = Field(
        None, alias="missingFields", description="Поля, которые не удалось извлечь"
    )

    class Config:
        populate_by_name = True
