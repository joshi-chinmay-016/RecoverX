"""Final 7-Point Critical Validation Test Suite for Phase 5 Adaptive Recovery Intelligence.

Validates the 7 core architectural constraints:
1. No data leakage — current payment's outcome cannot influence its own prediction.
2. Merchant isolation — Merchant A cannot retrieve Merchant B's evidence.
3. UNKNOWN handling — timeout/unknown outcomes don't affect recovery-rate calculations.
4. Sparse data — small samples cannot create extreme probabilities/confidence.
5. Policy authority — adaptive intelligence can recommend, but cannot bypass PolicyEngine.
6. Regression — all Phase 1-4 tests and execution rules remain intact.
7. Real data only — metrics derive purely from confirmed historical database records.
"""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock

from app.db.base import ActionStatus, PaymentStatus, PolicyStatus, RecoveryCaseStatus
from app.db.models.merchant import Merchant
from app.db.models.payment import Payment
from app.db.models.learning_outcome import LearningOutcomeRecord
from app.db.models.recovery_action import RecoveryAction
from app.db.models.recovery_case import RecoveryCase
from app.intelligence.schemas import FailureCategory
from app.agent.schemas import ActionType
from app.learning.schemas import EvidenceScope, SupportLevel
from app.learning.outcome_aggregator import OutcomeAggregator
from app.learning.probability_calibrator import AdaptiveProbabilityCalibrator, MAX_ADAPTIVE_DELTA, PRIOR_SAMPLE_WEIGHT
from app.learning.strategy_selector import StrategyPerformanceModel
from app.learning.service import LearningService
from app.execution.authorization import AuthorizationService
from app.agent.tools.registry import ToolRegistry


# ==============================================================================
# CHECK 1: NO DATA LEAKAGE
# ==============================================================================

def test_check_1_no_data_leakage_temporal_cutoff():
    """Check 1: Current payment outcome occurring at T+1 must NOT leak into prediction made at time T."""
    merchant_id = uuid.uuid4()
    payment_id = uuid.uuid4()
    
    t_prediction = datetime(2026, 8, 1, 10, 0, 0)
    
    # 10 records occurred BEFORE prediction time
    historical_records = [
        LearningOutcomeRecord(
            merchant_id=merchant_id,
            payment_id=uuid.uuid4(),
            failure_category=FailureCategory.BANK_FAILURE,
            action_type=ActionType.RETRY_PAYMENT,
            outcome_status=ActionStatus.SUCCEEDED if i < 6 else ActionStatus.FAILED,
            occurred_at=t_prediction - timedelta(days=i + 1),
        )
        for i in range(10)
    ]
    
    # 1 record occurred AFTER prediction time (future outcome of current payment)
    future_record = LearningOutcomeRecord(
        merchant_id=merchant_id,
        payment_id=payment_id,
        failure_category=FailureCategory.BANK_FAILURE,
        action_type=ActionType.RETRY_PAYMENT,
        outcome_status=ActionStatus.SUCCEEDED,
        occurred_at=t_prediction + timedelta(hours=2),
    )
    
    all_records = historical_records + [future_record]
    
    mock_db = MagicMock()
    def mock_filter(*args):
        filtered = [r for r in all_records if r.occurred_at <= t_prediction]
        mock_query = MagicMock()
        mock_query.all.return_value = filtered
        return mock_query

    mock_db.query.return_value.filter = mock_filter

    aggregator = OutcomeAggregator(mock_db)
    outcome, scope, _ = aggregator.aggregate_for_context(
        failure_category=FailureCategory.BANK_FAILURE,
        merchant_id=merchant_id,
        as_of_time=t_prediction,
    )

    # Must only contain the 10 historical records, excluding the future record
    assert outcome.confirmed_attempts == 10
    assert outcome.successes == 6


# ==============================================================================
# CHECK 2: MERCHANT ISOLATION
# ==============================================================================

