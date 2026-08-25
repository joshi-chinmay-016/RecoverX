import { apiClient } from './client';
import {
  AgentRunResponse,
  AgentRunDetail,
  AgentTraceResponse,
  AgentRunListResponse,
} from '@/types/agent';
import { PolicySummary } from '@/types/policy';

export async function analyzeOpportunity(
  opportunityId: string,
  forceReanalyze: boolean = false
): Promise<AgentRunResponse> {
  return apiClient<AgentRunResponse>(`/agent/analyze/${opportunityId}`, {
    method: 'POST',
    body: JSON.stringify({ force_reanalyze: forceReanalyze }),
  });
}

export async function previewOpportunity(
  opportunityId: string
): Promise<AgentRunResponse> {
  return apiClient<AgentRunResponse>(`/agent/preview/${opportunityId}`, {
    method: 'POST',
  });
}

export async function getAgentRun(runId: string): Promise<AgentRunDetail> {
  return apiClient<AgentRunDetail>(`/agent/runs/${runId}`);
}

export async function getAgentTrace(runId: string): Promise<AgentTraceResponse> {
  return apiClient<AgentTraceResponse>(`/agent/runs/${runId}/trace`);
}

export async function listAgentRuns(
  page: number = 1,
  pageSize: number = 20,
  opportunityId?: string,
  status?: string
): Promise<AgentRunListResponse> {
  const params = new URLSearchParams();
  params.append('page', page.toString());
  params.append('page_size', pageSize.toString());
  if (opportunityId) params.append('opportunity_id', opportunityId);
  if (status) params.append('status', status);

  return apiClient<AgentRunListResponse>(`/agent/runs?${params.toString()}`);
}

export async function getPolicySummary(): Promise<PolicySummary> {
  return apiClient<PolicySummary>('/agent/policy');
}
