"""Outcome Aggregator for Phase 5 Adaptive Recovery Intelligence.

Aggregates historical recovery attempts, distinguishing confirmed outcomes (SUCCEEDED, FAILED)
from UNKNOWN timeouts and BLOCKED actions. Enforces merchant isolation and temporal cutoffs.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.db.base import ActionStatus
from app.db.models.learning_outcome import LearningOutcomeRecord
from app.db.models.execution_attempt import ExecutionAttempt
from app.db.models.recovery_action import RecoveryAction
from app.intelligence.schemas import FailureCategory
from app.agent.schemas import ActionType
from app.learning.schemas import SupportLevel, EvidenceScope
from app.core.logging import get_logger

logger = get_logger(__name__)

# Minimum sample sizes for statistical reliability
MIN_HIGH_SUPPORT = 50
MIN_MODERATE_SUPPORT = 20
MIN_LOW_SUPPORT = 10


class AggregatedOutcome:
    """Statistical summary of aggregated recovery attempts."""
    def __init__(
        self,
        total_attempts: int = 0,
        successes: int = 0,
        failures: int = 0,
        unknowns: int = 0,
        blocked: int = 0,
        scope: EvidenceScope = EvidenceScope.BASELINE_FALLBACK,
    ):
        self.total_attempts = total_attempts
        self.successes = successes
        self.failures = failures
        self.unknowns = unknowns
        self.blocked = blocked
        self.scope = scope

    @property
    def confirmed_attempts(self) -> int:
        """Confirmed denominator excluding UNKNOWN timeouts and BLOCKED actions."""
        return self.successes + self.failures

    @property
    def empirical_recovery_rate(self) -> float:
        """Observed empirical success rate among confirmed outcomes."""
        if self.confirmed_attempts == 0:
            return 0.0
        return round(self.successes / self.confirmed_attempts, 4)

    @property
    def support_level(self) -> SupportLevel:
        """Classify sample size support."""
        if self.confirmed_attempts >= MIN_HIGH_SUPPORT:
            return SupportLevel.HIGH
        elif self.confirmed_attempts >= MIN_MODERATE_SUPPORT:
            return SupportLevel.MODERATE
        elif self.confirmed_attempts >= MIN_LOW_SUPPORT:
            return SupportLevel.LOW
        return SupportLevel.SPARSE


class OutcomeAggregator:
    """Deterministic aggregator of recovery outcome evidence."""

    def __init__(self, db: Session):
        self.db = db

    def aggregate_for_context(
        self,
        failure_category: FailureCategory,
        action_type: Optional[ActionType] = None,
        merchant_id: Optional[uuid.UUID] = None,
        as_of_time: Optional[datetime] = None,
        lookback_days: int = 90,
    ) -> Tuple[AggregatedOutcome, EvidenceScope, str]:
        """Hierarchical aggregation query returning the best statistical evidence.
        
        Fallback hierarchy:
        1. Merchant + Category + Action
        2. Merchant + Category
        3. Global Category + Action
        4. Global Category
        5. Baseline Fallback
        """
        cutoff_date = (as_of_time or datetime.utcnow()) - timedelta(days=lookback_days)
        time_filter = as_of_time or datetime.utcnow()

        # 1. Tier 1: Merchant + Category + Action
        if merchant_id and action_type:
            tier1 = self._query_aggregate(
                merchant_id=merchant_id,
                category=failure_category,
                action_type=action_type,
                start_time=cutoff_date,
                end_time=time_filter,
                scope=EvidenceScope.MERCHANT_CATEGORY_ACTION,
            )
            if tier1.confirmed_attempts >= MIN_LOW_SUPPORT:
                return tier1, EvidenceScope.MERCHANT_CATEGORY_ACTION, "Merchant-specific action history"

        # 2. Tier 2: Merchant + Category
        if merchant_id:
            tier2 = self._query_aggregate(
                merchant_id=merchant_id,
                category=failure_category,
                action_type=None,
                start_time=cutoff_date,
                end_time=time_filter,
                scope=EvidenceScope.MERCHANT_CATEGORY,
            )
            if tier2.confirmed_attempts >= MIN_LOW_SUPPORT:
                return tier2, EvidenceScope.MERCHANT_CATEGORY, "Merchant-specific category history"

        # 3. Tier 3: Global Category + Action
        if action_type:
            tier3 = self._query_aggregate(
                merchant_id=None,
                category=failure_category,
                action_type=action_type,
                start_time=cutoff_date,
                end_time=time_filter,
                scope=EvidenceScope.GLOBAL_CATEGORY_ACTION,
            )
            if tier3.confirmed_attempts >= MIN_LOW_SUPPORT:
                return tier3, EvidenceScope.GLOBAL_CATEGORY_ACTION, "Global category action history (Merchant history sparse)"

        # 4. Tier 4: Global Category
        tier4 = self._query_aggregate(
            merchant_id=None,
            category=failure_category,
            action_type=None,
            start_time=cutoff_date,
            end_time=time_filter,
            scope=EvidenceScope.GLOBAL_CATEGORY,
        )
        if tier4.confirmed_attempts >= MIN_LOW_SUPPORT:
            return tier4, EvidenceScope.GLOBAL_CATEGORY, "Global category aggregate history"

        # 5. Tier 5: Baseline Fallback
        fallback = AggregatedOutcome(scope=EvidenceScope.BASELINE_FALLBACK)
        return fallback, EvidenceScope.BASELINE_FALLBACK, "Insufficient sample size (Using deterministic Phase 2 baseline)"

    def _query_aggregate(
        self,
        merchant_id: Optional[uuid.UUID],
        category: FailureCategory,
        action_type: Optional[ActionType],
        start_time: datetime,
        end_time: datetime,
        scope: EvidenceScope,
    ) -> AggregatedOutcome:
        """Execute granular outcome aggregation query."""
        filters = [
            LearningOutcomeRecord.failure_category == category,
            LearningOutcomeRecord.occurred_at >= start_time,
            LearningOutcomeRecord.occurred_at <= end_time,
        ]

        if merchant_id:
            filters.append(LearningOutcomeRecord.merchant_id == merchant_id)
        if action_type:
            filters.append(LearningOutcomeRecord.action_type == action_type)

        records = self.db.query(LearningOutcomeRecord).filter(and_(*filters)).all()

        successes = sum(1 for r in records if r.outcome_status in [ActionStatus.SUCCEEDED])
        failures = sum(1 for r in records if r.outcome_status in [ActionStatus.FAILED, ActionStatus.RETRYABLE])
        unknowns = sum(1 for r in records if r.outcome_status == ActionStatus.UNKNOWN)
        blocked = sum(1 for r in records if r.outcome_status == ActionStatus.BLOCKED)

        return AggregatedOutcome(
            total_attempts=len(records),
            successes=successes,
            failures=failures,
            unknowns=unknowns,
            blocked=blocked,
            scope=scope,
        )

    def get_all_category_metrics(
        self,
        merchant_id: Optional[uuid.UUID] = None,
        lookback_days: int = 90
    ) -> Dict[FailureCategory, AggregatedOutcome]:
        """Aggregate outcomes across all standardized failure categories."""
        start_time = datetime.utcnow() - timedelta(days=lookback_days)
        result: Dict[FailureCategory, AggregatedOutcome] = {}

        for cat in FailureCategory:
            agg, _, _ = self.aggregate_for_context(
                failure_category=cat,
                merchant_id=merchant_id,
                lookback_days=lookback_days,
            )
            result[cat] = agg

        return result

    def get_strategy_performance_metrics(
        self,
        merchant_id: Optional[uuid.UUID] = None,
        lookback_days: int = 90
    ) -> Dict[ActionType, AggregatedOutcome]:
        """Aggregate outcomes across all allowed recovery actions."""
        start_time = datetime.utcnow() - timedelta(days=lookback_days)
        filters = [LearningOutcomeRecord.occurred_at >= start_time]
        if merchant_id:
            filters.append(LearningOutcomeRecord.merchant_id == merchant_id)

        records = self.db.query(LearningOutcomeRecord).filter(and_(*filters)).all()
        result: Dict[ActionType, AggregatedOutcome] = {}

        for action_type in ActionType:
            action_records = [r for r in records if r.action_type == action_type]
            successes = sum(1 for r in action_records if r.outcome_status == ActionStatus.SUCCEEDED)
            failures = sum(1 for r in action_records if r.outcome_status in [ActionStatus.FAILED, ActionStatus.RETRYABLE])
            unknowns = sum(1 for r in action_records if r.outcome_status == ActionStatus.UNKNOWN)
            blocked = sum(1 for r in action_records if r.outcome_status == ActionStatus.BLOCKED)

            result[action_type] = AggregatedOutcome(
                total_attempts=len(action_records),
                successes=successes,
                failures=failures,
                unknowns=unknowns,
                blocked=blocked,
                scope=EvidenceScope.MERCHANT_CATEGORY_ACTION if merchant_id else EvidenceScope.GLOBAL_CATEGORY_ACTION,
            )

        return result
