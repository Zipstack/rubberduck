const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

interface ApiRequestOptions extends RequestInit {
  skipAuth?: boolean;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: ApiRequestOptions = {}
  ): Promise<T> {
    const { skipAuth = false, ...requestOptions } = options;
    
    const url = `${this.baseUrl}${endpoint}`;
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(requestOptions.headers as Record<string, string>),
    };

    // Add auth token if not skipped
    if (!skipAuth) {
      const token = localStorage.getItem('auth_token');
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
    }

    const config: RequestInit = {
      ...requestOptions,
      headers,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorText = await response.text();
        let errorMessage = `HTTP ${response.status}`;
        
        try {
          const errorData = JSON.parse(errorText);
          errorMessage = errorData.detail || errorData.message || errorMessage;
        } catch {
          errorMessage = errorText || errorMessage;
        }
        
        throw new ApiError(response.status, errorMessage);
      }

      // Handle empty responses
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        return await response.json();
      } else {
        return {} as T;
      }
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      throw new ApiError(0, `Network error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  // Authentication endpoints
  async login(email: string, password: string) {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);

    return this.request<{ access_token: string; token_type: string }>('/auth/jwt/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData,
      skipAuth: true,
    });
  }

  async register(email: string, password: string) {
    return this.request<{ id: string; email: string; is_active: boolean; is_verified: boolean }>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
      skipAuth: true,
    });
  }

  async getCurrentUser() {
    return this.request<{ id: string; email: string; is_active: boolean; is_verified: boolean }>('/users/me');
  }

  // Health check
  async healthCheck() {
    return this.request<{ status: string; version: string; db_status?: string; running_proxy_count?: number }>('/healthz', {
      skipAuth: true,
    });
  }

  // Proxy endpoints
  async getProxies() {
    const response = await this.request<{proxies: any[]}>('/proxies');
    return response.proxies;
  }

  async createProxy(proxyData: {
    name: string;
    provider: string;
    description?: string;
    port?: number;
  }) {
    return this.request<any>('/proxies', {
      method: 'POST',
      body: JSON.stringify(proxyData),
    });
  }

  async startProxy(proxyId: number) {
    return this.request<any>(`/proxies/${proxyId}/start`, {
      method: 'POST',
    });
  }

  async stopProxy(proxyId: number) {
    return this.request<any>(`/proxies/${proxyId}/stop`, {
      method: 'POST',
    });
  }

  async deleteProxy(proxyId: number) {
    return this.request<any>(`/proxies/${proxyId}`, {
      method: 'DELETE',
    });
  }

  async getProviders() {
    return this.request<{providers: string[]}>('/providers');
  }

  async getProxyFailureConfig(proxyId: number) {
    return this.request<any>(`/proxies/${proxyId}/failure-config`);
  }

  async updateProxyFailureConfig(proxyId: number, config: any) {
    return this.request<any>(`/proxies/${proxyId}/failure-config`, {
      method: 'PUT',
      body: JSON.stringify(config),
    });
  }

  // Cache endpoints
  async getCacheStats(proxyId: number) {
    return this.request<any>(`/cache/${proxyId}/stats`);
  }

  async invalidateCache(proxyId: number) {
    return this.request<any>(`/cache/${proxyId}`, {
      method: 'DELETE',
    });
  }

  // Logs endpoints
  async getLogs(filters?: {
    proxy_id?: number;
    status_code?: number;
    cache_hit?: boolean;
    limit?: number;
    offset?: number;
  }) {
    const params = new URLSearchParams();
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          params.append(key, value.toString());
        }
      });
    }
    
    const queryString = params.toString();
    const endpoint = queryString ? `/logs?${queryString}` : '/logs';
    
    const response = await this.request<{logs: any[], total_count: number, limit: number, offset: number}>(endpoint);
    return response.logs;
  }

  async exportLogs(format: 'csv' | 'json', filters?: any) {
    const params = new URLSearchParams({ export: format });
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          params.append(key, value.toString());
        }
      });
    }
    
    return this.request<Blob>(`/logs?${params.toString()}`, {
      headers: {
        'Accept': format === 'csv' ? 'text/csv' : 'application/json',
      },
    });
  }
}

export const apiClient = new ApiClient();
export { ApiError };