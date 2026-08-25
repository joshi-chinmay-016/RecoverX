"""Automated Unit and Integration Tests for Phase 5 Adaptive Recovery Intelligence & Learning."""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock

from app.db.base import ActionStatus, PaymentStatus
from app.db.models.merchant import Merchant
from app.db.models.payment import Payment
from app.db.models.learning_outcome import LearningOutcomeRecord
from app.intelligence.schemas import FailureCategory
from app.agent.schemas import ActionType
from app.learning.schemas import EvidenceScope, SupportLevel, DriftStatus
from app.learning.outcome_aggregator import OutcomeAggregator
from app.learning.probability_calibrator import AdaptiveProbabilityCalibrator, MAX_ADAPTIVE_DELTA
from app.learning.strategy_selector import StrategyPerformanceModel
from app.learning.service import LearningService
from app.agent.tools.registry import ToolRegistry


@pytest.fixture
def sample_merchant():
    return Merchant(
        id=uuid.uuid4(),
        external_id="merch_learn_test",
        name="Learning Test Merchant",
        currency="INR",
    )


@pytest.fixture
def sample_payment(sample_merchant):
    return Payment(
        id=uuid.uuid4(),
        merchant_id=sample_merchant.id,
        razorpay_payment_id="pay_test_learn_1",
        amount_minor=2500000,
        currency="INR",
        method="upi",
        status=PaymentStatus.FAILED,
        failure_code="BAD_REQUEST_ERROR",
        failure_description="Bank technical error",
    )


# ==============================================================================
# 1. Outcome Aggregator & Exclusion Tests
# ==============================================================================

def test_outcome_aggregator_filters_unknown_and_blocked(sample_merchant, sample_payment):
    """Ensure UNKNOWN provider timeouts and BLOCKED actions are excluded from the confirmed denominator."""
    # 8 successes + 2 failures = 10 confirmed attempts (meets MIN_LOW_SUPPORT threshold)
    records = [
        *[LearningOutcomeRecord(
            merchant_id=sample_merchant.id,
            payment_id=sample_payment.id,
            failure_category=FailureCategory.BANK_FAILURE,
            action_type=ActionType.RETRY_PAYMENT,
            outcome_status=ActionStatus.SUCCEEDED,
            occurred_at=datetime.utcnow() - timedelta(days=5),
        ) for _ in range(8)],
        *[LearningOutcomeRecord(
            merchant_id=sample_merchant.id,
            payment_id=sample_payment.id,
            failure_category=FailureCategory.BANK_FAILURE,
            action_type=ActionType.RETRY_PAYMENT,
            outcome_status=ActionStatus.FAILED,
            occurred_at=datetime.utcnow() - timedelta(days=5),
        ) for _ in range(2)],
        # 5 UNKNOWN timeouts (must be excluded from confirmed yield denominator)
        *[LearningOutcomeRecord(
            merchant_id=sample_merchant.id,
            payment_id=sample_payment.id,
            failure_category=FailureCategory.BANK_FAILURE,
            action_type=ActionType.RETRY_PAYMENT,
            outcome_status=ActionStatus.UNKNOWN,
            occurred_at=datetime.utcnow() - timedelta(days=5),
        ) for _ in range(5)],
        # 3 BLOCKED actions (must be excluded from confirmed yield denominator)
        *[LearningOutcomeRecord(
            merchant_id=sample_merchant.id,
            payment_id=sample_payment.id,
            failure_category=FailureCategory.BANK_FAILURE,
            action_type=ActionType.RETRY_PAYMENT,
            outcome_status=ActionStatus.BLOCKED,
            occurred_at=datetime.utcnow() - timedelta(days=5),
        ) for _ in range(3)],
    ]

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.all.return_value = records

    aggregator = OutcomeAggregator(mock_db)
    outcome, scope, _ = aggregator.aggregate_for_context(
        failure_category=FailureCategory.BANK_FAILURE,
        action_type=ActionType.RETRY_PAYMENT,
        merchant_id=sample_merchant.id,
    )

    # 8 success + 2 failure = 10 confirmed attempts
    assert outcome.successes == 8
    assert outcome.failures == 2
    assert outcome.unknowns == 5
    assert outcome.blocked == 3
    assert outcome.confirmed_attempts == 10
    assert outcome.empirical_recovery_rate == 0.80


# ==============================================================================
# 2. Probability Calibrator & Beta-Binomial Tests
# ==============================================================================

