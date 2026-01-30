/**
 * Типы для входных параметров вакансии
 * Сгенерировано из schemas/vacancy-input.schema.json
 * Используется для парсинга текста вакансии через LLM
 */

// ============ ENUMS ============

export type CareerLevelCode =
  | "intern"
  | "junior"
  | "middle"
  | "senior"
  | "lead"
  | "head"
  | "director"
  | "c-level";

export type OrgLevelCode =
  | "ic"
  | "team_lead"
  | "manager"
  | "senior_manager"
  | "director"
  | "vp"
  | "c_level";

export type CompanyType =
  | "startup"
  | "sme"
  | "enterprise"
  | "corporation"
  | "government"
  | "ngo"
  | "consulting";

export type CompanySize =
  | "1-10"
  | "11-50"
  | "51-200"
  | "201-500"
  | "501-1000"
  | "1001-5000"
  | "5000+";

export type LinkType =
  | "site"
  | "hh"
  | "linkedin"
  | "habr"
  | "glassdoor"
  | "github"
  | "other";

export type EmploymentType =
  | "full-time"
  | "part-time"
  | "contract"
  | "freelance"
  | "internship"
  | "temporary";

export type ScheduleType =
  | "5/2"
  | "2/2"
  | "flexible"
  | "shift"
  | "remote-async"
  | "hybrid";

export type Currency =
  | "RUB"
  | "USD"
  | "EUR"
  | "GBP"
  | "KZT"
  | "BYN"
  | "UAH"
  | "GEL"
  | "AMD"
  | "AZN";

export type SalaryPeriod = "month" | "year" | "hour" | "project";

export type RemoteType = "office" | "remote" | "hybrid" | "relocate";

export type EducationLevel =
  | "any"
  | "secondary"
  | "bachelor"
  | "master"
  | "phd"
  | "mba";

export type SkillCategory = "hard" | "soft" | "management" | "digital_tool";

export type SkillLevel = "basic" | "intermediate" | "advanced" | "expert";

export type LanguageProficiency =
  | "A1"
  | "A2"
  | "B1"
  | "B2"
  | "C1"
  | "C2"
  | "native";

export type VacancyStatus =
  | "draft"
  | "review"
  | "active"
  | "paused"
  | "closed"
  | "archived";

export type Priority = "low" | "medium" | "high" | "urgent";

export type TextSource = "manual" | "generated" | "imported";

export type BusinessSegment = "B2B" | "B2C" | "B2B2C" | "B2G" | "C2C" | "D2C";

// ============ EXECUTIVE SEARCH ENUMS ============

export type TriggerEventType =
  | "growth"
  | "replacement"
  | "new_direction"
  | "crisis"
  | "transformation"
  | "m_and_a"
  | "restructuring";

export type MilestoneTimeframe = "30_days" | "60_days" | "90_days";

export type ImpactType = "direct" | "indirect" | "enabling";

export type AchievementImportance = "must_have" | "strong_plus" | "nice_to_have";

export type CompetitorPolicy =
  | "actively_hire"
  | "neutral"
  | "avoid"
  | "strict_avoid";

export type MarketRarity =
  | "common"
  | "uncommon"
  | "rare"
  | "very_rare"
  | "unicorn";

export type CompetitionLevel = "low" | "medium" | "high" | "extreme";

export type SalaryCompetitiveness =
  | "below_market"
  | "market"
  | "above_market"
  | "top_of_market";

export type DecisionAuthorityLevel =
  | "none"
  | "advisory"
  | "recommend"
  | "influence"
  | "propose"
  | "manage"
  | "approval"
  | "approve"
  | "final";

export type CompanyStage =
  | "startup_early"
  | "startup_growth"
  | "scaleup"
  | "enterprise"
  | "turnaround"
  | "m_and_a";

// ============ NESTED INTERFACES ============

