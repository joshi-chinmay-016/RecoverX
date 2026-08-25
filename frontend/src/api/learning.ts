import { apiClient } from './client';
import {
  LearningOverviewResponse,
  StrategyRankItem,
  AdaptiveProbabilityResult,
  CalibrationReport,
  RecomputeResponse,
} from '@/types/learning';

export const getLearningOverview = async (merchantId?: string): Promise<LearningOverviewResponse> => {
  const query = merchantId ? `?merchant_id=${merchantId}` : '';
  return apiClient<LearningOverviewResponse>(`/learning/overview${query}`);
};

export const getStrategyRankings = async (params?: {
  failure_category?: string;
  retry_count?: number;
  amount_minor?: number;
  merchant_id?: string;
}): Promise<StrategyRankItem[]> => {
  const queryParams = new URLSearchParams();
  if (params?.failure_category) queryParams.set('failure_category', params.failure_category);
  if (params?.retry_count !== undefined) queryParams.set('retry_count', String(params.retry_count));
  if (params?.amount_minor !== undefined) queryParams.set('amount_minor', String(params.amount_minor));
  if (params?.merchant_id) queryParams.set('merchant_id', params.merchant_id);

  const queryString = queryParams.toString();
  return apiClient<StrategyRankItem[]>(`/learning/strategies${queryString ? `?${queryString}` : ''}`);
};

export const getAdaptiveEvidence = async (params: {
  failure_category: string;
  action_type?: string;
  baseline_probability?: number;
  merchant_id?: string;
}): Promise<AdaptiveProbabilityResult> => {
  const queryParams = new URLSearchParams();
  queryParams.set('failure_category', params.failure_category);
  if (params.action_type) queryParams.set('action_type', params.action_type);
  if (params.baseline_probability !== undefined) queryParams.set('baseline_probability', String(params.baseline_probability));
  if (params.merchant_id) queryParams.set('merchant_id', params.merchant_id);

  return apiClient<AdaptiveProbabilityResult>(`/learning/evidence?${queryParams.toString()}`);
};

export const getCalibrationReport = async (merchantId?: string): Promise<CalibrationReport> => {
  const query = merchantId ? `?merchant_id=${merchantId}` : '';
  return apiClient<CalibrationReport>(`/learning/calibration${query}`);
};

export const recomputeLearningModel = async (merchantId?: string): Promise<RecomputeResponse> => {
  const query = merchantId ? `?merchant_id=${merchantId}` : '';
  return apiClient<RecomputeResponse>(`/learning/recompute${query}`, {
    method: 'POST',
  });
};
