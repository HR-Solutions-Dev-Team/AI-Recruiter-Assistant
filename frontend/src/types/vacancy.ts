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
 * Обязанности и зоны ответственности
 */
export interface VacancyResponsibilities {
  /** Общее описание зоны ответственности */
  scope?: string;
  /** Конкретные зоны ответственности */
  zones?: string[];
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
 * Рассчитана на поиск редких и узкоспециализированных специалистов
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
