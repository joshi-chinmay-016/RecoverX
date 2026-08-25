"""Policy Rules for Phase 3 Agent.

Deterministic rules that the agent must follow.
The PolicyEngine enforces these rules.
"""

from typing import Dict, Any, List
from app.core.config import settings
from app.agent.schemas import ActionType, RiskLevel


class PolicyRules:
    """Deterministic policy rules for recovery actions."""
    
    @staticmethod
    def get_max_retry_attempts() -> int:
        """Get maximum allowed retry attempts."""
        return settings.max_retry_attempts
    
    @staticmethod
    def get_action_approval_requirement(action_type: ActionType) -> bool:
        """Check if an action requires approval."""
        approval_required_actions = {
            ActionType.SEND_PAYMENT_REMINDER,
            ActionType.MANUAL_REVIEW,
            ActionType.CLOSE_RECOVERY_CASE,
            ActionType.ESCALATE,
        }
        return action_type in approval_required_actions
    
    @staticmethod
    def get_action_risk_level(action_type: ActionType) -> RiskLevel:
        """Get risk level for an action."""
        risk_levels = {
            ActionType.RETRY_PAYMENT: RiskLevel.MEDIUM,
            ActionType.REQUEST_ALTERNATE_PAYMENT_METHOD: RiskLevel.LOW,
            ActionType.SEND_PAYMENT_REMINDER: RiskLevel.LOW,
            ActionType.REQUEST_REAUTHENTICATION: RiskLevel.MEDIUM,
            ActionType.WAIT_AND_RETRY: RiskLevel.LOW,
            ActionType.MANUAL_REVIEW: RiskLevel.LOW,
            ActionType.CLOSE_RECOVERY_CASE: RiskLevel.LOW,
            ActionType.ESCALATE: RiskLevel.MEDIUM,
        }
        return risk_levels.get(action_type, RiskLevel.MEDIUM)
    
    @staticmethod
    def validate_retry_allowed(current_retry_count: int) -> bool:
        """Validate if retry is allowed based on retry count."""
        return current_retry_count < settings.max_retry_attempts
    
    @staticmethod
    def validate_payment_eligible(payment_status: str) -> bool:
        """Validate if payment is eligible for recovery actions."""
        # Cannot act on already successful payments
        if payment_status == "CAPTURED":
            return False
        # Cannot act on created payments (not yet attempted)
        if payment_status == "CREATED":
            return False
        return True
    
    @staticmethod
    def validate_recovery_case_open(recovery_case_status: str) -> bool:
        """Validate if recovery case is still open."""
        return recovery_case_status == "OPEN"
    
    @staticmethod
    def validate_action_parameters(action_type: ActionType, parameters: Dict[str, Any]) -> bool:
        """Validate action parameters."""
        # Delay must be non-negative
        if "delay_minutes" in parameters:
            if parameters["delay_minutes"] < 0:
                return False
            if parameters["delay_minutes"] > 1440:  # Max 24 hours
                return False
        
        return True
    
    @staticmethod
    def get_confidence_threshold() -> float:
        """Get minimum confidence threshold for agent plans."""
        return settings.agent_confidence_threshold
