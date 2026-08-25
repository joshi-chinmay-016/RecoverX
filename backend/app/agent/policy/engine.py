"""Policy Engine for Phase 3 Agent.

Deterministic policy enforcement that validates agent plans.
The LLM cannot override the PolicyEngine.
"""

from typing import Dict, Any, Optional
from app.agent.schemas import RecoveryPlan, PolicyStatus, ActionType
from app.agent.policy.rules import PolicyRules
from app.core.logging import get_logger

logger = get_logger(__name__)


class PolicyEngine:
    """Deterministic policy engine for validating agent plans."""
    
    def __init__(self):
        self.rules = PolicyRules()
    
    def validate_plan(
        self,
        plan: RecoveryPlan,
        context: Dict[str, Any],
    ) -> tuple[PolicyStatus, Optional[str]]:
        """Validate a recovery plan against policy rules.
        
        Returns:
            (policy_status, reason)
        """
        try:
            # Check if payment is eligible
            payment_status = context.get("payment_status", "")
            if not self.rules.validate_payment_eligible(payment_status):
                return PolicyStatus.BLOCKED, f"Payment status {payment_status} is not eligible for recovery actions"
            
            # Check recovery case status
            recovery_case_status = context.get("recovery_case_status", "OPEN")
            if not self.rules.validate_recovery_case_open(recovery_case_status):
                return PolicyStatus.BLOCKED, f"Recovery case is not open (status: {recovery_case_status})"
            
            # Validate each proposed action
            for action in plan.proposed_actions:
                action_result, action_reason = self._validate_action(
                    action,
                    context,
                )
                if action_result != PolicyStatus.ALLOWED:
                    return action_result, action_reason
            
            # Check if plan requires approval
            if plan.requires_approval:
                return PolicyStatus.REQUIRES_APPROVAL, "Plan contains actions requiring approval"
            
            # Check confidence threshold
            if plan.confidence < self.rules.get_confidence_threshold():
                return PolicyStatus.REQUIRES_APPROVAL, f"Plan confidence {plan.confidence} below threshold {self.rules.get_confidence_threshold()}"
            
            return PolicyStatus.ALLOWED, None
            
        except Exception as e:
            logger.error(f"Policy validation error: {e}")
            return PolicyStatus.BLOCKED, f"Policy validation failed: {str(e)}"
    
    def _validate_action(
        self,
        action,
        context: Dict[str, Any],
    ) -> tuple[PolicyStatus, Optional[str]]:
        """Validate a single action against policy rules."""
        action_type = action.action_type
        
        # Check if action is allowed
        if not self._is_action_allowed(action_type):
            return PolicyStatus.BLOCKED, f"Action {action_type} is not allowed"
        
        # Check retry limit for retry actions
        if action_type in [ActionType.RETRY_PAYMENT, ActionType.WAIT_AND_RETRY]:
            current_retry_count = context.get("retry_count", 0)
            if not self.rules.validate_retry_allowed(current_retry_count):
                return PolicyStatus.BLOCKED, f"Retry limit reached ({current_retry_count}/{self.rules.get_max_retry_attempts()})"
        
        # Validate action parameters
        parameters = action.parameters or {}
        if not self.rules.validate_action_parameters(action_type, parameters):
            return PolicyStatus.BLOCKED, f"Invalid parameters for action {action_type}"
        
        # Check approval requirement
        if self.rules.get_action_approval_requirement(action_type):
            return PolicyStatus.REQUIRES_APPROVAL, f"Action {action_type} requires approval"
        
        return PolicyStatus.ALLOWED, None
    
    def _is_action_allowed(self, action_type: ActionType) -> bool:
        """Check if an action type is in the allowed registry."""
        from app.agent.strategies.registry import ActionRegistry
        return ActionRegistry.is_action_allowed(action_type.value)
    
    def get_policy_summary(self) -> Dict[str, Any]:
        """Get summary of current policy configuration."""
        return {
            "max_retry_attempts": self.rules.get_max_retry_attempts(),
            "confidence_threshold": self.rules.get_confidence_threshold(),
            "approval_required_for": [
                action.value for action in ActionType
                if self.rules.get_action_approval_requirement(action)
            ],
            "policy_version": "policy-v1",
        }
