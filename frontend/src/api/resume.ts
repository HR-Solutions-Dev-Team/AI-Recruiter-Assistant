/**
 * API для работы с резюме.
 */

import { apiClient } from './client';

// ============ Types ============

export interface ResumeUploadResponse {
  id: number;
  status: string;
  message: string;
  candidateName: string | null;
  desiredPosition: string | null;
  confidence: number;
}

export interface ResumeListItem {
  id: number;
  firstName: string | null;
  lastName: string | null;
  desiredPosition: string | null;
  city: string | null;
  email: string | null;
  phone: string | null;
  totalExperienceMonths: number | null;
  skillsCount: number;
  status: string;
  createdAt: string;
}

export interface ResumeListResponse {
  items: ResumeListItem[];
  total: number;
  skip: number;
  limit: number;
}

export interface InterviewQuestion {
  topic: string;
  question: string;
}

export interface CandidateMatch {
  resumeId: number;
  firstName: string | null;
  lastName: string | null;
  desiredPosition: string | null;
  city: string | null;
  email: string | null;
  phone: string | null;
  matchScore: number;
  interviewQuestions: InterviewQuestion[];
  gapsSummary: string[];
  strengthsSummary: string[];
}

export interface VacancyCandidatesResponse {
  vacancyId: number;
  vacancyTitle: string;
  candidates: CandidateMatch[];
  total: number;
}

export interface ResumeDetail {
  id: number;
  personal: {
    firstName: string | null;
    lastName: string | null;
    middleName: string | null;
    birthDate: string | null;
    gender: string | null;
  };
  contacts: {
    email: string | null;
    phone: string | null;
    telegram: string | null;
    linkedinUrl: string | null;
  } | null;
  desiredPosition: {
    title: string | null;
    salaryMin: number | null;
    salaryMax: number | null;
    salaryCurrency: string;
  };
  location: {
    city: string | null;
    region: string | null;
    country: string | null;
  };
  summary: string | null;
  totalExperienceMonths: number | null;
  experience: Array<{
    companyName: string;
    position: string;
    startDate: string | null;
    endDate: string | null;
    isCurrent: boolean;
    responsibilities: string | null;
    achievements: string | null;
  }>;
  education: Array<{
    institutionName: string;
    specialization: string | null;
    degree: string | null;
    endYear: number | null;
  }>;
  skills: Array<{
    name: string;
    category: string;
    level: string | null;
  }>;
  languages: Array<{
    name: string;
    proficiency: string | null;
  }>;
  status: string;
  createdAt: string;
}

// ============ API Functions ============

/**
 * Загрузить резюме (PDF, DOCX).
 */
export async function uploadResume(file: File): Promise<ResumeUploadResponse> {
  const formData = new FormData();
  formData.append('file', file);

  return apiClient.postFormData<ResumeUploadResponse>('/v1/resume/upload', formData);
}

/**
 * Получить список резюме.
 */
export async function getResumes(
  skip: number = 0,
  limit: number = 50,
  status?: string
): Promise<ResumeListResponse> {
  let url = `/v1/resume?skip=${skip}&limit=${limit}`;
  if (status) {
    url += `&status=${status}`;
  }
  return apiClient.get<ResumeListResponse>(url);
}

/**
 * Получить резюме по ID.
 */
export async function getResume(id: number): Promise<ResumeDetail> {
  return apiClient.get<ResumeDetail>(`/v1/resume/${id}`);
}

/**
 * Получить кандидатов для вакансии.
 */
export async function getVacancyCandidates(
  vacancyId: number,
  minScore: number = 0,
  limit: number = 50
): Promise<VacancyCandidatesResponse> {
  return apiClient.get<VacancyCandidatesResponse>(
    `/v1/vacancy/${vacancyId}/candidates?min_score=${minScore}&limit=${limit}`
  );
}

/**
 * Удалить резюме.
 */
export async function deleteResume(id: number): Promise<void> {
  await apiClient.delete(`/v1/resume/${id}`);
}
