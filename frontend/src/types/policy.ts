export interface PolicySummary {
  max_retry_attempts: number;
  confidence_threshold: number;
  approval_required_for: string[];
  policy_version: string;
}
