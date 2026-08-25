"""Pydantic schemas for Phase 4 Controlled Action Execution."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from uuid import UUID
from enum import Enum

from app.agent.schemas import ActionType, PolicyStatus, RiskLevel
from app.db.base import ActionStatus, ExecutionAttemptStatus


class PolicyDecision(BaseModel):
    """Structured decision from deterministic PolicyEngine."""
    decision: PolicyStatus = Field(..., description="Decision: ALLOWED, BLOCKED, or REQUIRES_APPROVAL")
    reasons: List[str] = Field(default_factory=list, description="Explanations for the decision")
    applicable_rules: List[str] = Field(default_factory=list, description="Rules applied during evaluation")
    policy_version: str = Field(default="policy-v1", description="Policy version used")
    evaluated_at: datetime = Field(default_factory=datetime.utcnow, description="Evaluation timestamp")


class ProviderResult(BaseModel):
    """Normalized structured result returned by execution adapters."""
    success: bool = Field(..., description="Whether the action succeeded at provider")
    provider_reference: Optional[str] = Field(None, description="External provider transaction reference")
    provider_status: Optional[str] = Field(None, description="Raw provider status string")
    error_code: Optional[str] = Field(None, description="Standardized error code if failed")
    error_message: Optional[str] = Field(None, description="Detailed error description")
    is_retryable: bool = Field(default=False, description="Whether the failure is eligible for retry")
    is_unknown: bool = Field(default=False, description="True if provider timed out without confirmed status")
    latency_ms: int = Field(default=0, description="Provider execution latency in milliseconds")
    raw_payload: Optional[Dict[str, Any]] = Field(None, description="Raw response payload for auditing")


class CreateActionRequest(BaseModel):
    """Request to create a recovery action from a plan or opportunity."""
    opportunity_id: Union[UUID, str]
    action_type: ActionType
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict)
    recovery_plan_id: Optional[str] = None
    agent_run_id: Optional[Union[UUID, str]] = None


class AuthorizeActionRequest(BaseModel):
    """Request to evaluate policy and authorize an action."""
    force_reevaluate: bool = Field(default=False, description="Re-run policy even if already authorized")


class ExecuteActionRequest(BaseModel):
    """Request to execute an authorized action."""
    idempotency_key: Optional[str] = Field(None, description="Optional custom client idempotency key")
    simulation_override: Optional[str] = Field(None, description="Demo override: SUCCESS, TEMPORARY_FAILURE, PERMANENT_FAILURE, TIMEOUT")


class ExecutionAttemptResponse(BaseModel):
    """Response schema for an individual execution attempt."""
    id: Union[UUID, str]
    attempt_number: int
    idempotency_key: str
    adapter_name: str
    status: ExecutionAttemptStatus
    provider_reference: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    is_retryable: bool = False
    execution_latency_ms: int = 0
    started_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RecoveryActionResponse(BaseModel):
    """Complete response schema for a recovery action."""
    id: Union[UUID, str]
    action_id: str
    opportunity_id: Union[UUID, str]
    payment_id: Union[UUID, str]
    merchant_id: Union[UUID, str]
    recovery_plan_id: Optional[str] = None
    agent_run_id: Optional[Union[UUID, str]] = None
    action_type: ActionType
    status: ActionStatus
    parameters: Optional[Dict[str, Any]] = None
    policy_decision: Optional[Dict[str, Any]] = None
    idempotency_key: str
    execution_attempts_count: int = 0
    max_attempts: int = 3
    provider_reference: Optional[str] = None
    last_result: Optional[Dict[str, Any]] = None
    last_error_code: Optional[str] = None
    last_error_message: Optional[str] = None
    policy_version: str
    execution_version: str
    requested_at: datetime
    authorized_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    attempts: List[ExecutionAttemptResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True


class ExecutionResultResponse(BaseModel):
    """Immediate response returned after executing an action."""
    action_id: str
    status: ActionStatus
    success: bool
    recovered_amount_minor: Optional[int] = None
    provider_reference: Optional[str] = None
    latency_ms: int = 0
    attempt_number: int = 1
    is_retryable: bool = False
    is_unknown: bool = False
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    message: str
