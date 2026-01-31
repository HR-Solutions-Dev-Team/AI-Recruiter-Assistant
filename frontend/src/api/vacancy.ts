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
  parsed_data: VacancyInput;
  confidence: number;
  warnings: string[] | null;
  missing_fields: string[] | null;
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

export interface NextQuestionResponse {
  questions: EnrichmentQuestion[];
  is_complete: boolean;
  completion_percent: number;
}

export interface SubmitAnswerResponse {
  success: boolean;
  completion_percent: number;
  updated_field: string | null;
  // Буфер: до 3 независимых вопросов за раз
  next_questions: EnrichmentQuestion[];
  is_complete: boolean;
}

export interface BatchAnswerItem {
  field_path: string;
  answer: string;
  skip: boolean;
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
 * Получить следующий вопрос для обогащения вакансии.
 */
export async function getNextQuestion(sessionId: string): Promise<NextQuestionResponse> {
  return apiClient.post<NextQuestionResponse>(
    `/v1/vacancy/session/${sessionId}/enrichment/next-question`,
    {}
  );
}

/**
 * Отправить ответ на вопрос обогащения.
 */
export async function submitAnswer(
  sessionId: string,
  fieldPath: string,
  answer: string,
  skip: boolean = false
): Promise<SubmitAnswerResponse> {
  return apiClient.post<SubmitAnswerResponse>(
    `/v1/vacancy/session/${sessionId}/enrichment/answer`,
    { field_path: fieldPath, answer, skip }
  );
}

/**
 * Отправить пачку ответов за один запрос.
 * Используется когда буфер вопросов опустеет.
 */
export async function batchSubmitAnswers(
  sessionId: string,
  answers: BatchAnswerItem[]
): Promise<BatchAnswerResponse> {
  return apiClient.post<BatchAnswerResponse>(
    `/v1/vacancy/session/${sessionId}/enrichment/batch-answer`,
    { answers }
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
