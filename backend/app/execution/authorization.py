"""Deterministic Authorization Service for Phase 4."""

from datetime import datetime
from typing import Dict, Any, Tuple
from sqlalchemy.orm import Session

from app.agent.policy.engine import PolicyEngine
from app.agent.strategies.registry import ActionRegistry
from app.agent.schemas import PolicyStatus, ActionType
from app.db.models.payment import Payment
from app.db.models.recovery_case import RecoveryCase
from app.db.models.recovery_action import RecoveryAction
from app.execution.schemas import PolicyDecision
from app.core.logging import get_logger

logger = get_logger(__name__)


class AuthorizationService:
    """Server-side deterministic authority that evaluates and authorizes recovery actions."""

    def __init__(self, db: Session):
        self.db = db
        self.policy_engine = PolicyEngine()

    def evaluate_action(self, action: RecoveryAction) -> PolicyDecision:
        """Evaluate a recovery action against hard deterministic policies.
        
        Returns a rich, structured PolicyDecision.
        """
        reasons = []
        applicable_rules = []
        
        # 1. Verify Payment existence & eligibility
        payment: Payment = self.db.query(Payment).filter(Payment.id == action.payment_id).first()
        if not payment:
            reasons.append("Referenced payment does not exist in financial records.")
            return PolicyDecision(
                decision=PolicyStatus.BLOCKED,
                reasons=reasons,
                applicable_rules=["payment_exists_rule"],
                policy_version="policy-v1",
            )

        applicable_rules.append("payment_status_eligibility")
        payment_status_val = payment.status.value if hasattr(payment.status, "value") else str(payment.status or "")
        if payment_status_val == "CAPTURED":
            reasons.append("Payment is already captured and resolved. No recovery action permitted.")
            return PolicyDecision(
                decision=PolicyStatus.BLOCKED,
                reasons=reasons,
                applicable_rules=applicable_rules,
                policy_version="policy-v1",
            )
        
        if payment_status_val == "CREATED":
            reasons.append("Payment has not attempted execution yet.")
            return PolicyDecision(
                decision=PolicyStatus.BLOCKED,
                reasons=reasons,
                applicable_rules=applicable_rules,
                policy_version="policy-v1",
            )

        # 2. Verify Recovery Case status
        applicable_rules.append("recovery_case_open_rule")
        recovery_case = self.db.query(RecoveryCase).filter(RecoveryCase.payment_id == payment.id).first()
        if recovery_case and recovery_case.status:
            case_status_val = recovery_case.status.value if hasattr(recovery_case.status, "value") else str(recovery_case.status)
            if case_status_val != "OPEN":
                reasons.append(f"Recovery case is already {case_status_val}. Action blocked.")
                return PolicyDecision(
                    decision=PolicyStatus.BLOCKED,
                    reasons=reasons,
                    applicable_rules=applicable_rules,
                    policy_version="policy-v1",
                )

        # 3. Verify Merchant Isolation
        applicable_rules.append("merchant_isolation_rule")
        if action.merchant_id != payment.merchant_id:
            reasons.append("Security violation: Action merchant does not match payment merchant.")
            logger.error(f"merchant_isolation_breach action_merchant={action.merchant_id} payment_merchant={payment.merchant_id}")
            return PolicyDecision(
                decision=PolicyStatus.BLOCKED,
                reasons=reasons,
                applicable_rules=applicable_rules,
                policy_version="policy-v1",
            )

        # 4. Action Type Whitelist Check
        applicable_rules.append("action_whitelist_rule")
        action_type_val = action.action_type.value if hasattr(action.action_type, "value") else str(action.action_type)
        if not ActionRegistry.is_action_allowed(action_type_val):
            reasons.append(f"Action type '{action_type_val}' is not in the authorized action whitelist.")
            return PolicyDecision(
                decision=PolicyStatus.BLOCKED,
                reasons=reasons,
                applicable_rules=applicable_rules,
                policy_version="policy-v1",
            )

        # 5. Retry Limit Check
        applicable_rules.append("max_retry_limit_rule")
        current_attempts = action.execution_attempts_count
        if action_type_val in [ActionType.RETRY_PAYMENT.value, ActionType.WAIT_AND_RETRY.value]:
            if not self.policy_engine.rules.validate_retry_allowed(current_attempts):
                max_allowed = self.policy_engine.rules.get_max_retry_attempts()
                reasons.append(f"Maximum retry attempt limit reached ({current_attempts}/{max_allowed}). Manual review required.")
                return PolicyDecision(
                    decision=PolicyStatus.BLOCKED,
                    reasons=reasons,
                    applicable_rules=applicable_rules,
                    policy_version="policy-v1",
                )

        # 6. Check if action requires explicit manual approval
        applicable_rules.append("approval_requirement_rule")
        action_enum = action.action_type if isinstance(action.action_type, ActionType) else ActionType(action_type_val)
        if self.policy_engine.rules.get_action_approval_requirement(action_enum):
            reasons.append(f"Action '{action_type_val}' has elevated policy sensitivity and requires human operator approval.")
            return PolicyDecision(
                decision=PolicyStatus.REQUIRES_APPROVAL,
                reasons=reasons,
                applicable_rules=applicable_rules,
                policy_version="policy-v1",
            )

        # All deterministic checks passed
        reasons.append("Action satisfied all deterministic policy constraints.")
        return PolicyDecision(
            decision=PolicyStatus.ALLOWED,
            reasons=reasons,
            applicable_rules=applicable_rules,
            policy_version="policy-v1",
        )
