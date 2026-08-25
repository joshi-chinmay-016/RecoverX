"""Deterministic Action State Machine for Phase 4."""

from typing import Dict, Set
from app.db.base import ActionStatus
from app.core.logging import get_logger

logger = get_logger(__name__)


class InvalidStateTransitionError(ValueError):
    """Raised when an illegal action state transition is attempted."""
    pass


class ActionStateMachine:
    """Enforces strict, auditable lifecycle transitions for recovery actions."""

    VALID_TRANSITIONS: Dict[ActionStatus, Set[ActionStatus]] = {
        ActionStatus.PROPOSED: {
            ActionStatus.POLICY_CHECK,
            ActionStatus.CANCELLED,
        },
        ActionStatus.POLICY_CHECK: {
            ActionStatus.AUTHORIZED,
            ActionStatus.BLOCKED,
            ActionStatus.REQUIRES_APPROVAL,
            ActionStatus.CANCELLED,
        },
        ActionStatus.REQUIRES_APPROVAL: {
            ActionStatus.AUTHORIZED,
            ActionStatus.BLOCKED,
            ActionStatus.CANCELLED,
        },
        ActionStatus.AUTHORIZED: {
            ActionStatus.QUEUED,
            ActionStatus.EXECUTING,
            ActionStatus.CANCELLED,
        },
        ActionStatus.QUEUED: {
            ActionStatus.EXECUTING,
            ActionStatus.CANCELLED,
        },
        ActionStatus.EXECUTING: {
            ActionStatus.SUCCEEDED,
            ActionStatus.FAILED,
            ActionStatus.RETRYABLE,
            ActionStatus.UNKNOWN,
        },
        ActionStatus.RETRYABLE: {
            ActionStatus.QUEUED,
            ActionStatus.EXECUTING,
            ActionStatus.FAILED,
            ActionStatus.CANCELLED,
        },
        ActionStatus.UNKNOWN: {
            ActionStatus.SUCCEEDED,
            ActionStatus.FAILED,
            ActionStatus.RETRYABLE,
            ActionStatus.CANCELLED,
        },
        # Terminal states
        ActionStatus.SUCCEEDED: set(),
        ActionStatus.FAILED: set(),
        ActionStatus.BLOCKED: set(),
        ActionStatus.CANCELLED: set(),
    }

    @classmethod
    def can_transition(cls, current_status: ActionStatus, target_status: ActionStatus) -> bool:
        """Check if a transition from current_status to target_status is valid."""
        allowed = cls.VALID_TRANSITIONS.get(current_status, set())
        return target_status in allowed

    @classmethod
    def is_terminal(cls, status: ActionStatus) -> bool:
        """Check if the given status is a terminal state."""
        return len(cls.VALID_TRANSITIONS.get(status, set())) == 0

    @classmethod
    def transition(cls, current_status: ActionStatus, target_status: ActionStatus) -> ActionStatus:
        """Validate and return the target status or raise InvalidStateTransitionError."""
        if not cls.can_transition(current_status, target_status):
            error_msg = f"Forbidden state transition: Cannot transition RecoveryAction from {current_status.value} to {target_status.value}."
            logger.warning(f"invalid_action_transition from={current_status.value} to={target_status.value}")
            raise InvalidStateTransitionError(error_msg)
        return target_status
