export type ActionType =
  | 'RETRY_PAYMENT'
  | 'REQUEST_ALTERNATE_PAYMENT_METHOD'
  | 'SEND_PAYMENT_REMINDER'
  | 'REQUEST_REAUTHENTICATION'
  | 'WAIT_AND_RETRY'
  | 'MANUAL_REVIEW'
  | 'CLOSE_RECOVERY_CASE'
  | 'ESCALATE';

export type ActionStatus =
  | 'PROPOSED'
  | 'POLICY_CHECK'
  | 'AUTHORIZED'
  | 'QUEUED'
  | 'EXECUTING'
  | 'SUCCEEDED'
  | 'FAILED'
  | 'RETRYABLE'
  | 'BLOCKED'
  | 'REQUIRES_APPROVAL'
  | 'CANCELLED'
  | 'UNKNOWN';

export type ExecutionAttemptStatus =
  | 'PENDING'
  | 'EXECUTING'
  | 'SUCCESS'
  | 'FAILURE'
  | 'TIMEOUT'
  | 'UNKNOWN';

export interface PolicyDecision {
  decision: 'ALLOWED' | 'BLOCKED' | 'REQUIRES_APPROVAL';
  reasons: string[];
  applicable_rules: string[];
  policy_version: string;
  evaluated_at: string;
}

export interface ExecutionAttempt {
  id: string;
  attempt_number: number;
  idempotency_key: string;
  adapter_name: string;
  status: ExecutionAttemptStatus;
  provider_reference?: string | null;
  error_code?: string | null;
  error_message?: string | null;
  is_retryable: boolean;
  execution_latency_ms: number;
  started_at: string;
  completed_at?: string | null;
}

export interface RecoveryAction {
  id: string;
  action_id: string;
  opportunity_id: string;
  payment_id: string;
  merchant_id: string;
  recovery_plan_id?: string | null;
  agent_run_id?: string | null;
  action_type: ActionType;
  status: ActionStatus;
  parameters?: Record<string, any> | null;
  policy_decision?: PolicyDecision | null;
  idempotency_key: string;
  execution_attempts_count: number;
  max_attempts: number;
  provider_reference?: string | null;
  last_result?: Record<string, any> | null;
  last_error_code?: string | null;
  last_error_message?: string | null;
  policy_version: string;
  execution_version: string;
  requested_at: string;
  authorized_at?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
  created_at: string;
  updated_at: string;
  attempts?: ExecutionAttempt[];
}

export interface ExecutionResultResponse {
  action_id: string;
  status: ActionStatus;
  success: boolean;
  recovered_amount_minor?: number | null;
  provider_reference?: string | null;
  latency_ms: number;
  attempt_number: number;
  is_retryable: boolean;
  is_unknown: boolean;
  error_code?: string | null;
  error_message?: string | null;
  message: string;
}