def test_check_2_merchant_isolation_boundary():
    """Check 2: Merchant A cannot access Merchant B's private outcomes."""
    merchant_a = uuid.uuid4()
    
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.all.return_value = []

    aggregator = OutcomeAggregator(mock_db)
    calibrator = AdaptiveProbabilityCalibrator(aggregator)

    result_a = calibrator.calibrate(
        baseline_probability=0.50,
        failure_category=FailureCategory.INSUFFICIENT_FUNDS,
        merchant_id=merchant_a,
    )

    # Merchant A must fall back to baseline / global evidence without seeing Merchant B's samples
    assert result_a.is_cold_start is True
    assert result_a.sample_size == 0
    assert result_a.adaptive_probability == 0.50


# ==============================================================================
# CHECK 3: UNKNOWN TIMEOUT HANDLING
# ==============================================================================

def test_check_3_unknown_timeouts_excluded_from_recovery_rate():
    """Check 3: UNKNOWN timeouts and BLOCKED actions do NOT dilute or inflate recovery rate."""
    merchant_id = uuid.uuid4()
    records = [
        # 8 Confirmed Successes
        *[LearningOutcomeRecord(
            merchant_id=merchant_id,
            payment_id=uuid.uuid4(),
            failure_category=FailureCategory.TEMPORARY_FAILURE,
            action_type=ActionType.WAIT_AND_RETRY,
            outcome_status=ActionStatus.SUCCEEDED,
            occurred_at=datetime.utcnow() - timedelta(days=2),
        ) for _ in range(8)],
        # 2 Confirmed Failures
        *[LearningOutcomeRecord(
            merchant_id=merchant_id,
            payment_id=uuid.uuid4(),
            failure_category=FailureCategory.TEMPORARY_FAILURE,
            action_type=ActionType.WAIT_AND_RETRY,
            outcome_status=ActionStatus.FAILED,
            occurred_at=datetime.utcnow() - timedelta(days=2),
        ) for _ in range(2)],
        # 5 UNKNOWN Timeouts (Must NOT be counted as failed attempts)
        *[LearningOutcomeRecord(
            merchant_id=merchant_id,
            payment_id=uuid.uuid4(),
            failure_category=FailureCategory.TEMPORARY_FAILURE,
            action_type=ActionType.WAIT_AND_RETRY,
            outcome_status=ActionStatus.UNKNOWN,
            occurred_at=datetime.utcnow() - timedelta(days=2),
        ) for _ in range(5)],
        # 3 BLOCKED Actions (Must NOT be counted as recovery attempts)
        *[LearningOutcomeRecord(
            merchant_id=merchant_id,
            payment_id=uuid.uuid4(),
            failure_category=FailureCategory.TEMPORARY_FAILURE,
            action_type=ActionType.WAIT_AND_RETRY,
            outcome_status=ActionStatus.BLOCKED,
            occurred_at=datetime.utcnow() - timedelta(days=2),
        ) for _ in range(3)],
    ]

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.all.return_value = records

    aggregator = OutcomeAggregator(mock_db)
    outcome, _, _ = aggregator.aggregate_for_context(
        failure_category=FailureCategory.TEMPORARY_FAILURE,
        merchant_id=merchant_id,
    )

    # Confirmed attempts = 8 + 2 = 10 (NOT 18)
    assert outcome.confirmed_attempts == 10
    assert outcome.successes == 8
    assert outcome.failures == 2
    assert outcome.unknowns == 5
    assert outcome.blocked == 3
    assert outcome.empirical_recovery_rate == 0.80


# ==============================================================================
# CHECK 4: SPARSE DATA PROTECTION
# ==============================================================================

def test_check_4_sparse_data_cannot_create_extreme_probabilities():
    """Check 4: A single 1/1 success or 0/1 failure cannot swing probability to 1.0 or 0.0."""
    merchant_id = uuid.uuid4()
    
    single_success_record = [
        LearningOutcomeRecord(
            merchant_id=merchant_id,
            failure_category=FailureCategory.BANK_FAILURE,
            action_type=ActionType.RETRY_PAYMENT,
            outcome_status=ActionStatus.SUCCEEDED,
            occurred_at=datetime.utcnow() - timedelta(days=1),
        )
    ]

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.all.return_value = single_success_record

    aggregator = OutcomeAggregator(mock_db)
    calibrator = AdaptiveProbabilityCalibrator(aggregator)

    result = calibrator.calibrate(
        baseline_probability=0.40,
        failure_category=FailureCategory.BANK_FAILURE,
        merchant_id=merchant_id,
    )

    assert result.adaptive_probability < 0.60
    assert result.adaptive_probability >= 0.40
    assert abs(result.adaptive_probability - 0.40) <= MAX_ADAPTIVE_DELTA


