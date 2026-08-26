/**
 * Authentication & Tenant Context API methods (Phase 6)
 */

import { apiClient } from './client';
import {
  LoginResponse,
  TenantContextResponse,
  SwitchMerchantRequest,
} from '@/types/auth';

export async function loginApi(email: string, password: string): Promise<LoginResponse> {
  return apiClient<LoginResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
}

export async function getCurrentUserProfileApi(): Promise<TenantContextResponse> {
  return apiClient<TenantContextResponse>('/auth/me');
}

export async function switchMerchantApi(merchantId: string): Promise<TenantContextResponse> {
  return apiClient<TenantContextResponse>('/auth/switch-merchant', {
    method: 'POST',
    body: JSON.stringify({ merchant_id: merchantId } as SwitchMerchantRequest),
  });
}
