/**
 * API клиент для взаимодействия с бэкендом.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

class ApiClient {
  private accessToken: string | null = null;
  private refreshToken: string | null = null;

  constructor() {
    // Восстанавливаем токены из localStorage
    this.accessToken = localStorage.getItem('access_token');
    this.refreshToken = localStorage.getItem('refresh_token');
  }

  /**
   * Получить или обновить токен авторизации.
   */
  async ensureAuth(): Promise<string> {
    if (this.accessToken) {
      return this.accessToken;
    }

    // Получаем новый токен
    const response = await fetch(`${API_BASE_URL}/v1/auth/token`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ client_id: this.getClientId() }),
    });

    if (!response.ok) {
      throw new Error('Failed to get auth token');
    }

    const data: TokenResponse = await response.json();
    this.setTokens(data.access_token, data.refresh_token);
    return data.access_token;
  }

  /**
   * Выполнить авторизованный запрос.
   */
  async fetch<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const token = await this.ensureAuth();

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers: {
        ...options.headers,
        'Authorization': `Bearer ${token}`,
      },
    });

    if (response.status === 401) {
      // Токен истёк, пробуем обновить
      await this.refreshAccessToken();
      return this.fetch(endpoint, options);
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  /**
   * POST запрос с JSON body.
   */
  async post<T>(endpoint: string, data: unknown): Promise<T> {
    return this.fetch<T>(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
  }

  /**
   * POST запрос с FormData (для файлов).
   */
  async postFormData<T>(endpoint: string, formData: FormData): Promise<T> {
    const token = await this.ensureAuth();

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: formData,
    });

    if (response.status === 401) {
      await this.refreshAccessToken();
      return this.postFormData(endpoint, formData);
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  /**
   * GET запрос.
   */
  async get<T>(endpoint: string): Promise<T> {
    return this.fetch<T>(endpoint, { method: 'GET' });
  }

  /**
   * DELETE запрос.
   */
  async delete<T>(endpoint: string): Promise<T> {
    return this.fetch<T>(endpoint, { method: 'DELETE' });
  }

  private async refreshAccessToken(): Promise<void> {
    if (!this.refreshToken) {
      this.clearTokens();
      throw new Error('No refresh token');
    }

    const response = await fetch(`${API_BASE_URL}/v1/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: this.refreshToken }),
    });

    if (!response.ok) {
      this.clearTokens();
      throw new Error('Failed to refresh token');
    }

    const data: TokenResponse = await response.json();
    this.setTokens(data.access_token, data.refresh_token);
  }

  private setTokens(access: string, refresh: string): void {
    this.accessToken = access;
    this.refreshToken = refresh;
    localStorage.setItem('access_token', access);
    localStorage.setItem('refresh_token', refresh);
  }

  private clearTokens(): void {
    this.accessToken = null;
    this.refreshToken = null;
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }

  private getClientId(): string {
    let clientId = localStorage.getItem('client_id');
    if (!clientId) {
      clientId = crypto.randomUUID();
      localStorage.setItem('client_id', clientId);
    }
    return clientId;
  }
}

export const apiClient = new ApiClient();