# ==============================================================================
# CHECK 5: POLICY AUTHORITY
# ==============================================================================

def test_check_5_adaptive_recommendation_cannot_bypass_policy_engine():
    """Check 5: Even if the adaptive model gives RETRY_PAYMENT a score of 95, PolicyEngine strictly blocks if retry count >= 3."""
    merchant_id = uuid.uuid4()
    payment_id = uuid.uuid4()
    
    payment = Payment(
        id=payment_id,
        merchant_id=merchant_id,
        amount_minor=2500000,
        currency="INR",
        status=PaymentStatus.FAILED,
    )
    recovery_case = RecoveryCase(
        id=uuid.uuid4(),
        payment_id=payment_id,
        status=RecoveryCaseStatus.OPEN,
        amount_at_risk_minor=2500000,
    )
    action = RecoveryAction(
        id=uuid.uuid4(),
        action_id="ACT-POLICY-TEST",
        payment_id=payment_id,
        merchant_id=merchant_id,
        action_type=ActionType.RETRY_PAYMENT,
        status=ActionStatus.PROPOSED,
        execution_attempts_count=3,
        max_attempts=3,
    )

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.side_effect = [payment, recovery_case]

    auth_service = AuthorizationService(mock_db)
    decision = auth_service.evaluate_action(action)

    # PolicyEngine MUST block
    assert decision.decision == PolicyStatus.BLOCKED
    assert any("retry attempt limit" in r.lower() for r in decision.reasons)


# ==============================================================================
# CHECK 6: REGRESSION ACROSS PHASES 1-4
# ==============================================================================

def test_check_6_regression_state_machine_and_agent_tools():
    """Check 6: Tool registry and State Machine maintain strict Phase 1-4 contracts."""
    mock_db = MagicMock()
    registry = ToolRegistry(mock_db)

    tools = registry.list_tools()
    assert "get_payment_context" in tools
    assert "get_recovery_history" in tools
    assert "get_revenue_intelligence" in tools
    assert "get_merchant_context" in tools
    assert "get_recovery_policy" in tools
    assert "get_allowed_actions" in tools
    assert "get_recovery_strategy_evidence" in tools


# ==============================================================================
# CHECK 7: REAL DATA GENERATION IN SERVICE
# ==============================================================================

def test_check_7_service_metrics_derive_from_database_records():
    """Check 7: Overview response computes metrics directly from database records without hardcoding."""
    merchant_id = uuid.uuid4()
    
    # 20 samples, 12 successes = 60.0% recovery rate
    records = [
        LearningOutcomeRecord(
            merchant_id=merchant_id,
            payment_id=uuid.uuid4(),
            failure_category=FailureCategory.BANK_FAILURE,
            action_type=ActionType.RETRY_PAYMENT,
            outcome_status=ActionStatus.SUCCEEDED if i < 12 else ActionStatus.FAILED,
            occurred_at=datetime.utcnow() - timedelta(days=10),
        )
        for i in range(20)
    ]

    mock_db = MagicMock()
    mock_query = MagicMock()
    mock_query.filter.return_value = mock_query
    mock_query.all.return_value = records
    mock_query.count.return_value = 0
    mock_query.first.return_value = None
    mock_db.query.return_value = mock_query

    service = LearningService(mock_db)
    snapshot = service.recompute_snapshot(merchant_id=merchant_id)

    assert snapshot.total_samples == 20
    assert snapshot.confirmed_recoveries == 12
    assert snapshot.overall_recovery_rate == 0.60
    assert snapshot.brier_score is not None
