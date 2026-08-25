"""Unit and Integration Tests for Phase 4 Controlled Recovery Action Execution."""

import pytest
import uuid
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock

from app.db.base import (
    PaymentStatus,
    RecoveryCaseStatus,
    ActionStatus,
    ExecutionAttemptStatus,
    PolicyStatus,
)
from app.db.models.merchant import Merchant
from app.db.models.customer import Customer
from app.db.models.payment import Payment
from app.db.models.recovery_case import RecoveryCase
from app.db.models.revenue_intelligence import RevenueIntelligenceResult
from app.db.models.recovery_action import RecoveryAction
from app.db.models.execution_attempt import ExecutionAttempt
from app.agent.schemas import ActionType
from app.execution.state_machine import ActionStateMachine, InvalidStateTransitionError
from app.execution.authorization import AuthorizationService
from app.execution.service import ExecutionService
from app.execution.adapters.mock_payment import MockPaymentAdapter
from app.execution.schemas import ProviderResult


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    session = MagicMock()
    return session


@pytest.fixture
def sample_merchant():
    return Merchant(
        id=uuid.uuid4(),
        external_id="merch_test_1",
        name="Test Merchant",
        currency="INR",
    )


@pytest.fixture
def sample_payment(sample_merchant):
    payment_id = uuid.uuid4()
    return Payment(
        id=payment_id,
        merchant_id=sample_merchant.id,
        razorpay_payment_id="pay_test_phase4_123",
        amount_minor=2500000,
        currency="INR",
        method="upi",
        status=PaymentStatus.FAILED,
        failure_code="BAD_REQUEST_ERROR",
        failure_description="Bank technical error",
    )


@pytest.fixture
def sample_recovery_case(sample_payment):
    return RecoveryCase(
        id=uuid.uuid4(),
        payment_id=sample_payment.id,
        status=RecoveryCaseStatus.OPEN,
        amount_at_risk_minor=2500000,
    )


@pytest.fixture
def sample_action(sample_merchant, sample_payment):
    return RecoveryAction(
        id=uuid.uuid4(),
        action_id="ACT-UNITTEST-001",
        opportunity_id=uuid.uuid4(),
        merchant_id=sample_merchant.id,
        payment_id=sample_payment.id,
        action_type=ActionType.RETRY_PAYMENT,
        status=ActionStatus.PROPOSED,
        idempotency_key=f"idem_act_test_001",
        execution_attempts_count=0,
        max_attempts=3,
        parameters={"reason": "Deterministic automated retry"},
    )


# ==============================================================================
# 1. State Machine Transition Tests
# ==============================================================================

def test_state_machine_valid_happy_path_transitions():
    """Verify standard happy-path lifecycle: PROPOSED -> POLICY_CHECK -> AUTHORIZED -> QUEUED -> EXECUTING -> SUCCEEDED."""
    s1 = ActionStateMachine.transition(ActionStatus.PROPOSED, ActionStatus.POLICY_CHECK)
    assert s1 == ActionStatus.POLICY_CHECK

    s2 = ActionStateMachine.transition(ActionStatus.POLICY_CHECK, ActionStatus.AUTHORIZED)
    assert s2 == ActionStatus.AUTHORIZED

    s3 = ActionStateMachine.transition(ActionStatus.AUTHORIZED, ActionStatus.QUEUED)
    assert s3 == ActionStatus.QUEUED

    s4 = ActionStateMachine.transition(ActionStatus.QUEUED, ActionStatus.EXECUTING)
    assert s4 == ActionStatus.EXECUTING

    s5 = ActionStateMachine.transition(ActionStatus.EXECUTING, ActionStatus.SUCCEEDED)
    assert s5 == ActionStatus.SUCCEEDED
    assert ActionStateMachine.is_terminal(s5) is True


def test_state_machine_policy_block_transition():
    """Verify policy engine rejection: POLICY_CHECK -> BLOCKED."""
    s = ActionStateMachine.transition(ActionStatus.POLICY_CHECK, ActionStatus.BLOCKED)
    assert s == ActionStatus.BLOCKED
    assert ActionStateMachine.is_terminal(s) is True