export interface CareerLevel {
  code?: CareerLevelCode;
  experienceYearsMin?: number;
  experienceYearsMax?: number;
}

export interface Industry {
  id?: string;
  name?: string;
  subIndustry?: string;
}

/** Элемент иерархии сферы деятельности */
export interface ActivitySphereItem {
  id?: string;
  name?: string;
}

/** Сфера деятельности компании (иерархическая структура) */
export interface ActivitySphere {
  /** Основная сфера деятельности */
  sphere?: ActivitySphereItem;
  /** Подсфера деятельности */
  subSphere?: ActivitySphereItem;
  /** Специализация */
  specialization?: ActivitySphereItem;
}

export interface CompanyLink {
  type: LinkType;
  url: string;
}

export interface BusinessFunction {
  id?: string;
  name?: string;
}

export interface RoleFamily {
  id?: string;
  name?: string;
}

export interface OrgLevel {
  code?: OrgLevelCode;
  name?: string;
}

export interface BusinessModel {
  id?: string;
  name?: string;
  segment?: BusinessSegment;
}

export interface EmploymentTypeInfo {
  id?: string;
  name?: EmploymentType;
}

export interface ScheduleInfo {
  id?: string;
  name?: ScheduleType;
}

export interface Salary {
  amountMin?: number;
  amountMax?: number;
  currency?: Currency;
  period?: SalaryPeriod;
  comment?: string;
}

export interface Location {
  city?: string;
  region?: string;
  country?: string;
  remote?: RemoteType;
  relocationSupport?: boolean;
  visaSupport?: boolean;
}

export interface Education {
  level?: EducationLevel;
  fields?: string[];
  comment?: string;
}

export interface Experience {
  yearsMin?: number;
  yearsMax?: number;
  domains?: string[];
  mustHave?: string[];
  niceToHave?: string[];
  /** Индикаторы масштаба опыта (Executive Search) */
  scaleIndicators?: ScaleIndicators;
  /** Контекстный опыт (Executive Search) */
  contextualExperience?: ContextualExperience;
}

export interface Skill {
  id?: string;
  name: string;
  category: SkillCategory;
  isRequired?: boolean;
  level?: SkillLevel;
  comment?: string;
}

export interface Language {
  id?: string;
  code?: string;
  name: string;
  proficiency?: LanguageProficiency;
  isRequired?: boolean;
}

export interface Subprocess {
  id?: string;
  name: string;
}

export interface BusinessProcess {
  id?: string;
  name: string;
  subprocesses?: Subprocess[];
}

// ============ EXECUTIVE SEARCH INTERFACES ============

/** Событие, послужившее причиной открытия вакансии */
export interface TriggerEvent {
  type?: TriggerEventType;
  description?: string;
}

/** Информация о предыдущих попытках закрыть вакансию */
export interface PreviousAttempts {
  hadAttempts?: boolean;
  duration?: string;
  candidatesSeen?: number;
  whyFailed?: string;
}

/** Milestone первых 90 дней */
export interface OnboardingMilestone {
  milestone?: string;
  timeframe?: MilestoneTimeframe;
  measureOfSuccess?: string;
}

/** KPI на 6 месяцев */
export interface ShortTermKPI {
  metric?: string;
  currentValue?: string;
  targetValue?: string;
}

/** Бизнес-метрика с типом влияния */
export interface BusinessMetric {
  metric?: string;
  impactType?: ImpactType;
  description?: string;
}

/** Требуемая отраслевая экспертиза */
export interface IndustryExpertise {
  industries?: string[];
  whyMatters?: string;
  regulatoryKnowledge?: string[];
}

/** Требование по размеру команды */
export interface TeamSizeRequirement {
  min?: number;
  description?: string;
}

/** Требование по бюджету */
export interface BudgetRequirement {
  min?: string;
  currency?: string;
}

