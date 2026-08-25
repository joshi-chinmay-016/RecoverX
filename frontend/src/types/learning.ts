import { FailureCategory } from './intelligence';
import { ActionType } from './action';

export type EvidenceScope =
  | 'MERCHANT_CATEGORY_ACTION'
  | 'MERCHANT_CATEGORY'
  | 'GLOBAL_CATEGORY_ACTION'
  | 'GLOBAL_CATEGORY'
  | 'BASELINE_FALLBACK';

export type SupportLevel = 'HIGH' | 'MODERATE' | 'LOW' | 'SPARSE';
export type DriftStatus = 'NORMAL' | 'DEGRADATION_DETECTED' | 'INSUFFICIENT_DATA';

export interface StrategyScoreFactor {
  name: string;
  impact: number;
  description: string;
}

export interface StrategyRankItem {
  action_type: ActionType;
  strategy_score: number;
  empirical_recovery_rate: number;
  sample_size: number;
  support_level: SupportLevel;
  evidence_scope: EvidenceScope;
  is_policy_eligible: boolean;
  confidence: number;
  factors: StrategyScoreFactor[];
  reasons: string[];
}

export interface AdaptiveProbabilityResult {
  adaptive_probability: number;
  baseline_probability: number;
  empirical_rate: number;
  sample_size: number;
  successes: number;
  support_level: SupportLevel;
  evidence_scope: EvidenceScope;
  fallback_level: string;
  model_version: string;
  is_cold_start: boolean;
  explanation: string;
}

export interface CategoryLearningMetrics {
  failure_category: FailureCategory;
  total_attempts: number;
  confirmed_successes: number;
  confirmed_failures: number;
  observed_recovery_rate: number;
  baseline_probability: number;
  adaptive_probability: number;
  top_recommended_strategy: ActionType;
  support_level: SupportLevel;
}

export interface StrategyPerformanceSummary {
  action_type: ActionType;
  total_attempts: number;
  successful_recoveries: number;
  observed_success_rate: number;
  average_latency_ms: number;
  best_matching_category?: FailureCategory | null;
}

export interface CalibrationReport {
  brier_score: number;
  evaluated_samples: number;
  calibration_status: string;
  bucketed_accuracy: Array<{
    bucket: string;
    predicted_mid: number;
    samples: number;
    observed_rate: number;
  }>;
}

export interface LearningOverviewResponse {
  model_version: string;
  model_name: string;
  evidence_window_days: number;
  total_samples: number;
  confirmed_recoveries: number;
  overall_recovery_rate: number;
  baseline_benchmark_rate: number;
  adaptive_yield_lift_pct: number;
  unknown_outcomes_count: number;
  drift_status: DriftStatus;
  brier_score?: number | null;
  last_updated: string;
  category_breakdown: CategoryLearningMetrics[];
  strategy_rankings: StrategyPerformanceSummary[];
}

export interface RecomputeResponse {
  success: boolean;
  model_version: string;
  total_samples_processed: number;
  categories_calibrated: number;
  strategies_evaluated: number;
  brier_score?: number | null;
  drift_status: string;
  recomputed_at: string;
  message: string;
}