def test_state_machine_timeout_to_unknown_transition():
    """Verify timeout scenario: EXECUTING -> UNKNOWN."""
    s = ActionStateMachine.transition(ActionStatus.EXECUTING, ActionStatus.UNKNOWN)
    assert s == ActionStatus.UNKNOWN
    assert ActionStateMachine.is_terminal(s) is False

    s_rec = ActionStateMachine.transition(ActionStatus.UNKNOWN, ActionStatus.SUCCEEDED)
    assert s_rec == ActionStatus.SUCCEEDED


def test_state_machine_retryable_transitions():
    """Verify retryable failure transitions."""
    assert ActionStateMachine.transition(ActionStatus.EXECUTING, ActionStatus.RETRYABLE) == ActionStatus.RETRYABLE
    assert ActionStateMachine.transition(ActionStatus.RETRYABLE, ActionStatus.EXECUTING) == ActionStatus.EXECUTING


def test_state_machine_forbidden_transitions():
    """Verify that illegal transitions raise InvalidStateTransitionError."""
    with pytest.raises(InvalidStateTransitionError):
        ActionStateMachine.transition(ActionStatus.BLOCKED, ActionStatus.EXECUTING)

    with pytest.raises(InvalidStateTransitionError):
        ActionStateMachine.transition(ActionStatus.SUCCEEDED, ActionStatus.EXECUTING)

    with pytest.raises(InvalidStateTransitionError):
        ActionStateMachine.transition(ActionStatus.CANCELLED, ActionStatus.EXECUTING)


# ==============================================================================
# 2. Deterministic Authorization Engine Tests
# ==============================================================================

def test_authorization_allowed_for_eligible_failed_payment(sample_payment, sample_recovery_case, sample_action):
    """Eligible failed payment with low retry count must be ALLOWED."""
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.side_effect = [
        sample_payment,       # query Payment
        sample_recovery_case, # query RecoveryCase
    ]

    auth_service = AuthorizationService(mock_db)
    decision = auth_service.evaluate_action(sample_action)

    assert decision.decision == PolicyStatus.ALLOWED
    assert "payment_status_eligibility" in decision.applicable_rules
    assert "max_retry_limit_rule" in decision.applicable_rules


def test_authorization_blocks_already_captured_payment(sample_payment, sample_recovery_case, sample_action):
    """Payment that is already CAPTURED must be BLOCKED from recovery execution."""
    sample_payment.status = PaymentStatus.CAPTURED
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.side_effect = [
        sample_payment,
        sample_recovery_case,
    ]

    auth_service = AuthorizationService(mock_db)
    decision = auth_service.evaluate_action(sample_action)

    assert decision.decision == PolicyStatus.BLOCKED
    assert any("already captured" in r.lower() for r in decision.reasons)


def test_authorization_blocks_when_max_retries_exceeded(sample_payment, sample_recovery_case, sample_action):
    """Actions exceeding maximum allowed retry attempts must be BLOCKED."""
    sample_action.execution_attempts_count = 3
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.side_effect = [
        sample_payment,
        sample_recovery_case,
    ]

    auth_service = AuthorizationService(mock_db)
    decision = auth_service.evaluate_action(sample_action)

    assert decision.decision == PolicyStatus.BLOCKED
    assert any("maximum retry attempt limit reached" in r.lower() for r in decision.reasons)


def test_authorization_blocks_merchant_isolation_breach(sample_payment, sample_recovery_case, sample_action):
    """Action requested with mismatched merchant_id must be strictly BLOCKED."""
    sample_action.merchant_id = uuid.uuid4()
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.side_effect = [
        sample_payment,
        sample_recovery_case,
    ]

    auth_service = AuthorizationService(mock_db)
    decision = auth_service.evaluate_action(sample_action)

    assert decision.decision == PolicyStatus.BLOCKED
    assert any("merchant" in r.lower() for r in decision.reasons)