/** Опыт работы с определённым масштабом */
export interface ScaleExperience {
  teamSize?: TeamSizeRequirement;
  budget?: BudgetRequirement;
  dataVolume?: string;
  usersScale?: string;
  revenueImpact?: string;
}

/** Маркер достижения */
export interface AchievementMarker {
  achievement?: string;
  importance?: AchievementImportance;
}

/** Предпочтительный бэкграунд по типам компаний */
export interface CompanyBackground {
  preferred?: string[];
  reasoning?: string;
}

/** Культурные маркеры и стиль работы */
export interface CulturalFit {
  workStyle?: string[];
  leadershipStyle?: string[];
  environment?: string[];
}

/** Абсолютное требование без исключений */
export interface AbsoluteRequirement {
  requirement?: string;
  reason?: string;
}

/** Минимальные пороги опыта */
export interface ExperienceMinimums {
  totalYears?: number;
  domainYears?: number;
  leadershipYears?: number;
  specificExperience?: string[];
}

/** Политика по отношению к кандидатам из конкурентов */
export interface CompetitorPolicyInfo {
  policy?: CompetitorPolicy;
  companies?: string[];
  reason?: string;
}

/** Критическая задача первых 90 дней */
export interface CriticalTask {
  task?: string;
  deadline?: string;
  successIndicator?: string;
}

/** Уровни полномочий в принятии решений */
export interface DecisionAuthorityLevels {
  technical?: DecisionAuthorityLevel;
  hiring?: DecisionAuthorityLevel;
  budget?: DecisionAuthorityLevel;
}

/** Информация об управлении командой */
export interface TeamManagement {
  directReports?: string;
  totalTeam?: string;
}

/** Индикаторы масштаба опыта */
export interface ScaleIndicators {
  teamManagement?: TeamManagement;
  budgetManagement?: string;
  projectScale?: string;
  businessImpact?: string;
}

/** Контекстный опыт */
export interface ContextualExperience {
  companyStages?: CompanyStage[];
  situations?: string[];
}

// ============ MAIN BLOCKS ============

/**
 * Ядро вакансии (обязательный блок)
 * Минимально необходимая информация для создания вакансии
 */
export interface VacancyCore {
  /** Название должности/роли. Ключевой параметр. */
  jobTitle: string;
  /** Альтернативные названия роли для расширения поиска */
  synonyms?: string[];
  /** Уровень позиции в карьерной иерархии */
  careerLevel?: CareerLevel;
  /** Отрасль/индустрия */
  industry?: Industry;
}

/**
 * Информация о компании-работодателе
 * Если name заполнено — все вложенные поля доступны
 */
export interface VacancyCompany {
  /** Название компании */
  name?: string;
  /** Внешний идентификатор компании */
  externalId?: string;
  /** Тип компании */
  type?: CompanyType;
  /** Размер компании по количеству сотрудников */
  size?: CompanySize;
  /** ID отрасли компании */
  industryId?: string;
  /** Код ОКВЭД */
  okved?: string;
  /** Сфера деятельности компании (иерархическая) */
  activitySphere?: ActivitySphere;
  /** Публичные ссылки компании */
  publicLinks?: CompanyLink[];
}

/**
 * Детальная классификация позиции
 */
export interface VacancyClassification {
  /** Бизнес-функция (IT, Finance, HR, Marketing и т.д.) */
  businessFunction?: BusinessFunction;
  /** Семейство ролей (Engineering, Management, Analytics и т.д.) */
  roleFamily?: RoleFamily;
  /** Организационный уровень */
  orgLevel?: OrgLevel;
  /** Бизнес-модель компании/продукта */
  businessModel?: BusinessModel;
  /** Тип проекта (продукт, аутсорс, аутстафф, стартап, R&D и т.д.) */
  projectType?: string;
}

/**
 * Условия работы: формат, график и компенсация
 */
