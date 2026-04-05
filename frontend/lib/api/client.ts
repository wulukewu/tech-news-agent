const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL;

interface ApiError {
  error: string;
  description?: string;
  detail?: string;
}

export class ApiClient {
  private baseURL: string;

  constructor(baseURL: string = API_BASE_URL!) {
    this.baseURL = baseURL;
  }

  private getToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('access_token');
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;

    // Get token from localStorage
    const token = this.getToken();
    console.log(
      'API request:',
      endpoint,
      'Token:',
      token ? token.substring(0, 20) + '...' : 'none',
    );

    const config: RequestInit = {
      ...options,
      credentials: 'include', // Still include for potential future use
      headers: {
        'Content-Type': 'application/json',
        ...(token && { Authorization: `Bearer ${token}` }), // Add Authorization header if token exists
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, config);
      console.log('API response:', endpoint, 'Status:', response.status);

      if (response.status === 401) {
        // Token 過期或無效，觸發登出
        console.error('401 Unauthorized - removing token');
        if (typeof window !== 'undefined') {
          localStorage.removeItem('access_token');
        }
        window.dispatchEvent(new Event('unauthorized'));
        throw new Error('Unauthorized');
      }

      if (!response.ok) {
        const error: ApiError = await response.json();
        console.error('API error:', error);
        throw new Error(error.detail || error.error || 'API request failed');
      }

      return await response.json();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  async get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  async post<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async patch<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }
}

export const apiClient = new ApiClient();