# ==============================================================================
# 3. Execution Service & Idempotency Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_execution_success_updates_payment_and_case(sample_payment, sample_recovery_case, sample_action):
    """Successful execution must capture the payment and resolve the recovery case."""
    sample_action.status = ActionStatus.AUTHORIZED
    sample_action.payment = sample_payment

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.side_effect = [
        sample_action,
        sample_payment,
        sample_recovery_case,
        None,
        sample_payment,
        sample_recovery_case,
    ]

    mock_adapter = MockPaymentAdapter(simulated_latency_ms=0)
    service = ExecutionService(mock_db, payment_adapter=mock_adapter)

    result = await service.execute_action(sample_action.action_id, simulation_override="SUCCESS")

    assert result.success is True
    assert result.status == ActionStatus.SUCCEEDED
    assert result.provider_reference.startswith("mock_pay_")
    assert sample_payment.status == PaymentStatus.CAPTURED
    assert sample_recovery_case.status == RecoveryCaseStatus.RESOLVED


@pytest.mark.asyncio
async def test_execution_idempotency_duplicate_safety(sample_payment, sample_recovery_case, sample_action):
    """Duplicate execution with identical idempotency key returns cached result without calling provider twice."""
    sample_action.status = ActionStatus.AUTHORIZED
    sample_action.payment = sample_payment

    existing_successful_attempt = ExecutionAttempt(
        id=uuid.uuid4(),
        action_id=sample_action.id,
        attempt_number=1,
        idempotency_key="idem_fixed_key",
        adapter_name="MockPaymentAdapter",
        status=ExecutionAttemptStatus.SUCCESS,
        provider_reference="mock_pay_cached_9999",
    )

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.side_effect = [
        sample_action,
        sample_payment,
        sample_recovery_case,
        existing_successful_attempt,
    ]

    mock_adapter = MagicMock()
    service = ExecutionService(mock_db, payment_adapter=mock_adapter)

    result = await service.execute_action(sample_action.action_id, custom_idempotency_key="idem_fixed_key")

    assert result.success is True
    assert result.provider_reference == "mock_pay_cached_9999"
    assert "Idempotent duplicate request" in result.message
    mock_adapter.execute_retry.assert_not_called()


@pytest.mark.asyncio
async def test_execution_timeout_marks_unknown_and_blocks_blind_retry(sample_payment, sample_recovery_case, sample_action):
    """Provider timeout marks action as UNKNOWN and strictly prevents blind retries."""
    sample_action.status = ActionStatus.AUTHORIZED
    sample_action.payment = sample_payment

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.side_effect = [
        sample_action,
        sample_payment,
        sample_recovery_case,
        None,
        sample_payment,
    ]

    mock_adapter = MockPaymentAdapter(simulated_latency_ms=0)
    service = ExecutionService(mock_db, payment_adapter=mock_adapter)

    result = await service.execute_action(sample_action.action_id, simulation_override="TIMEOUT")

    assert result.success is False
    assert result.is_unknown is True
    assert result.is_retryable is False
    assert sample_action.status == ActionStatus.UNKNOWN
    assert sample_payment.status == PaymentStatus.FAILED


@pytest.mark.asyncio
async def test_reconciliation_resolves_unknown_action(sample_payment, sample_recovery_case, sample_action):
    """Reconciling an UNKNOWN action queries provider and updates financial truth safely."""
    sample_action.status = ActionStatus.UNKNOWN
    sample_action.provider_reference = "mock_pay_rec_1234"

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.side_effect = [
        sample_action,
        sample_payment,
        sample_recovery_case,
    ]

    mock_adapter = MockPaymentAdapter(simulated_latency_ms=0)
    service = ExecutionService(mock_db, payment_adapter=mock_adapter)

    reconciled = await service.reconcile_action(sample_action.action_id)

    assert reconciled.status == ActionStatus.SUCCEEDED
    assert sample_payment.status == PaymentStatus.CAPTURED
    assert sample_recovery_case.status == RecoveryCaseStatus.RESOLVED
