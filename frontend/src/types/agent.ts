export type ActionType =
  | 'RETRY_PAYMENT'
  | 'REQUEST_ALTERNATE_PAYMENT_METHOD'
  | 'SEND_PAYMENT_REMINDER'
  | 'REQUEST_REAUTHENTICATION'
  | 'WAIT_AND_RETRY'
  | 'MANUAL_REVIEW'
  | 'CLOSE_RECOVERY_CASE'
  | 'ESCALATE';

export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export type PolicyStatus = 'ALLOWED' | 'BLOCKED' | 'REQUIRES_APPROVAL';

export type AgentRunStatus =
  | 'CREATED'
  | 'INVESTIGATING'
  | 'PLANNING'
  | 'VALIDATING'
  | 'COMPLETED'
  | 'BLOCKED'
  | 'FAILED';

export interface AgentAction {
  action_type: ActionType;
  purpose: string;
  parameters: Record<string, any>;
  rationale: string;
  expected_outcome: string;
  risk_level: RiskLevel;
  requires_approval: boolean;
}

export interface DecisionTrace {
  observation: string;
  evidence: string;
  decision: string;
  reason: string;
  confidence: number;
}

export interface AlternativeConsidered {
  strategy?: string;
  action_type?: string;
  reason?: string;
}

export interface RecoveryPlan {
  plan_id?: string;
  opportunity_id: string;
  payment_id: string;
  merchant_id: string;
  summary: string;
  diagnosis: string;
  selected_strategy: ActionType;
  reasoning: string;
  confidence: number;
  proposed_actions: AgentAction[];
  alternatives_considered: AlternativeConsidered[];
  required_inputs: string[];
  risks: string[];
  constraints: string[];
  fallback_strategy: string;
  requires_approval: boolean;
  policy_status: PolicyStatus;
  policy_reason?: string | null;
  agent_version?: string;
  prompt_version?: string;
  policy_version?: string;
  created_at?: string;
}

export interface AgentRunResponse {
  run_id: string;
  status: AgentRunStatus;
  selected_strategy?: string | null;
  confidence?: number | null;
  plan?: RecoveryPlan | null;
  decision_summary?: string | null;
  policy_status?: PolicyStatus | null;
  error?: string | null;
}

export interface AgentRunListItem {
  run_id: string;
  opportunity_id: string;
  payment_id: string;
  merchant_id: string;
  status: string;
  current_step: number;
  selected_strategy?: string | null;
  confidence?: number | null;
  policy_status?: string | null;
  agent_version: string;
  prompt_version: string;
  policy_version: string;
  started_at?: string | null;
  completed_at?: string | null;
  created_at?: string | null;
}

export interface AgentRunListResponse {
  total: number;
  page: number;
  page_size: number;
  runs: AgentRunListItem[];
}

export interface AgentRunDetail {
  run_id: string;
  opportunity_id: string;
  payment_id: string;
  merchant_id: string;
  status: string;
  current_step: number;
  context?: any;
  tool_calls_summary?: any[];
  reasoning_summary?: string;
  decision_trace?: DecisionTrace[];
  proposed_plan?: RecoveryPlan;
  validation_result?: any;
  errors?: string[];
  started_at?: string;
  completed_at?: string;
  agent_version: string;
  prompt_version: string;
  policy_version: string;
}

export interface AgentTraceResponse {
  run_id: string;
  decision_trace: DecisionTrace[];
  tool_calls_summary: any[];
  reasoning_summary?: string;
}
