import { apiClient } from './client';
import { OpportunityListResponse, OpportunityFilter } from '@/types/opportunity';
import { IntelligenceResult } from '@/types/intelligence';

export async function listOpportunities(
  filter: OpportunityFilter = {}
): Promise<OpportunityListResponse> {
  const params = new URLSearchParams();
  
  if (filter.priority) params.append('priority', filter.priority);
  if (filter.failure_category) params.append('failure_category', filter.failure_category);
  if (filter.page) params.append('page', filter.page.toString());
  if (filter.page_size) params.append('page_size', filter.page_size.toString());

  const queryString = params.toString();
  const endpoint = `/intelligence/opportunities${queryString ? `?${queryString}` : ''}`;
  
  return apiClient<OpportunityListResponse>(endpoint);
}

export async function getOpportunity(resultId: string): Promise<IntelligenceResult> {
  return apiClient<IntelligenceResult>(`/intelligence/opportunities/${resultId}`);
}