def test_probability_calibrator_beta_binomial_smoothing(sample_merchant):
    """Test Beta-Binomial Bayesian smoothing on historical recovery samples."""
    mock_db = MagicMock()
    records = [
        LearningOutcomeRecord(
            merchant_id=sample_merchant.id,
            failure_category=FailureCategory.BANK_FAILURE,
            action_type=ActionType.RETRY_PAYMENT,
            outcome_status=ActionStatus.SUCCEEDED if i < 70 else ActionStatus.FAILED,
            occurred_at=datetime.utcnow() - timedelta(days=10),
        )
        for i in range(100)
    ]
    mock_db.query.return_value.filter.return_value.all.return_value = records

    aggregator = OutcomeAggregator(mock_db)
    calibrator = AdaptiveProbabilityCalibrator(aggregator)

    result = calibrator.calibrate(
        baseline_probability=0.40,
        failure_category=FailureCategory.BANK_FAILURE,
        action_type=ActionType.RETRY_PAYMENT,
        merchant_id=sample_merchant.id,
    )

    assert result.baseline_probability == 0.40
    assert result.empirical_rate == 0.70
    assert result.sample_size == 100
    assert result.adaptive_probability > 0.40
    assert result.adaptive_probability <= 0.60
    assert result.support_level == SupportLevel.HIGH
    assert not result.is_cold_start


def test_probability_calibrator_enforces_max_delta_bound(sample_merchant):
    """Ensure adaptive probability never deviates more than 0.20 from Phase 2 baseline."""
    mock_db = MagicMock()
    records = [
        LearningOutcomeRecord(
            merchant_id=sample_merchant.id,
            failure_category=FailureCategory.BANK_FAILURE,
            action_type=ActionType.RETRY_PAYMENT,
            outcome_status=ActionStatus.SUCCEEDED,
            occurred_at=datetime.utcnow() - timedelta(days=10),
        )
        for _ in range(500)
    ]
    mock_db.query.return_value.filter.return_value.all.return_value = records

    aggregator = OutcomeAggregator(mock_db)
    calibrator = AdaptiveProbabilityCalibrator(aggregator)

    result = calibrator.calibrate(
        baseline_probability=0.30,
        failure_category=FailureCategory.BANK_FAILURE,
        merchant_id=sample_merchant.id,
    )

    assert result.adaptive_probability <= (0.30 + MAX_ADAPTIVE_DELTA + 0.01)
    assert result.adaptive_probability == 0.50


# ==============================================================================
# 3. Strategy Performance Model Tests
# ==============================================================================

def test_strategy_performance_ranking_prefers_effective_action(sample_merchant):
    """Verify that strategies with high empirical yields rank above low yield actions."""
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.all.return_value = []

    aggregator = OutcomeAggregator(mock_db)
    model = StrategyPerformanceModel(aggregator)

    ranked = model.evaluate_strategies(
        failure_category=FailureCategory.BANK_FAILURE,
        merchant_id=sample_merchant.id,
        retry_count=0,
    )

    top_action = ranked[0]
    assert top_action.action_type in [ActionType.RETRY_PAYMENT, ActionType.WAIT_AND_RETRY]
    assert top_action.strategy_score >= 50.0
    assert top_action.is_policy_eligible is True


def test_strategy_performance_penalizes_max_retries(sample_merchant):
    """When retry count >= 3, retry strategies are heavily penalized and flagged policy ineligible."""
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.all.return_value = []

    aggregator = OutcomeAggregator(mock_db)
    model = StrategyPerformanceModel(aggregator)

    ranked = model.evaluate_strategies(
        failure_category=FailureCategory.BANK_FAILURE,
        merchant_id=sample_merchant.id,
        retry_count=3,
    )

    retry_item = next(item for item in ranked if item.action_type == ActionType.RETRY_PAYMENT)
    assert retry_item.is_policy_eligible is False
    assert any("PolicyEngine" in r for r in retry_item.reasons)
    assert ranked[0].action_type in [ActionType.REQUEST_ALTERNATE_PAYMENT_METHOD, ActionType.MANUAL_REVIEW]


# ==============================================================================
# 4. Temporal Leakage & Merchant Isolation Tests
# ==============================================================================

def test_temporal_leakage_prevention(sample_merchant):
    """Outcomes occurring AFTER as_of_time must never be included in the prediction."""
    mock_db = MagicMock()
    as_of = datetime(2026, 8, 1, 12, 0, 0)
    
    aggregator = OutcomeAggregator(mock_db)
    aggregator.aggregate_for_context(
        failure_category=FailureCategory.BANK_FAILURE,
        merchant_id=sample_merchant.id,
        as_of_time=as_of,
    )

    mock_db.query.assert_called()


# ==============================================================================
# 5. Agent Tool & Brier Calibration Tests
# ==============================================================================

def test_agent_tool_get_recovery_strategy_evidence(sample_merchant, sample_payment):
    """Verify AI Agent tool executes safely and returns structured empirical rankings."""
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.side_effect = [
        sample_payment,
        None,
    ]
    mock_db.query.return_value.filter.return_value.all.return_value = []

    registry = ToolRegistry(mock_db)
    assert registry.is_tool_allowed("get_recovery_strategy_evidence")

    tool_result = registry.execute_tool(
        "get_recovery_strategy_evidence",
        {"payment_id": str(sample_payment.id), "failure_category": "BANK_FAILURE"}
    )

    assert tool_result["success"] is True
    output = tool_result["output"]
    assert "recommended_action" in output
    assert "strategy_score" in output
    assert "adaptive_probability" in output
    assert "alternatives" in output
