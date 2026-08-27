/**
 * RecoverX Centralized Typed API Client with JWT & Multi-Tenant Support
 */

export const BASE_URL = (() => {
  const envUrl = import.meta.env?.VITE_API_BASE_URL;
  if (envUrl) {
    const cleanUrl = envUrl.replace(/\/$/, '');
    return cleanUrl.endsWith('/api/v1') ? cleanUrl : `${cleanUrl}/api/v1`;
  }
  return import.meta.env.PROD 
    ? 'https://recoverx-v65y.onrender.com/api/v1'
    : 'http://localhost:8000/api/v1';
})();

export class ApiError extends Error {
  status: number;
  data: any;

  constructor(status: number, message: string, data?: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

export async function apiClient<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = endpoint.startsWith('http')
    ? endpoint
    : `${BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;

  const token = localStorage.getItem('recoverx_token');
  const activeMerchantId = localStorage.getItem('recoverx_active_merchant_id');

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(activeMerchantId ? { 'X-Merchant-ID': activeMerchantId } : {}),
    ...(options.headers as Record<string, string>),
  };

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      let errorData;
      try {
        errorData = await response.json();
      } catch {
        errorData = { detail: response.statusText };
      }

      const errorMessage =
        (typeof errorData.detail === 'string' ? errorData.detail : errorData.message) ||
        `HTTP Request failed with status ${response.status}`;

      // Handle 401 Unauthorized globally
      if (response.status === 401 && !url.includes('/auth/login')) {
        localStorage.removeItem('recoverx_token');
        localStorage.removeItem('recoverx_user');
        localStorage.removeItem('recoverx_active_merchant_id');
        if (window.location.pathname !== '/login') {
          window.location.href = '/login';
        }
      }

      throw new ApiError(response.status, errorMessage, errorData);
    }

    return (await response.json()) as T;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError(
      0,
      error instanceof Error ? error.message : 'Network connection failure. Ensure backend is running.'
    );
  }
}
