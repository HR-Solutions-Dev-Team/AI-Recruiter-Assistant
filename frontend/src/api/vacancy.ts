/**
 * API для работы с вакансиями.
 */

import { apiClient } from './client';
import type { VacancyInput } from '../types/vacancy';

export interface CreateSessionResponse {
  session_id: string;
  status: string;
}

export interface ParseResponse {
  session_id: string;
  status: string;
  completion_percent: number;
  parsed_data: VacancyInput | null;
  confidence: number;
  warnings: string[] | null;
  missing_fields: string[] | null;
  is_valid: boolean;
  validation_error: string | null;
}

export interface SessionResponse {
  session_id: string;
  status: string;
  completion_percent: number;
  parsed_data: VacancyInput | null;
  confidence: number | null;
  warnings: string[] | null;
  missing_fields: string[] | null;
}

export interface EnrichmentOption {
  value: string;
  description: string | null;
}

export interface EnrichmentQuestion {
  field_path: string;
  question_text: string;
  options: EnrichmentOption[];
  allow_custom: boolean;
  has_more_questions: boolean;
}

export interface QuestionCategory {
  key: string;
  name: string;
  description: string;
  fields_count: number;
}

export interface NextQuestionResponse {
  questions: EnrichmentQuestion[];
  is_complete: boolean;
  completion_percent: number;
  available_categories?: QuestionCategory[];
}

export interface SubmitAnswerResponse {
  success: boolean;
  completion_percent: number;
  updated_field: string | null;
  // Буфер: до 2 вопросов за раз
  next_questions: EnrichmentQuestion[];
  is_complete: boolean;
}

export interface BatchAnswerItem {
  field_path: string;
  answer: string;
  skip: boolean;
  question_text?: string;  // Для сохранения в Q-A историю
}

export interface BatchAnswerResponse {
  success: boolean;
  completion_percent: number;
  processed_count: number;
  next_questions: EnrichmentQuestion[];
  is_complete: boolean;
}

export interface CalculateWeightsResponse {
  weights: Record<string, number>;  // баллы 0-10 для каждой категории
}

// ============ Vacancy CRUD Types ============

export interface VacancyListItem {
  id: number;
  job_title: string;
  company_name: string | null;
  location_city: string | null;
  status: string;
  salary_min: number | null;
  salary_max: number | null;
  salary_currency: string;
  created_at: string;
}

export interface VacancyListResponse {
  items: VacancyListItem[];
  total: number;
  skip: number;
  limit: number;
}

export interface SaveVacancyRequest {
  session_id: string;
  weights?: Record<string, number>;
}

export interface SaveVacancyResponse {
  id: number;
  job_title: string;
  status: string;
  message: string;
}

/**
 * Создать новую сессию для создания вакансии.
 */
export async function createSession(): Promise<CreateSessionResponse> {
  return apiClient.post<CreateSessionResponse>('/v1/vacancy/session', {});
}

/**
 * Получить текущее состояние сессии.
 */
export async function getSession(sessionId: string): Promise<SessionResponse> {
  return apiClient.get<SessionResponse>(`/v1/vacancy/session/${sessionId}`);
}

/**
 * Загрузить текст вакансии и распарсить его.
 */
export async function uploadText(
  sessionId: string,
  text: string,
  hints?: { company_name?: string; industry?: string }
): Promise<ParseResponse> {
  return apiClient.post<ParseResponse>(
    `/v1/vacancy/session/${sessionId}/upload-text`,
    { text, hints }
  );
}

/**
 * Загрузить файл вакансии и распарсить его.
 */
export async function uploadFile(
  sessionId: string,
  file: File,
  hints?: { company_name?: string; industry?: string }
): Promise<ParseResponse> {
  const formData = new FormData();
  formData.append('file', file);
  if (hints) {
    formData.append('hints', JSON.stringify(hints));
  }

  return apiClient.postFormData<ParseResponse>(
    `/v1/vacancy/session/${sessionId}/upload-file`,
    formData
  );
}

/**
 * Удалить сессию.
 */
export async function deleteSession(sessionId: string): Promise<void> {
  await apiClient.delete(`/v1/vacancy/session/${sessionId}`);
}

/**
 * Получить список доступных категорий вопросов.
 */
export async function getEnrichmentCategories(): Promise<QuestionCategory[]> {
  return apiClient.get<QuestionCategory[]>('/v1/vacancy/enrichment/categories');
}

/**
 * Получить следующие вопросы для обогащения вакансии.
 */
export async function getNextQuestion(
  sessionId: string,
  priorityCategories?: string[]
): Promise<NextQuestionResponse> {
  return apiClient.post<NextQuestionResponse>(
    `/v1/vacancy/session/${sessionId}/enrichment/next-question`,
    { priority_categories: priorityCategories }
  );
}

/**
 * Отправить ответ на вопрос обогащения.
 */
export async function submitAnswer(
  sessionId: string,
  fieldPath: string,
  answer: string,
  skip: boolean = false,
  questionText?: string
): Promise<SubmitAnswerResponse> {
  return apiClient.post<SubmitAnswerResponse>(
    `/v1/vacancy/session/${sessionId}/enrichment/answer`,
    { field_path: fieldPath, answer, skip, question_text: questionText }
  );
}

/**
 * Отправить пачку ответов за один запрос.
 * Используется когда буфер вопросов опустеет.
 */
export async function batchSubmitAnswers(
  sessionId: string,
  answers: BatchAnswerItem[],
  priorityCategories?: string[]
): Promise<BatchAnswerResponse> {
  return apiClient.post<BatchAnswerResponse>(
    `/v1/vacancy/session/${sessionId}/enrichment/batch-answer`,
    { answers, priority_categories: priorityCategories }
  );
}

/**
 * Рассчитать веса критериев отбора для вакансии через LLM.
 * Вызывается при переходе на EditStep после завершения ChatStep.
 */
export async function calculateWeights(
  sessionId: string
): Promise<CalculateWeightsResponse> {
  return apiClient.post<CalculateWeightsResponse>(
    `/v1/vacancy/session/${sessionId}/calculate-weights`,
    {}
  );
}

// ============ Vacancy CRUD Functions ============

/**
 * Получить список вакансий из БД.
 */
export async function getVacancies(
  skip: number = 0,
  limit: number = 50,
  status?: string
): Promise<VacancyListResponse> {
  let url = `/v1/vacancy?skip=${skip}&limit=${limit}`;
  if (status) {
    url += `&status=${status}`;
  }
  return apiClient.get<VacancyListResponse>(url);
}

/**
 * Получить одну вакансию по ID.
 */
export async function getVacancy(id: number): Promise<VacancyInput> {
  return apiClient.get<VacancyInput>(`/v1/vacancy/${id}`);
}

/**
 * Сохранить вакансию из сессии в БД.
 */
export async function saveVacancy(
  sessionId: string,
  weights?: Record<string, number>
): Promise<SaveVacancyResponse> {
  return apiClient.post<SaveVacancyResponse>('/v1/vacancy', {
    session_id: sessionId,
    weights,
  });
}

/**
 * Удалить вакансию.
 */
export async function deleteVacancy(id: number): Promise<void> {
  await apiClient.delete(`/v1/vacancy/${id}`);
}