export interface VacancyWorkConditions {
  /** Тип занятости */
  employmentType?: EmploymentTypeInfo;
  /** График работы */
  schedule?: ScheduleInfo;
  /** Часы/окно работы */
  workHours?: string;
  /** Компенсация */
  salary?: Salary;
  /** Локация */
  location?: Location;
}

/**
 * Требования к кандидату
 */
export interface VacancyRequirements {
  /** Требования к образованию */
  education?: Education;
  /** Требования к опыту */
  experience?: Experience;
  /** Навыки и компетенции */
  skills?: Skill[];
  /** Требования к языкам */
  languages?: Language[];
}

/**
 * Обязанности и зоны ответственности (расширено для Executive Search)
 */
export interface VacancyResponsibilities {
  /** Общее описание зоны ответственности */
  scope?: string;
  /** Конкретные зоны ответственности */
  zones?: string[];
  /** Критические задачи первых 90 дней (Executive Search) */
  criticalTasks?: CriticalTask[];
  /** Процессы, которыми будет владеть (Executive Search) */
  processOwnership?: string[];
  /** Уровень полномочий в принятии решений (Executive Search) */
  decisionAuthority?: DecisionAuthorityLevels;
  /** Модель компетенций */
  competencyModel?: string;
  /** Бизнес-процессы (двухуровневая иерархия) */
  businessProcesses?: BusinessProcess[];
}

/**
 * Место роли в оргструктуре
 */
export interface VacancyOrgStructure {
  /** Кому подчиняется (название роли) */
  reportsTo?: string;
  /** Количество подчинённых (0 = IC) */
  subordinatesCount?: number;
  /** Название подразделения/отдела */
  orgUnit?: string;
  /** Роли в команде */
  teamRoles?: string[];
  /** Кросс-функциональные взаимодействия */
  crossFunctionalLinks?: string[];
}

// ============ EXECUTIVE SEARCH BLOCKS ============

/**
 * Контекст найма (Executive Search)
 * КРИТИЧЕСКИЙ БЛОК: определяет ЗАЧЕМ нужен этот человек
 */
export interface HiringContext {
  /** Что послужило причиной открытия вакансии */
  triggerEvent?: TriggerEvent;
  /** Какую бизнес-проблему должен решить */
  businessProblem?: string;
  /** Какой результат ожидается от найма */
  expectedImpact?: string;
  /** Почему срочно */
  urgencyReason?: string;
  /** Были ли попытки закрыть раньше */
  previousAttempts?: PreviousAttempts;
  /** Ожидания ключевых стейкхолдеров */
  stakeholderExpectations?: string;
}

/**
 * Критерии успеха и KPI
 * Измеримые критерии, по которым оценим успех найма
 */
export interface SuccessCriteria {
  /** Milestones первых 90 дней */
  onboardingMilestones?: OnboardingMilestone[];
  /** KPI на 6 месяцев */
  shortTermKPIs?: ShortTermKPI[];
  /** Стратегические цели на 1+ год */
  longTermGoals?: string[];
  /** Бизнес-метрики */
  businessMetrics?: BusinessMetric[];
  /** Качественные ожидания */
  qualitativeExpectations?: string;
}

/**
 * Дифференцирующие критерии
 * Что отличает ИДЕАЛЬНОГО кандидата от просто подходящего
 */
export interface Differentiators {
  /** Требуемая отраслевая экспертиза */
  industryExpertise?: IndustryExpertise;
  /** Знание специфических доменов */
  domainKnowledge?: string[];
  /** Опыт работы с определённым масштабом */
  scaleExperience?: ScaleExperience;
  /** Конкретные достижения */
  achievementMarkers?: AchievementMarker[];
  /** Предпочтительный бэкграунд */
  companyBackground?: CompanyBackground;
  /** Ценность нетворка */
  networkValue?: string;
  /** Культурные маркеры */
  culturalFit?: CulturalFit;
}

/**
 * Критические отсечки (Dealbreakers)
 * Чёткие критерии отсечения кандидатов
 */
