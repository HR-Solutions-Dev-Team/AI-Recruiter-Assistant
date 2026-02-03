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


# ============ EXECUTIVE SEARCH ENUMS ============


class TriggerEventType(str, Enum):
    """Тип события, послужившего причиной открытия вакансии"""

    GROWTH = "growth"
    REPLACEMENT = "replacement"
    NEW_DIRECTION = "new_direction"
    CRISIS = "crisis"
    TRANSFORMATION = "transformation"
    M_AND_A = "m_and_a"
    RESTRUCTURING = "restructuring"


class MilestoneTimeframe(str, Enum):
    """Временные рамки для milestones"""

    DAYS_30 = "30_days"
    DAYS_60 = "60_days"
    DAYS_90 = "90_days"


class ImpactType(str, Enum):
    """Тип влияния на метрику"""

    DIRECT = "direct"
    INDIRECT = "indirect"
    ENABLING = "enabling"


class AchievementImportance(str, Enum):
    """Важность достижения"""

    MUST_HAVE = "must_have"
    STRONG_PLUS = "strong_plus"
    NICE_TO_HAVE = "nice_to_have"


class CompetitorPolicy(str, Enum):
    """Политика по отношению к кандидатам из конкурентов"""

    ACTIVELY_HIRE = "actively_hire"
    NEUTRAL = "neutral"
    AVOID = "avoid"
    STRICT_AVOID = "strict_avoid"


class MarketRarity(str, Enum):
    """Редкость специалиста на рынке"""

    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    VERY_RARE = "very_rare"
    UNICORN = "unicorn"


