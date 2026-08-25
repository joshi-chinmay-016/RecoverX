import { apiClient } from './client';
import { IntelligenceOverview, IntelligenceResult } from '@/types/intelligence';

export async function getIntelligenceOverview(): Promise<IntelligenceOverview> {
  return apiClient<IntelligenceOverview>('/intelligence/overview');
}

export async function analyzePayment(
  paymentId: string,
  forceReanalyze: boolean = false
): Promise<IntelligenceResult> {
  return apiClient<IntelligenceResult>(
    `/intelligence/analyze/${paymentId}?force_reanalyze=${forceReanalyze}`,
    { method: 'POST' }
  );
}

export async function batchAnalyze(paymentIds?: string[]): Promise<{
  total_analyzed: number;
  results: IntelligenceResult[];
  errors: any[];
}> {
  return apiClient('/intelligence/analyze', {
    method: 'POST',
    body: JSON.stringify({
      payment_ids: paymentIds,
      force_reanalyze: false,
    }),
  });
}