export interface Dealbreakers {
  /** Абсолютные требования */
  absoluteRequirements?: AbsoluteRequirement[];
  /** Минимальные пороги опыта */
  experienceMinimums?: ExperienceMinimums;
  /** Что точно НЕ подходит */
  redFlags?: string[];
  /** Политика по конкурентам */
  competitorPolicy?: CompetitorPolicyInfo;
  /** Требования, которые не обсуждаются */
  nonNegotiables?: string[];
}

/**
 * Оценка сложности поиска
 * Автоматически рассчитываемая оценка сложности закрытия позиции
 */
export interface SearchDifficulty {
  /** Редкость специалиста на рынке */
  marketRarity?: MarketRarity;
  /** Примерный размер пула кандидатов */
  estimatedPool?: string;
  /** Уровень конкуренции */
  competitionLevel?: CompetitionLevel;
  /** Конкурентоспособность зарплаты */
  salaryCompetitiveness?: SalaryCompetitiveness;
  /** Рекомендуемая стратегия поиска */
  recommendedStrategy?: string;
  /** Примерная оценка времени закрытия */
  timeToHireEstimate?: string;
  /** Факторы риска */
  riskFactors?: string[];
}

/**
 * Полный текст вакансии (версионируемый)
 */
export interface VacancyFullText {
  /** Полный текст описания вакансии */
  text?: string;
  /** Источник текста */
  source?: TextSource;
}

/**
 * Метаданные вакансии
 */
export interface VacancyMetadata {
  /** Статус вакансии */
  status?: VacancyStatus;
  /** Приоритет закрытия */
  priority?: Priority;
  /** Желаемая дата закрытия */
  deadline?: string;
  /** Теги для внутренней классификации */
  tags?: string[];
}

// ============ MAIN TYPE ============

/**
 * Полная структура входных параметров вакансии
 * Рассчитана на Executive Search - поиск редких и узкоспециализированных специалистов
 */
export interface VacancyInput {
  /** Ядро вакансии (обязательный блок) */
  core: VacancyCore;
  /** Информация о компании */
  company?: VacancyCompany;
  /** Классификация позиции */
  classification?: VacancyClassification;
  /** Условия работы */
  workConditions?: VacancyWorkConditions;
  /** Требования к кандидату */
  requirements?: VacancyRequirements;
  /** Обязанности и зоны ответственности */
  responsibilities?: VacancyResponsibilities;
  /** Организационная структура */
  orgStructure?: VacancyOrgStructure;
  // ============ EXECUTIVE SEARCH БЛОКИ ============
  /** Контекст найма (КРИТИЧНО для executive search) */
  hiringContext?: HiringContext;
  /** Критерии успеха и KPI */
  successCriteria?: SuccessCriteria;
  /** Дифференцирующие критерии (что отличает идеального кандидата) */
  differentiators?: Differentiators;
  /** Критические отсечки */
  dealbreakers?: Dealbreakers;
  /** Оценка сложности поиска (авто-расчёт) */
  searchDifficulty?: SearchDifficulty;
  /** Полный текст вакансии */
  fullText?: VacancyFullText;
  /** Метаданные */
  metadata?: VacancyMetadata;
}

// ============ API TYPES ============

/**
 * Запрос на парсинг текста вакансии
 */
export interface ParseVacancyRequest {
  /** Исходный текст вакансии для парсинга */
  text: string;
  /** Опциональные подсказки для парсера */
  hints?: {
    companyName?: string;
    industry?: string;
  };
}

/**
 * Ответ с распарсенной вакансией
 */
export interface ParseVacancyResponse {
  /** Распарсенные данные */
  data: VacancyInput;
  /** Уверенность парсера (0-1) */
  confidence: number;
  /** Предупреждения при парсинге */
  warnings?: string[];
  /** Поля, которые не удалось извлечь */
  missingFields?: string[];
}

/**
 * Ошибка API
 */
export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}
