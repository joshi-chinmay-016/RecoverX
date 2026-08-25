export type FailureCategory =
  | 'PAYMENT_METHOD_FAILURE'
  | 'INSUFFICIENT_FUNDS'
  | 'BANK_FAILURE'
  | 'NETWORK_FAILURE'
  | 'AUTHENTICATION_FAILURE'
  | 'LIMIT_EXCEEDED'
  | 'TEMPORARY_FAILURE'
  | 'UNKNOWN';

export type PriorityLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export interface Factor {
  factor?: string;
  name?: string;
  impact: number;
  explanation?: string;
  direction?: 'positive' | 'negative';
}

export interface IntelligenceOverview {
  total_failed_revenue: number;
  revenue_at_risk: number;
  potentially_recoverable_revenue?: number;
  estimated_recoverable_revenue: number;
  total_opportunities: number;
  high_priority_opportunities: number;
  average_recovery_probability: number;
  failure_distribution: Record<string, number>;
  top_failure_reasons: Array<{ reason: string; count: number }>;
  priority_distribution: Record<string, number>;
  recovered_revenue: number;
  total_revenue?: number;
}

export interface IntelligenceResult {
  id: string;
  payment_id: string;
  recovery_case_id: string | null;
  failure_category: FailureCategory;
  failure_reason: string;
  revenue_at_risk: number;
  recovery_probability: number;
  estimated_recoverable_revenue: number;
  opportunity_score: number;
  priority: PriorityLevel;
  recommended_intervention: string;
  intervention_reason: string;
  confidence: number;
  explanation: string;
  factors: Factor[];
  model_version: string;
  created_at: string;
  updated_at: string;
}