class CompetitionLevel(str, Enum):
    """Уровень конкуренции за специалиста"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"


class SalaryCompetitiveness(str, Enum):
    """Конкурентоспособность зарплаты"""

    BELOW_MARKET = "below_market"
    MARKET = "market"
    ABOVE_MARKET = "above_market"
    TOP_OF_MARKET = "top_of_market"


class DecisionAuthority(str, Enum):
    """Уровень полномочий в принятии решений"""

    NONE = "none"
    ADVISORY = "advisory"
    RECOMMEND = "recommend"
    INFLUENCE = "influence"
    PROPOSE = "propose"
    MANAGE = "manage"
    APPROVAL = "approval"
    APPROVE = "approve"
    FINAL = "final"


class CompanyStage(str, Enum):
    """Стадия компании"""

    STARTUP_EARLY = "startup_early"
    STARTUP_GROWTH = "startup_growth"
    SCALEUP = "scaleup"
    ENTERPRISE = "enterprise"
    TURNAROUND = "turnaround"
    M_AND_A = "m_and_a"


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


class ActivitySphereItem(BaseModel):
    """Элемент иерархии сферы деятельности"""

    id: Optional[str] = None
    name: Optional[str] = None


class ActivitySphere(BaseModel):
    """Сфера деятельности компании (иерархическая структура)"""

    sphere: Optional[ActivitySphereItem] = Field(None, description="Основная сфера деятельности")
    sub_sphere: Optional[ActivitySphereItem] = Field(None, alias="subSphere", description="Подсфера деятельности")
    specialization: Optional[ActivitySphereItem] = Field(None, description="Специализация")

    class Config:
        populate_by_name = True


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


class TeamManagement(BaseModel):
    """Информация об управлении командой"""

    direct_reports: Optional[str] = Field(None, alias="directReports")
    total_team: Optional[str] = Field(None, alias="totalTeam")

    class Config:
        populate_by_name = True


class ScaleIndicators(BaseModel):
    """Индикаторы масштаба опыта"""

    team_management: Optional[TeamManagement] = Field(None, alias="teamManagement")
    budget_management: Optional[str] = Field(None, alias="budgetManagement")
    project_scale: Optional[str] = Field(None, alias="projectScale")
    business_impact: Optional[str] = Field(None, alias="businessImpact")

    class Config:
        populate_by_name = True


class ContextualExperience(BaseModel):
    """Контекстный опыт"""

    company_stages: Optional[list[CompanyStage]] = Field(None, alias="companyStages")
    situations: Optional[list[str]] = None

    class Config:
        populate_by_name = True


class Experience(BaseModel):
    """Требования к опыту. Расширен для executive search."""

    years_min: Optional[int] = Field(None, ge=0, alias="yearsMin")
    years_max: Optional[int] = Field(None, ge=0, alias="yearsMax")
    domains: Optional[list[str]] = None
    must_have: Optional[list[str]] = Field(None, alias="mustHave")
    nice_to_have: Optional[list[str]] = Field(None, alias="niceToHave")
    # Executive Search расширения
    scale_indicators: Optional[ScaleIndicators] = Field(
        None, alias="scaleIndicators", description="Индикаторы масштаба опыта"
    )
    contextual_experience: Optional[ContextualExperience] = Field(
        None, alias="contextualExperience", description="Контекстный опыт"
    )

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


# ============ EXECUTIVE SEARCH NESTED MODELS ============


class TriggerEvent(BaseModel):
    """Событие, послужившее причиной открытия вакансии"""

    type: Optional[TriggerEventType] = None
    description: Optional[str] = None


class PreviousAttempts(BaseModel):
    """Информация о предыдущих попытках закрыть вакансию"""

    had_attempts: Optional[bool] = Field(None, alias="hadAttempts")
    duration: Optional[str] = None
    candidates_seen: Optional[int] = Field(None, alias="candidatesSeen")
    why_failed: Optional[str] = Field(None, alias="whyFailed")

    class Config:
        populate_by_name = True


class OnboardingMilestone(BaseModel):
    """Milestone первых 90 дней"""

    milestone: Optional[str] = None
    timeframe: Optional[MilestoneTimeframe] = None
    measure_of_success: Optional[str] = Field(None, alias="measureOfSuccess")

    class Config:
        populate_by_name = True


class ShortTermKPI(BaseModel):
    """KPI на 6 месяцев"""

    metric: Optional[str] = None
    current_value: Optional[str] = Field(None, alias="currentValue")
    target_value: Optional[str] = Field(None, alias="targetValue")

    class Config:
        populate_by_name = True


class BusinessMetric(BaseModel):
    """Бизнес-метрика с типом влияния"""

    metric: Optional[str] = None
    impact_type: Optional[ImpactType] = Field(None, alias="impactType")
    description: Optional[str] = None

    class Config:
        populate_by_name = True


class IndustryExpertise(BaseModel):
    """Требуемая отраслевая экспертиза"""

    industries: Optional[list[str]] = None
    why_matters: Optional[str] = Field(None, alias="whyMatters")
    regulatory_knowledge: Optional[list[str]] = Field(None, alias="regulatoryKnowledge")

    class Config:
        populate_by_name = True


class TeamSizeRequirement(BaseModel):
    """Требование по размеру команды"""

    min: Optional[int] = None
    description: Optional[str] = None


class BudgetRequirement(BaseModel):
    """Требование по бюджету"""

    min: Optional[str] = None
    currency: Optional[str] = None


class ScaleExperience(BaseModel):
    """Опыт работы с определённым масштабом"""

    team_size: Optional[TeamSizeRequirement] = Field(None, alias="teamSize")
    budget: Optional[BudgetRequirement] = None
    data_volume: Optional[str] = Field(None, alias="dataVolume")
    users_scale: Optional[str] = Field(None, alias="usersScale")
    revenue_impact: Optional[str] = Field(None, alias="revenueImpact")

    class Config:
        populate_by_name = True


class AchievementMarker(BaseModel):
    """Маркер достижения"""

    achievement: Optional[str] = None
    importance: Optional[AchievementImportance] = None


class CompanyBackground(BaseModel):
    """Предпочтительный бэкграунд по типам компаний"""

    preferred: Optional[list[str]] = None
    reasoning: Optional[str] = None


class CulturalFit(BaseModel):
    """Культурные маркеры и стиль работы"""

    work_style: Optional[list[str]] = Field(None, alias="workStyle")
    leadership_style: Optional[list[str]] = Field(None, alias="leadershipStyle")
    environment: Optional[list[str]] = None

    class Config:
        populate_by_name = True


class AbsoluteRequirement(BaseModel):
    """Абсолютное требование без исключений"""

    requirement: Optional[str] = None
    reason: Optional[str] = None


class ExperienceMinimums(BaseModel):
    """Минимальные пороги опыта"""

    total_years: Optional[int] = Field(None, alias="totalYears")
    domain_years: Optional[int] = Field(None, alias="domainYears")
    leadership_years: Optional[int] = Field(None, alias="leadershipYears")
    specific_experience: Optional[list[str]] = Field(None, alias="specificExperience")

    class Config:
        populate_by_name = True


class CompetitorPolicyInfo(BaseModel):
    """Политика по отношению к кандидатам из конкурентов"""

    policy: Optional[CompetitorPolicy] = None
    companies: Optional[list[str]] = None
    reason: Optional[str] = None


class CriticalTask(BaseModel):
    """Критическая задача первых 90 дней"""

    task: Optional[str] = None
    deadline: Optional[str] = None
    success_indicator: Optional[str] = Field(None, alias="successIndicator")

    class Config:
        populate_by_name = True


class DecisionAuthorityLevels(BaseModel):
    """Уровни полномочий в принятии решений"""

    technical: Optional[DecisionAuthority] = None
    hiring: Optional[DecisionAuthority] = None
    budget: Optional[DecisionAuthority] = None


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
    activity_sphere: Optional[ActivitySphere] = Field(None, alias="activitySphere")
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
    """Обязанности и зоны ответственности. Расширен для executive search."""

    scope: Optional[str] = None
    zones: Optional[list[str]] = None
    # Executive Search расширения
    critical_tasks: Optional[list[CriticalTask]] = Field(
        None, alias="criticalTasks", description="Критические задачи первых 90 дней"
    )
    process_ownership: Optional[list[str]] = Field(
        None, alias="processOwnership", description="Процессы, которыми будет владеть"
    )
    decision_authority: Optional[DecisionAuthorityLevels] = Field(
        None, alias="decisionAuthority", description="Уровень полномочий в принятии решений"
    )
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


# ============ EXECUTIVE SEARCH BLOCKS ============


class HiringContext(BaseModel):
    """
    Контекст найма (Executive Search).
    КРИТИЧЕСКИЙ БЛОК: определяет ЗАЧЕМ нужен этот человек, а не просто КТО нужен.
    """

    trigger_event: Optional[TriggerEvent] = Field(
        None, alias="triggerEvent", description="Что послужило причиной открытия вакансии"
    )
    business_problem: Optional[str] = Field(
        None, alias="businessProblem", description="Какую бизнес-проблему должен решить"
    )
    expected_impact: Optional[str] = Field(
        None, alias="expectedImpact", description="Какой результат ожидается от найма"
    )
    urgency_reason: Optional[str] = Field(
        None, alias="urgencyReason", description="Почему срочно"
    )
    previous_attempts: Optional[PreviousAttempts] = Field(
        None, alias="previousAttempts", description="Были ли попытки закрыть раньше"
    )
    stakeholder_expectations: Optional[str] = Field(
        None, alias="stakeholderExpectations", description="Ожидания ключевых стейкхолдеров"
    )

    class Config:
        populate_by_name = True


class SuccessCriteria(BaseModel):
    """
    Критерии успеха и KPI.
    Измеримые критерии, по которым оценим успех найма.
    """

    onboarding_milestones: Optional[list[OnboardingMilestone]] = Field(
        None, alias="onboardingMilestones", description="Milestones первых 90 дней"
    )
    short_term_kpis: Optional[list[ShortTermKPI]] = Field(
        None, alias="shortTermKPIs", description="KPI на 6 месяцев"
    )
    long_term_goals: Optional[list[str]] = Field(
        None, alias="longTermGoals", description="Стратегические цели на 1+ год"
    )
    business_metrics: Optional[list[BusinessMetric]] = Field(
        None, alias="businessMetrics", description="Бизнес-метрики"
    )
    qualitative_expectations: Optional[str] = Field(
        None, alias="qualitativeExpectations", description="Качественные ожидания"
    )

    class Config:
        populate_by_name = True


class Differentiators(BaseModel):
    """
    Дифференцирующие критерии.
    Что отличает ИДЕАЛЬНОГО кандидата от просто подходящего.
    """

    industry_expertise: Optional[IndustryExpertise] = Field(
        None, alias="industryExpertise", description="Требуемая отраслевая экспертиза"
    )
    domain_knowledge: Optional[list[str]] = Field(
        None, alias="domainKnowledge", description="Знание специфических доменов"
    )
    scale_experience: Optional[ScaleExperience] = Field(
        None, alias="scaleExperience", description="Опыт работы с определённым масштабом"
    )
    achievement_markers: Optional[list[AchievementMarker]] = Field(
        None, alias="achievementMarkers", description="Конкретные достижения"
    )
    company_background: Optional[CompanyBackground] = Field(
        None, alias="companyBackground", description="Предпочтительный бэкграунд"
    )
    network_value: Optional[str] = Field(
        None, alias="networkValue", description="Ценность нетворка"
    )
    cultural_fit: Optional[CulturalFit] = Field(
        None, alias="culturalFit", description="Культурные маркеры"
    )

    class Config:
        populate_by_name = True


class Dealbreakers(BaseModel):
    """
    Критические отсечки (Dealbreakers).
    Чёткие критерии отсечения кандидатов.
    """

    absolute_requirements: Optional[list[AbsoluteRequirement]] = Field(
        None, alias="absoluteRequirements", description="Абсолютные требования"
    )
    experience_minimums: Optional[ExperienceMinimums] = Field(
        None, alias="experienceMinimums", description="Минимальные пороги опыта"
    )
    red_flags: Optional[list[str]] = Field(
        None, alias="redFlags", description="Что точно НЕ подходит"
    )
    competitor_policy: Optional[CompetitorPolicyInfo] = Field(
        None, alias="competitorPolicy", description="Политика по конкурентам"
    )
    non_negotiables: Optional[list[str]] = Field(
        None, alias="nonNegotiables", description="Требования, которые не обсуждаются"
    )

    class Config:
        populate_by_name = True


class SearchDifficulty(BaseModel):
    """
    Оценка сложности поиска.
    Автоматически рассчитываемая оценка сложности закрытия позиции.
    """

    market_rarity: Optional[MarketRarity] = Field(
        None, alias="marketRarity", description="Редкость специалиста на рынке"
    )
    estimated_pool: Optional[str] = Field(
        None, alias="estimatedPool", description="Примерный размер пула кандидатов"
    )
    competition_level: Optional[CompetitionLevel] = Field(
        None, alias="competitionLevel", description="Уровень конкуренции"
    )
    salary_competitiveness: Optional[SalaryCompetitiveness] = Field(
        None, alias="salaryCompetitiveness", description="Конкурентоспособность зарплаты"
    )
    recommended_strategy: Optional[str] = Field(
        None, alias="recommendedStrategy", description="Рекомендуемая стратегия поиска"
    )
    time_to_hire_estimate: Optional[str] = Field(
        None, alias="timeToHireEstimate", description="Примерная оценка времени закрытия"
    )
    risk_factors: Optional[list[str]] = Field(
        None, alias="riskFactors", description="Факторы риска"
    )

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
    Рассчитана на Executive Search - поиск редких и узкоспециализированных специалистов.
    """

    core: VacancyCore = Field(..., description="Ядро вакансии (обязательный блок)")
    company: Optional[VacancyCompany] = None
    classification: Optional[VacancyClassification] = None
    work_conditions: Optional[VacancyWorkConditions] = Field(None, alias="workConditions")
    requirements: Optional[VacancyRequirements] = None
    responsibilities: Optional[VacancyResponsibilities] = None
    org_structure: Optional[VacancyOrgStructure] = Field(None, alias="orgStructure")
    # Executive Search блоки
    hiring_context: Optional[HiringContext] = Field(
        None, alias="hiringContext", description="Контекст найма (КРИТИЧНО для executive search)"
    )
    success_criteria: Optional[SuccessCriteria] = Field(
        None, alias="successCriteria", description="Критерии успеха и KPI"
    )
    differentiators: Optional[Differentiators] = Field(
        None, description="Дифференцирующие критерии (что отличает идеального кандидата)"
    )
    dealbreakers: Optional[Dealbreakers] = Field(
        None, description="Критические отсечки"
    )
    search_difficulty: Optional[SearchDifficulty] = Field(
        None, alias="searchDifficulty", description="Оценка сложности поиска (авто-расчёт)"
    )
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

    data: Optional[VacancyInput] = Field(None, description="Распарсенные данные (None если невалидно)")
    confidence: float = Field(..., ge=0, le=1, description="Уверенность парсера (0-1)")
    warnings: Optional[list[str]] = Field(None, description="Предупреждения при парсинге")
    missing_fields: Optional[list[str]] = Field(
        None, alias="missingFields", description="Поля, которые не удалось извлечь"
    )
    is_valid: bool = Field(True, alias="isValid", description="Валидность документа как вакансии")
    validation_error: Optional[str] = Field(
        None, alias="validationError", description="Причина невалидности"
    )

    class Config:
        populate_by_name = True
