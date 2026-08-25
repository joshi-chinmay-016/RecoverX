"""Tool: Get recovery policy for agent reasoning."""

from typing import Dict, Any
from app.core.config import settings


def get_recovery_policy(context: Dict[str, Any]) -> Dict[str, Any]:
    """Get recovery policy for agent reasoning (read-only)."""
    return {
        "max_retry_attempts": settings.max_retry_attempts,
        "allowed_actions": [
            "RETRY_PAYMENT",
            "REQUEST_ALTERNATE_PAYMENT_METHOD",
            "SEND_PAYMENT_REMINDER",
            "REQUEST_REAUTHENTICATION",
            "WAIT_AND_RETRY",
            "MANUAL_REVIEW",
            "CLOSE_RECOVERY_CASE",
            "ESCALATE",
        ],
        "action_limits": {
            "RETRY_PAYMENT": {
                "max_attempts": settings.max_retry_attempts,
                "requires_recent_failure": True,
            },
            "SEND_PAYMENT_REMINDER": {
                "max_per_day": 3,
                "requires_approval": True,
            },
        },
        "approval_requirements": {
            "HIGH_RISK_ACTIONS": True,
            "MANUAL_REVIEW": True,
            "CLOSE_RECOVERY_CASE": True,
        },
        "policy_version": settings.policy_version,
        "current_retry_count": context.get("retry_count", 0),
    }
