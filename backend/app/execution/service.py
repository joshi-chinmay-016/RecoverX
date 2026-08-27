"""Central Execution Service for Phase 4 Controlled Action Execution."""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.base import (
    ActionStatus,
    ExecutionAttemptStatus,
    PaymentStatus,
    RecoveryCaseStatus,
    AuditEventType,
    ActorType,
    PolicyStatus,
)
from app.db.models.payment import Payment
from app.db.models.payment_attempt import PaymentAttempt
from app.db.models.recovery_case import RecoveryCase
from app.db.models.recovery_action import RecoveryAction
from app.db.models.execution_attempt import ExecutionAttempt
from app.db.models.revenue_intelligence import RevenueIntelligenceResult
from app.db.models.agent_run import AgentRun
from app.db.models.audit_event import AuditEvent
from app.db.models.learning_outcome import LearningOutcomeRecord
from app.intelligence.schemas import FailureCategory
from app.agent.schemas import ActionType
from app.execution.schemas import (
    ProviderResult,
    ExecutionResultResponse,
    PolicyDecision,
)
from app.execution.state_machine import ActionStateMachine, InvalidStateTransitionError
from app.execution.authorization import AuthorizationService
from app.execution.adapters.mock_payment import MockPaymentAdapter
from app.execution.adapters.mock_communication import MockCommunicationAdapter
from app.core.logging import get_logger

logger = get_logger(__name__)


