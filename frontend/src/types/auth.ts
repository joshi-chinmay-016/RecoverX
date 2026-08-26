/**
 * RecoverX Authentication, Multi-Tenancy & RBAC Types (Phase 6)
 */

export type UserRole = 'ADMIN' | 'OPERATOR' | 'ANALYST';

export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  last_login_at: string | null;
  created_at: string;
}

export interface MerchantMembership {
  id: string;
  merchant_id: string;
  merchant_name: string;
  merchant_external_id: string;
  currency: string;
  role: UserRole;
  is_active: boolean;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: UserProfile;
  active_merchant: MerchantMembership;
  available_merchants: MerchantMembership[];
}

export interface TenantContextResponse {
  user: UserProfile;
  active_membership: MerchantMembership;
  available_merchants: MerchantMembership[];
}

export interface SwitchMerchantRequest {
  merchant_id: string;
}
