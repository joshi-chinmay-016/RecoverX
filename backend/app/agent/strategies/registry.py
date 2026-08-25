"""Allowed Action Registry for Phase 3 Agent.

Defines the explicit set of actions the agent can select from.
The agent cannot invent arbitrary actions.
"""

from typing import List, Dict, Any
from app.agent.schemas import ActionType


class ActionRegistry:
    """Registry of allowed recovery actions."""
    
    ALLOWED_ACTIONS = {
        ActionType.RETRY_PAYMENT: {
            "name": "RETRY_PAYMENT",
            "description": "Retry the failed payment",
            "risk_level": "MEDIUM",
            "requires_approval": False,
            "parameters": {
                "delay_minutes": {"type": "int", "default": 0, "description": "Delay before retry in minutes"},
            },
        },
        ActionType.REQUEST_ALTERNATE_PAYMENT_METHOD: {
            "name": "REQUEST_ALTERNATE_PAYMENT_METHOD",
            "description": "Request customer to use a different payment method",
            "risk_level": "LOW",
            "requires_approval": False,
            "parameters": {
                "suggested_methods": {"type": "list", "default": [], "description": "Suggested alternative methods"},
            },
        },
        ActionType.SEND_PAYMENT_REMINDER: {
            "name": "SEND_PAYMENT_REMINDER",
            "description": "Send a payment reminder to the customer",
            "risk_level": "LOW",
            "requires_approval": True,
            "parameters": {
                "reminder_type": {"type": "str", "default": "gentle", "description": "Type of reminder"},
            },
        },
        ActionType.REQUEST_REAUTHENTICATION: {
            "name": "REQUEST_REAUTHENTICATION",
            "description": "Request customer to re-authenticate",
            "risk_level": "MEDIUM",
            "requires_approval": False,
            "parameters": {
                "auth_method": {"type": "str", "default": "standard", "description": "Authentication method"},
            },
        },
        ActionType.WAIT_AND_RETRY: {
            "name": "WAIT_AND_RETRY",
            "description": "Wait a specified time then retry",
            "risk_level": "LOW",
            "requires_approval": False,
            "parameters": {
                "delay_minutes": {"type": "int", "default": 30, "description": "Delay before retry in minutes"},
            },
        },
        ActionType.MANUAL_REVIEW: {
            "name": "MANUAL_REVIEW",
            "description": "Escalate to manual review",
            "risk_level": "LOW",
            "requires_approval": True,
            "parameters": {
                "reason": {"type": "str", "default": "", "description": "Reason for manual review"},
            },
        },
        ActionType.CLOSE_RECOVERY_CASE: {
            "name": "CLOSE_RECOVERY_CASE",
            "description": "Close the recovery case",
            "risk_level": "LOW",
            "requires_approval": True,
            "parameters": {
                "closure_reason": {"type": "str", "default": "", "description": "Reason for closure"},
            },
        },
        ActionType.ESCALATE: {
            "name": "ESCALATE",
            "description": "Escalate to higher priority handling",
            "risk_level": "MEDIUM",
            "requires_approval": True,
            "parameters": {
                "escalation_level": {"type": "str", "default": "standard", "description": "Escalation level"},
            },
        },
    }
    
    @classmethod
    def get_allowed_actions(cls) -> List[str]:
        """Get list of allowed action names."""
        return [action.value for action in ActionType]
    
    @classmethod
    def get_action_config(cls, action_type: ActionType) -> Dict[str, Any]:
        """Get configuration for a specific action."""
        return cls.ALLOWED_ACTIONS.get(action_type, {})
    
    @classmethod
    def is_action_allowed(cls, action_name: str) -> bool:
        """Check if an action is allowed."""
        return action_name in cls.get_allowed_actions()
    
    @classmethod
    def validate_action_parameters(cls, action_type: ActionType, parameters: Dict[str, Any]) -> bool:
        """Validate action parameters against schema."""
        config = cls.get_action_config(action_type)
        param_schema = config.get("parameters", {})
        
        for param_name, param_value in parameters.items():
            if param_name not in param_schema:
                return False  # Unknown parameter
            
            # Validate parameter values
            if param_name == "delay_minutes":
                if not isinstance(param_value, (int, float)):
                    return False
                if param_value < 0:
                    return False
                if param_value > 1440:  # Max 24 hours
                    return False
        
        return True


def get_allowed_actions() -> List[str]:
    """Get list of allowed action names."""
    return ActionRegistry.get_allowed_actions()