class ExecutionService:
    """Central orchestrator for Phase 4 controlled recovery action execution."""

    def __init__(
        self,
        db: Session,
        payment_adapter: Optional[MockPaymentAdapter] = None,
        communication_adapter: Optional[MockCommunicationAdapter] = None,
    ):
        self.db = db
        self.authorization_service = AuthorizationService(db)
        self.payment_adapter = payment_adapter or MockPaymentAdapter()
        self.communication_adapter = communication_adapter or MockCommunicationAdapter()

    def create_action(
        self,
        opportunity_id: str,
        action_type: ActionType,
        parameters: Optional[Dict[str, Any]] = None,
        recovery_plan_id: Optional[str] = None,
        agent_run_id: Optional[str] = None,
    ) -> RecoveryAction:
        """Create a new proposed recovery action."""
        intel = self.db.query(RevenueIntelligenceResult).filter(
            RevenueIntelligenceResult.id == opportunity_id
        ).first()
        if not intel:
            raise ValueError(f"Revenue intelligence opportunity '{opportunity_id}' not found.")

        payment = self.db.query(Payment).filter(Payment.id == intel.payment_id).first()
        if not payment:
            raise ValueError(f"Payment '{intel.payment_id}' not found.")

        action_id = f"ACT-{uuid.uuid4().hex[:8].upper()}"
        idempotency_key = f"idem_{payment.id}_{action_type.value}_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"

        action = RecoveryAction(
            action_id=action_id,
            opportunity_id=intel.id,
            payment_id=payment.id,
            merchant_id=payment.merchant_id,
            recovery_plan_id=recovery_plan_id,
            agent_run_id=agent_run_id,
            action_type=action_type,
            status=ActionStatus.PROPOSED,
            parameters=parameters or {},
            idempotency_key=idempotency_key,
            max_attempts=3,
            policy_version="policy-v1",
            execution_version="execution-v1",
            requested_at=datetime.utcnow(),
        )

        self.db.add(action)
        self.db.flush()

        # Record Audit Event
        self._record_audit(
            entity_type="RecoveryAction",
            entity_id=action.id,
            event_type=AuditEventType.POLICY_DECISION,
            metadata={
                "event_subtype": "ACTION_PROPOSED",
                "action_id": action.action_id,
                "action_type": action.action_type.value,
                "payment_id": str(payment.id),
                "opportunity_id": str(intel.id),
            },
        )

        self.db.commit()
        self.db.refresh(action)
        logger.info(f"recovery_action_created action_id={action.action_id} type={action.action_type.value}")
        return action

    def create_actions_from_plan(self, opportunity_id: str) -> List[RecoveryAction]:
        """Synthesize recovery action records from an approved Phase 3 AgentRun."""
        # Find latest completed agent run
        agent_run = self.db.query(AgentRun).filter(
            AgentRun.opportunity_id == opportunity_id
        ).order_by(AgentRun.created_at.desc()).first()

        if not agent_run or not agent_run.proposed_plan:
            raise ValueError("No recovery plan available for this opportunity. Run AI Agent first.")

        plan_dict = agent_run.proposed_plan
        proposed_actions = plan_dict.get("proposed_actions", [])
        created_actions = []

        for p_act in proposed_actions:
            action_type_str = p_act.get("action_type")
            try:
                action_type_enum = ActionType(action_type_str)
            except ValueError:
                action_type_enum = ActionType.MANUAL_REVIEW

            act = self.create_action(
                opportunity_id=opportunity_id,
                action_type=action_type_enum,
                parameters=p_act.get("parameters", {}),
                recovery_plan_id=plan_dict.get("plan_id"),
                agent_run_id=str(agent_run.id),
            )
            created_actions.append(act)

        return created_actions

    def authorize_action(self, action_id: str, force_reevaluate: bool = False) -> Tuple[RecoveryAction, PolicyDecision]:
        """Evaluate deterministic policy and update authorization status."""
        action = self._get_action_by_id(action_id)

        # Transition to POLICY_CHECK
        if action.status == ActionStatus.PROPOSED or force_reevaluate:
            ActionStateMachine.transition(action.status, ActionStatus.POLICY_CHECK)
            action.status = ActionStatus.POLICY_CHECK

        decision: PolicyDecision = self.authorization_service.evaluate_action(action)
        action.policy_decision = decision.model_dump(mode="json")
        action.policy_version = decision.policy_version

        if decision.decision == PolicyStatus.ALLOWED:
            ActionStateMachine.transition(action.status, ActionStatus.AUTHORIZED)
            action.status = ActionStatus.AUTHORIZED
            action.authorized_at = datetime.utcnow()
            event_type = AuditEventType.POLICY_DECISION
        elif decision.decision == PolicyStatus.REQUIRES_APPROVAL:
            ActionStateMachine.transition(action.status, ActionStatus.REQUIRES_APPROVAL)
            action.status = ActionStatus.REQUIRES_APPROVAL
            event_type = AuditEventType.POLICY_DECISION
        else:
            ActionStateMachine.transition(action.status, ActionStatus.BLOCKED)
            action.status = ActionStatus.BLOCKED
            event_type = AuditEventType.POLICY_DECISION

        self._record_audit(
            entity_type="RecoveryAction",
            entity_id=action.id,
            event_type=event_type,
            metadata={
                "action_id": action.action_id,
                "decision": decision.decision.value,
                "reasons": decision.reasons,
                "rules": decision.applicable_rules,
            },
        )

        self.db.commit()
        self.db.refresh(action)
        logger.info(f"action_policy_evaluated action_id={action.action_id} status={action.status.value}")
        return action, decision

    async def execute_action(
        self,
        action_id: str,
        custom_idempotency_key: Optional[str] = None,
        simulation_override: Optional[str] = None,
    ) -> ExecutionResultResponse:
        """Securely execute an authorized recovery action."""
        action = self._get_action_by_id(action_id)

        # 1. Verify action state is executable
        if action.status not in [ActionStatus.AUTHORIZED, ActionStatus.RETRYABLE]:
            # If proposed, attempt automatic authorization
            if action.status == ActionStatus.PROPOSED:
                action, decision = self.authorize_action(action_id)
                if action.status != ActionStatus.AUTHORIZED:
                    return ExecutionResultResponse(
                        action_id=action.action_id,
                        status=action.status,
                        success=False,
                        error_code="POLICY_AUTHORIZATION_FAILED",
                        error_message="; ".join(decision.reasons),
                        message=f"Action authorization failed: {decision.decision.value}",
                    )
            else:
                return ExecutionResultResponse(
                    action_id=action.action_id,
                    status=action.status,
                    success=False,
                    error_code="INVALID_STATE",
                    error_message=f"Cannot execute action in '{action.status.value}' state. Must be AUTHORIZED or RETRYABLE.",
                    message="Action is not eligible for execution.",
                )

        # 2. Re-evaluate policy immediately prior to execution (Freshness guard)
        fresh_decision = self.authorization_service.evaluate_action(action)
        if fresh_decision.decision != PolicyStatus.ALLOWED:
            action.status = ActionStatus.BLOCKED
            action.policy_decision = fresh_decision.model_dump(mode="json")
            self.db.commit()
            return ExecutionResultResponse(
                action_id=action.action_id,
                status=ActionStatus.BLOCKED,
                success=False,
                error_code="POLICY_RECHECK_FAILED",
                error_message="; ".join(fresh_decision.reasons),
                message="Pre-execution policy verification blocked the action.",
            )

        # 3. Idempotency Key Determination
        attempt_number = action.execution_attempts_count + 1
        idempotency_key = custom_idempotency_key or f"{action.idempotency_key}_att{attempt_number}"

        # 4. Check for existing completed attempt with same key (Idempotency duplicate guard)
        existing_attempt = self.db.query(ExecutionAttempt).filter(
            ExecutionAttempt.idempotency_key == idempotency_key
        ).first()

        if existing_attempt and existing_attempt.status == ExecutionAttemptStatus.SUCCESS:
            logger.info(f"duplicate_execution_intercepted key={idempotency_key}")
            return ExecutionResultResponse(
                action_id=action.action_id,
                status=ActionStatus.SUCCEEDED,
                success=True,
                recovered_amount_minor=action.payment.amount_minor if action.payment else None,
                provider_reference=existing_attempt.provider_reference,
                latency_ms=0,
                attempt_number=existing_attempt.attempt_number,
                message="Idempotent duplicate request: Returned cached successful execution result.",
            )

        # 5. Create ExecutionAttempt record and mark action EXECUTING
        ActionStateMachine.transition(action.status, ActionStatus.EXECUTING)
        action.status = ActionStatus.EXECUTING
        action.started_at = action.started_at or datetime.utcnow()
        action.execution_attempts_count = attempt_number

        adapter_name = "MockPaymentAdapter" if action.action_type in [ActionType.RETRY_PAYMENT, ActionType.WAIT_AND_RETRY] else "MockCommunicationAdapter"
        attempt = ExecutionAttempt(
            action_id=action.id,
            attempt_number=attempt_number,
            idempotency_key=idempotency_key,
            adapter_name=adapter_name,
            status=ExecutionAttemptStatus.EXECUTING,
            request_payload={
                "action_type": action.action_type.value,
                "parameters": action.parameters,
                "payment_id": str(action.payment_id),
                "amount": action.payment.amount_minor if action.payment else 0,
            },
            started_at=datetime.utcnow(),
        )
        self.db.add(attempt)
        self.db.commit()
        self.db.refresh(action)

        # 6. Call Provider Adapter
        payment: Payment = self.db.query(Payment).filter(Payment.id == action.payment_id).first()
        try:
            if adapter_name == "MockPaymentAdapter":
                provider_result: ProviderResult = await self.payment_adapter.execute_retry(
                    payment=payment,
                    action=action,
                    attempt_number=attempt_number,
                    idempotency_key=idempotency_key,
                    simulation_override=simulation_override,
                )
            else:
                provider_result: ProviderResult = await self.communication_adapter.send_message(
                    payment=payment,
                    action=action,
                    template_name="PAYMENT_RECOVERY_REMINDER",
                    parameters=action.parameters or {},
                    idempotency_key=idempotency_key,
                )

        except Exception as e:
            logger.error(f"adapter_unexpected_exception error={str(e)}")
            provider_result = ProviderResult(
                success=False,
                error_code="ADAPTER_EXCEPTION",
                error_message=str(e),
                is_retryable=False,
                is_unknown=True,
            )

        # 7. Process Provider Result & Update Domain State
        attempt.completed_at = datetime.utcnow()
        attempt.response_payload = provider_result.raw_payload
        attempt.provider_reference = provider_result.provider_reference
        attempt.error_code = provider_result.error_code
        attempt.error_message = provider_result.error_message
        attempt.is_retryable = provider_result.is_retryable
        attempt.execution_latency_ms = provider_result.latency_ms

        action.last_result = provider_result.model_dump(mode="json")
        action.provider_reference = provider_result.provider_reference or action.provider_reference
        action.last_error_code = provider_result.error_code
        action.last_error_message = provider_result.error_message

        if provider_result.success:
            # Succeeded
            attempt.status = ExecutionAttemptStatus.SUCCESS
            ActionStateMachine.transition(action.status, ActionStatus.SUCCEEDED)
            action.status = ActionStatus.SUCCEEDED
            action.completed_at = datetime.utcnow()

            # Update Payment & Financial Truth
            if payment and action.action_type in [ActionType.RETRY_PAYMENT, ActionType.WAIT_AND_RETRY]:
                payment.transition_to(PaymentStatus.CAPTURED)
                # Create successful PaymentAttempt
                current_attempt_num = (len(payment.attempts) + 1) if payment.attempts else attempt_number
                new_attempt = PaymentAttempt(
                    payment_id=payment.id,
                    attempt_number=current_attempt_num,
                    status=PaymentStatus.CAPTURED,
                    method=payment.method or "card",
                    started_at=datetime.utcnow(),
                    completed_at=datetime.utcnow(),
                )
                self.db.add(new_attempt)

                # Resolve RecoveryCase
                recovery_case = self.db.query(RecoveryCase).filter(RecoveryCase.payment_id == payment.id).first()
                if recovery_case:
                    recovery_case.status = RecoveryCaseStatus.RESOLVED

            self._record_audit(
                entity_type="RecoveryAction",
                entity_id=action.id,
                event_type=AuditEventType.ACTION_EXECUTED,
                metadata={
                    "status": "SUCCEEDED",
                    "provider_reference": provider_result.provider_reference,
                    "attempt": attempt_number,
                    "amount_recovered": payment.amount_minor if payment else 0,
                },
            )
            self._record_audit(
                entity_type="Payment",
                entity_id=payment.id,
                event_type=AuditEventType.RECOVERY_VERIFIED,
                metadata={"recovered_by_action": action.action_id, "provider_ref": provider_result.provider_reference},
            )

            self._record_learning_outcome(
                action=action,
                payment=payment,
                outcome_status=ActionStatus.SUCCEEDED,
                latency_ms=provider_result.latency_ms,
            )

            self.db.commit()
            return ExecutionResultResponse(
                action_id=action.action_id,
                status=ActionStatus.SUCCEEDED,
                success=True,
                recovered_amount_minor=payment.amount_minor if payment else 0,
                provider_reference=provider_result.provider_reference,
                latency_ms=provider_result.latency_ms,
                attempt_number=attempt_number,
                message=f"Recovery action executed successfully. Payment captured under reference {provider_result.provider_reference}.",
            )

        elif provider_result.is_unknown:
            # Timeout / Unknown status -> Forbid blind retry
            attempt.status = ExecutionAttemptStatus.UNKNOWN
            ActionStateMachine.transition(action.status, ActionStatus.UNKNOWN)
            action.status = ActionStatus.UNKNOWN

            self._record_audit(
                entity_type="RecoveryAction",
                entity_id=action.id,
                event_type=AuditEventType.ACTION_EXECUTED,
                metadata={"status": "UNKNOWN", "error": provider_result.error_message, "attempt": attempt_number},
            )
            self._record_learning_outcome(
                action=action,
                payment=payment,
                outcome_status=ActionStatus.UNKNOWN,
                latency_ms=provider_result.latency_ms,
            )
            self.db.commit()
            return ExecutionResultResponse(
                action_id=action.action_id,
                status=ActionStatus.UNKNOWN,
                success=False,
                is_unknown=True,
                is_retryable=False,
                error_code=provider_result.error_code,
                error_message=provider_result.error_message,
                latency_ms=provider_result.latency_ms,
                attempt_number=attempt_number,
                message="Provider timeout: Outcome unconfirmed. Blind retries disabled. Reconciliation required.",
            )

        else:
            # Failed
            attempt.status = ExecutionAttemptStatus.FAILURE
            if provider_result.is_retryable and attempt_number < action.max_attempts:
                ActionStateMachine.transition(action.status, ActionStatus.RETRYABLE)
                action.status = ActionStatus.RETRYABLE
            else:
                ActionStateMachine.transition(action.status, ActionStatus.FAILED)
                action.status = ActionStatus.FAILED
                action.completed_at = datetime.utcnow()

            self._record_audit(
                entity_type="RecoveryAction",
                entity_id=action.id,
                event_type=AuditEventType.ACTION_EXECUTED,
                metadata={
                    "status": action.status.value,
                    "error_code": provider_result.error_code,
                    "attempt": attempt_number,
                },
            )
            self._record_learning_outcome(
                action=action,
                payment=payment,
                outcome_status=action.status,
                latency_ms=provider_result.latency_ms,
            )
            self.db.commit()
            return ExecutionResultResponse(
                action_id=action.action_id,
                status=action.status,
                success=False,
                is_retryable=provider_result.is_retryable,
                error_code=provider_result.error_code,
                error_message=provider_result.error_message,
                latency_ms=provider_result.latency_ms,
                attempt_number=attempt_number,
                message=f"Recovery execution failed: {provider_result.error_message or provider_result.error_code}",
            )

    async def reconcile_action(self, action_id: str) -> RecoveryAction:
        """Reconcile an action with UNKNOWN outcome by querying provider status."""
        action = self._get_action_by_id(action_id)
        if action.status != ActionStatus.UNKNOWN:
            raise ValueError(f"Action '{action.action_id}' is not in UNKNOWN status.")

        ref = action.provider_reference or f"mock_rec_{action.idempotency_key[-8:]}"
        result = await self.payment_adapter.check_transaction_status(ref)

        payment = self.db.query(Payment).filter(Payment.id == action.payment_id).first()
        if result.success:
            action.status = ActionStatus.SUCCEEDED
            action.completed_at = datetime.utcnow()
            if payment:
                payment.transition_to(PaymentStatus.CAPTURED)
                recovery_case = self.db.query(RecoveryCase).filter(RecoveryCase.payment_id == payment.id).first()
                if recovery_case:
                    recovery_case.status = RecoveryCaseStatus.RESOLVED
        else:
            action.status = ActionStatus.FAILED
            action.completed_at = datetime.utcnow()

        self._record_learning_outcome(
            action=action,
            payment=payment,
            outcome_status=action.status,
            latency_ms=result.latency_ms if hasattr(result, 'latency_ms') else 100,
        )

        self._record_audit(
            entity_type="RecoveryAction",
            entity_id=action.id,
            event_type=AuditEventType.ACTION_EXECUTED,
            metadata={"event_subtype": "ACTION_RECONCILED", "reconciled_status": action.status.value, "provider_ref": ref},
        )
        self.db.commit()
        self.db.refresh(action)
        logger.info(f"action_reconciled action_id={action.action_id} final_status={action.status.value}")
        return action

    def cancel_action(self, action_id: str, reason: str = "Cancelled by operator") -> RecoveryAction:
        """Safely cancel a pending recovery action."""
        action = self._get_action_by_id(action_id)
        ActionStateMachine.transition(action.status, ActionStatus.CANCELLED)
        action.status = ActionStatus.CANCELLED
        action.completed_at = datetime.utcnow()
        action.last_error_message = reason

        self._record_audit(
            entity_type="RecoveryAction",
            entity_id=action.id,
            event_type=AuditEventType.ACTION_EXECUTED,
            metadata={"event_subtype": "ACTION_CANCELLED", "reason": reason},
        )
        self.db.commit()
        self.db.refresh(action)
        return action

    def list_actions(
        self,
        status: Optional[str] = None,
        action_type: Optional[str] = None,
        opportunity_id: Optional[str] = None,
        payment_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[RecoveryAction], int]:
        """List recovery actions with filtering and pagination."""
        query = self.db.query(RecoveryAction)
        if status:
            query = query.filter(RecoveryAction.status == status)
        if action_type:
            query = query.filter(RecoveryAction.action_type == action_type)
        if opportunity_id:
            query = query.filter(RecoveryAction.opportunity_id == opportunity_id)
        if payment_id:
            query = query.filter(RecoveryAction.payment_id == payment_id)

        total = query.count()
        actions = query.order_by(RecoveryAction.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        return actions, total

    def get_action(self, action_id: str) -> RecoveryAction:
        """Get recovery action by action_id or UUID string."""
        return self._get_action_by_id(action_id)

    def _get_action_by_id(self, action_id: str) -> RecoveryAction:
        query = self.db.query(RecoveryAction)
        action = query.filter(RecoveryAction.action_id == action_id).first()
        if not action:
            try:
                uuid_obj = uuid.UUID(action_id)
                action = query.filter(RecoveryAction.id == uuid_obj).first()
            except ValueError:
                pass
        if not action:
            raise ValueError(f"Recovery action '{action_id}' not found.")
        return action

    def _record_audit(self, entity_type: str, entity_id: uuid.UUID, event_type: AuditEventType, metadata: Dict[str, Any]):
        audit = AuditEvent(
            entity_type=entity_type,
            entity_id=entity_id,
            event_type=event_type,
            actor_type=ActorType.SYSTEM,
            audit_metadata=metadata,
        )
        self.db.add(audit)

    def _record_learning_outcome(
        self,
        action: RecoveryAction,
        payment: Optional[Payment],
        outcome_status: ActionStatus,
        latency_ms: int,
    ) -> Optional[LearningOutcomeRecord]:
        """Record a closed-loop LearningOutcomeRecord for adaptive strategy calibration."""
        try:
            category = FailureCategory.UNKNOWN
            if action.opportunity_id:
                opp = self.db.query(RevenueIntelligenceResult).filter(
                    RevenueIntelligenceResult.id == action.opportunity_id
                ).first()
                if opp and opp.failure_category:
                    category = opp.failure_category
            elif payment and payment.failure_code:
                category = FailureCategory.BANK_FAILURE

            record = LearningOutcomeRecord(
                merchant_id=action.merchant_id,
                payment_id=action.payment_id,
                recovery_action_id=action.id,
                failure_category=category,
                action_type=action.action_type,
                amount_minor=payment.amount_minor if payment else 0,
                retry_count=action.execution_attempts_count,
                payment_method=payment.method if payment else "card",
                outcome_status=outcome_status,
                execution_latency_ms=latency_ms,
                occurred_at=datetime.utcnow(),
                context_metadata={
                    "action_id": action.action_id,
                    "idempotency_key": action.idempotency_key,
                    "provider_reference": action.provider_reference,
                },
            )
            self.db.add(record)
            return record
        except Exception as ex:
            logger.error(f"failed_to_record_learning_outcome error={str(ex)}")
            return None
