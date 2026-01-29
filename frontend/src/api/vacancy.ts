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
