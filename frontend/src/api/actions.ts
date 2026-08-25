import { apiClient } from './client';
import { RecoveryAction, ExecutionResultResponse } from '@/types/action';

export const createActionsFromPlan = async (opportunityId: string): Promise<RecoveryAction[]> => {
  return apiClient<RecoveryAction[]>(`/actions/create-from-plan/${opportunityId}`, {
    method: 'POST',
  });
};

export const authorizeAction = async (
  actionId: string,
  forceReevaluate: boolean = false
): Promise<{ action: RecoveryAction; decision: any }> => {
  return apiClient<{ action: RecoveryAction; decision: any }>(`/actions/${actionId}/authorize`, {
    method: 'POST',
    body: JSON.stringify({
      force_reevaluate: forceReevaluate,
    }),
  });
};

export const executeAction = async (
  actionId: string,
  simulationOverride?: string,
  idempotencyKey?: string
): Promise<ExecutionResultResponse> => {
  return apiClient<ExecutionResultResponse>(`/actions/${actionId}/execute`, {
    method: 'POST',
    body: JSON.stringify({
      simulation_override: simulationOverride,
      idempotency_key: idempotencyKey,
    }),
  });
};

export const retryAction = async (
  actionId: string,
  simulationOverride?: string
): Promise<ExecutionResultResponse> => {
  return apiClient<ExecutionResultResponse>(`/actions/${actionId}/retry`, {
    method: 'POST',
    body: JSON.stringify({
      simulation_override: simulationOverride,
    }),
  });
};

export const reconcileAction = async (actionId: string): Promise<RecoveryAction> => {
  return apiClient<RecoveryAction>(`/actions/${actionId}/reconcile`, {
    method: 'POST',
  });
};

export const cancelAction = async (actionId: string, reason?: string): Promise<RecoveryAction> => {
  const query = reason ? `?reason=${encodeURIComponent(reason)}` : '';
  return apiClient<RecoveryAction>(`/actions/${actionId}/cancel${query}`, {
    method: 'POST',
  });
};

export const getAction = async (actionId: string): Promise<RecoveryAction> => {
  return apiClient<RecoveryAction>(`/actions/${actionId}`);
};

export const listActions = async (params?: {
  status?: string;
  action_type?: string;
  opportunity_id?: string;
  payment_id?: string;
  page?: number;
  page_size?: number;
}): Promise<{ items: RecoveryAction[]; total: number; page: number; page_size: number }> => {
  const queryParams = new URLSearchParams();
  if (params?.status) queryParams.set('status', params.status);
  if (params?.action_type) queryParams.set('action_type', params.action_type);
  if (params?.opportunity_id) queryParams.set('opportunity_id', params.opportunity_id);
  if (params?.payment_id) queryParams.set('payment_id', params.payment_id);
  if (params?.page) queryParams.set('page', String(params.page));
  if (params?.page_size) queryParams.set('page_size', String(params.page_size));

  const queryString = queryParams.toString();
  const url = `/actions${queryString ? `?${queryString}` : ''}`;
  return apiClient<{ items: RecoveryAction[]; total: number; page: number; page_size: number }>(url);
};
