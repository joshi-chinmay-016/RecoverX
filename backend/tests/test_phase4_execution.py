"""Unit and Integration Tests for Phase 4 Controlled Recovery Action Execution."""

import pytest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock

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
def mock_db_session(mocker):
    """Create a mock database session."""
    session = mocker.MagicMock()
    return session


@pytest.fixture
def sample_merchant():
    return Merchant(
        id=uuid.uuid4(),
        external_id="merch_test_1",
        name="Test Merchant",
        is_active=True,
    )


@pytest.fixture
def sample_payment(sample_merchant):
    payment_id = uuid.uuid4()
    return Payment(
        id=payment_id,
        razorpay_payment_id=f"pay_test_{uuid.uuid4().hex[:8]}",
        merchant_id=sample_merchant.id,
        amount_minor=2500000,
        currency="INR",
        status=PaymentStatus.FAILED,
        method="upi",
        failure_code="BANK_GATEWAY_TIMEOUT",
        failure_description="Transaction timed out at acquiring bank",
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
def sample_opportunity(sample_payment):
    return RevenueIntelligenceResult(
        id=uuid.uuid4(),
        payment_id=sample_payment.id,
        merchant_id=sample_payment.merchant_id,
        failure_category="TEMPORARY_FAILURE",
        recovery_likelihood=0.85,
        opportunity_score=90.0,
        priority="HIGH",
        recommended_intervention="WAIT_AND_RETRY",
        explanation="Temporary network issue with high recovery probability",
        is_actionable=True,
    )


@pytest.fixture
def sample_action(sample_payment, sample_opportunity):
    return RecoveryAction(
        id=uuid.uuid4(),
        action_id=f"ACT-{uuid.uuid4().hex[:8].upper()}",
        opportunity_id=sample_opportunity.id,
        payment_id=sample_payment.id,
        merchant_id=sample_payment.merchant_id,
        action_type=ActionType.RETRY_PAYMENT,
        status=ActionStatus.PROPOSED,
        parameters={"delay_minutes": 0},
        idempotency_key=f"idem_test_{uuid.uuid4().hex[:8]}",
        execution_attempts_count=0,
        max_attempts=3,
        policy_version="policy-v1",
        execution_version="execution-v1",
        requested_at=datetime.utcnow(),
    )


# ==============================================================================
# 1. State Machine Tests
# ==============================================================================

def test_state_machine_valid_transitions():
    """Verify standard valid state transitions."""
    assert ActionStateMachine.transition(ActionStatus.PROPOSED, ActionStatus.POLICY_CHECK) == ActionStatus.POLICY_CHECK
    assert ActionStateMachine.transition(ActionStatus.POLICY_CHECK, ActionStatus.AUTHORIZED) == ActionStatus.AUTHORIZED
    assert ActionStateMachine.transition(ActionStatus.AUTHORIZED, ActionStatus.EXECUTING) == ActionStatus.EXECUTING
    assert ActionStateMachine.transition(ActionStatus.EXECUTING, ActionStatus.SUCCEEDED) == ActionStatus.SUCCEEDED


def test_state_machine_retryable_transitions():
    """Verify retryable failure transitions."""
    assert ActionStateMachine.transition(ActionStatus.EXECUTING, ActionStatus.RETRYABLE) == ActionStatus.RETRYABLE
    assert ActionStateMachine.transition(ActionStatus.RETRYABLE, ActionStatus.EXECUTING) == ActionStatus.EXECUTING


def test_state_machine_forbidden_transitions():
    """Verify that illegal transitions raise InvalidStateTransitionError."""
    # Blocked cannot jump to executing
    with pytest.raises(InvalidStateTransitionError):
        ActionStateMachine.transition(ActionStatus.BLOCKED, ActionStatus.EXECUTING)

    # Succeeded cannot execute again (Terminal state)
    with pytest.raises(InvalidStateTransitionError):
        ActionStateMachine.transition(ActionStatus.SUCCEEDED, ActionStatus.EXECUTING)

    # Cancelled cannot execute
    with pytest.raises(InvalidStateTransitionError):
        ActionStateMachine.transition(ActionStatus.CANCELLED, ActionStatus.EXECUTING)


# ==============================================================================
# 2. Deterministic Authorization Engine Tests
# ==============================================================================

def test_authorization_allowed_for_eligible_failed_payment(mocker, sample_payment, sample_recovery_case, sample_action):
    """Eligible failed payment with low retry count must be ALLOWED."""
    mock_db = mocker.MagicMock()
    mock_db.query.return_value.filter.return_value.first.side_effect = [
        sample_payment,       # query Payment
        sample_recovery_case, # query RecoveryCase
    ]

    auth_service = AuthorizationService(mock_db)
    decision = auth_service.evaluate_action(sample_action)

    assert decision.decision == PolicyStatus.ALLOWED
    assert "payment_status_eligibility" in decision.applicable_rules
    assert "max_retry_limit_rule" in decision.applicable_rules


def test_authorization_blocks_already_captured_payment(mocker, sample_payment, sample_recovery_case, sample_action):
    """Payment that is already CAPTURED must be BLOCKED from recovery execution."""
    sample_payment.status = PaymentStatus.CAPTURED
    mock_db = mocker.MagicMock()
    mock_db.query.return_value.filter.return_value.first.side_effect = [
        sample_payment,
        sample_recovery_case,
    ]

    auth_service = AuthorizationService(mock_db)
    decision = auth_service.evaluate_action(sample_action)

    assert decision.decision == PolicyStatus.BLOCKED
    assert any("already captured" in r.lower() for r in decision.reasons)


def test_authorization_blocks_when_max_retries_exceeded(mocker, sample_payment, sample_recovery_case, sample_action):
    """Actions exceeding maximum allowed retry attempts must be BLOCKED."""
    sample_action.execution_attempts_count = 3  # Max limit reached
    mock_db = mocker.MagicMock()
    mock_db.query.return_value.filter.return_value.first.side_effect = [
        sample_payment,
        sample_recovery_case,
    ]

    auth_service = AuthorizationService(mock_db)
    decision = auth_service.evaluate_action(sample_action)

    assert decision.decision == PolicyStatus.BLOCKED
    assert any("maximum retry attempt limit reached" in r.lower() for r in decision.reasons)


def test_authorization_blocks_merchant_isolation_breach(mocker, sample_payment, sample_recovery_case, sample_action):
    """Action requested with mismatched merchant_id must be strictly BLOCKED."""
    sample_action.merchant_id = uuid.uuid4()  # Mismatched merchant
    mock_db = mocker.MagicMock()
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
async def test_execution_success_updates_payment_and_case(mocker, sample_payment, sample_recovery_case, sample_action):
    """Successful execution must capture the payment and resolve the recovery case."""
    sample_action.status = ActionStatus.AUTHORIZED
    sample_action.payment = sample_payment

    mock_db = mocker.MagicMock()
    # Mock queries: 1) action lookup, 2) auth payment, 3) auth case, 4) idempotency check, 5) exec payment, 6) recovery case
    mock_db.query.return_value.filter.return_value.first.side_effect = [
        sample_action,
        sample_payment,
        sample_recovery_case,
        None,  # No existing attempt (idempotency check)
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
async def test_execution_idempotency_duplicate_safety(mocker, sample_payment, sample_recovery_case, sample_action):
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

    mock_db = mocker.MagicMock()
    mock_db.query.return_value.filter.return_value.first.side_effect = [
        sample_action,
        sample_payment,
        sample_recovery_case,
        existing_successful_attempt,  # Existing attempt found!
    ]

    mock_adapter = mocker.MagicMock()
    service = ExecutionService(mock_db, payment_adapter=mock_adapter)

    result = await service.execute_action(sample_action.action_id, custom_idempotency_key="idem_fixed_key")

    assert result.success is True
    assert result.provider_reference == "mock_pay_cached_9999"
    assert "Idempotent duplicate request" in result.message
    # Adapter was NOT called because of idempotency interception
    mock_adapter.execute_retry.assert_not_called()


@pytest.mark.asyncio
async def test_execution_timeout_marks_unknown_and_blocks_blind_retry(mocker, sample_payment, sample_recovery_case, sample_action):
    """Provider timeout marks action as UNKNOWN and strictly prevents blind retries."""
    sample_action.status = ActionStatus.AUTHORIZED
    sample_action.payment = sample_payment

    mock_db = mocker.MagicMock()
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
    # Payment status remains unchanged (NOT captured)
    assert sample_payment.status == PaymentStatus.FAILED


@pytest.mark.asyncio
async def test_reconciliation_resolves_unknown_action(mocker, sample_payment, sample_recovery_case, sample_action):
    """Reconciling an UNKNOWN action queries provider and updates financial truth safely."""
    sample_action.status = ActionStatus.UNKNOWN
    sample_action.provider_reference = "mock_pay_rec_1234"

    mock_db = mocker.MagicMock()
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
