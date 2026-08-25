"""Strategy Performance Model and Selector for Phase 5.

Evaluates historical effectiveness of candidate recovery actions for specific failure contexts,
computes explainable strategy scores (0-100), and ranks recommendations with alternatives.
"""

from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime

from app.intelligence.schemas import FailureCategory, FeatureSet
from app.agent.schemas import ActionType
from app.learning.schemas import (
    StrategyRankItem,
    StrategyScoreFactor,
    SupportLevel,
    EvidenceScope,
)
from app.learning.outcome_aggregator import OutcomeAggregator
from app.core.logging import get_logger

logger = get_logger(__name__)


class StrategyPerformanceModel:
    """Evaluates and ranks recovery strategies using empirical evidence and current payment context."""

    def __init__(self, aggregator: OutcomeAggregator):
        self.aggregator = aggregator

    def evaluate_strategies(
        self,
        failure_category: FailureCategory,
        features: Optional[FeatureSet] = None,
        merchant_id: Optional[uuid.UUID] = None,
        retry_count: int = 0,
        payment_amount_minor: int = 0,
        as_of_time: Optional[datetime] = None,
    ) -> List[StrategyRankItem]:
        """Rank all allowed recovery actions for this failure context."""
        ranked_items: List[StrategyRankItem] = []

        candidate_actions = [
            ActionType.RETRY_PAYMENT,
            ActionType.WAIT_AND_RETRY,
            ActionType.REQUEST_ALTERNATE_PAYMENT_METHOD,
            ActionType.SEND_PAYMENT_REMINDER,
            ActionType.REQUEST_REAUTHENTICATION,
            ActionType.MANUAL_REVIEW,
        ]

        for action_type in candidate_actions:
            item = self._score_action(
                action_type=action_type,
                failure_category=failure_category,
                features=features,
                merchant_id=merchant_id,
                retry_count=retry_count,
                payment_amount_minor=payment_amount_minor,
                as_of_time=as_of_time,
            )
            ranked_items.append(item)

        # Sort descending by strategy_score
        ranked_items.sort(key=lambda x: x.strategy_score, reverse=True)
        return ranked_items

    def _score_action(
        self,
        action_type: ActionType,
        failure_category: FailureCategory,
        features: Optional[FeatureSet],
        merchant_id: Optional[uuid.UUID],
        retry_count: int,
        payment_amount_minor: int,
        as_of_time: Optional[datetime],
    ) -> StrategyRankItem:
        """Compute transparent 0-100 strategy score for an individual action."""
        factors: List[StrategyScoreFactor] = []
        reasons: List[str] = []

        # 1. Historical Empirical Evidence
        outcome, scope, _ = self.aggregator.aggregate_for_context(
            failure_category=failure_category,
            action_type=action_type,
            merchant_id=merchant_id,
            as_of_time=as_of_time,
        )

        n = outcome.confirmed_attempts
        empirical_rate = outcome.empirical_recovery_rate if n > 0 else self._baseline_action_rate(action_type, failure_category)

        empirical_score = empirical_rate * 45.0
        factors.append(StrategyScoreFactor(
            name="historical_empirical_yield",
            impact=round(empirical_score, 1),
            description=f"Empirical historical recovery rate ({round(empirical_rate * 100)}%) across {n} attempts",
        ))

        # 2. Context Match Score (Max 30)
        context_score = self._compute_context_match(action_type, failure_category, retry_count, payment_amount_minor)
        factors.append(StrategyScoreFactor(
            name="failure_context_affinity",
            impact=round(context_score, 1),
            description=f"Contextual alignment with {failure_category.value}",
        ))

        # 3. Evidence Support Bonus (Max 25)
        support_bonus = 0.0
        if outcome.support_level == SupportLevel.HIGH:
            support_bonus = 25.0
        elif outcome.support_level == SupportLevel.MODERATE:
            support_bonus = 18.0
        elif outcome.support_level == SupportLevel.LOW:
            support_bonus = 10.0
        else:
            support_bonus = 5.0

        factors.append(StrategyScoreFactor(
            name="evidence_sample_support",
            impact=support_bonus,
            description=f"{outcome.support_level.value} statistical support ({n} samples)",
        ))

        # 4. Risk / Retry Count Penalties
        penalties = 0.0
        is_policy_eligible = True

        if action_type in [ActionType.RETRY_PAYMENT, ActionType.WAIT_AND_RETRY]:
            if retry_count >= 3:
                penalties += 40.0
                is_policy_eligible = False
                reasons.append("Max retry attempt limit reached (PolicyEngine constraint)")
            elif retry_count == 2:
                penalties += 15.0
                reasons.append("High retry fatigue (2 prior failed attempts)")
            elif retry_count == 1:
                penalties += 5.0

        if failure_category == FailureCategory.INSUFFICIENT_FUNDS and action_type in [ActionType.RETRY_PAYMENT]:
            penalties += 20.0
            reasons.append("Retrying insufficient funds without customer balance update has low yield")

        if failure_category == FailureCategory.LIMIT_EXCEEDED and action_type in [ActionType.RETRY_PAYMENT, ActionType.WAIT_AND_RETRY]:
            penalties += 25.0
            reasons.append("Limit exceeded requires manual review or alternate method")

        if penalties > 0:
            factors.append(StrategyScoreFactor(
                name="risk_and_policy_penalties",
                impact=-penalties,
                description="Penalties applied for retry exhaustion or context mismatch",
            ))

        total_score = max(5.0, min(100.0, empirical_score + context_score + support_bonus - penalties))
        confidence = min(0.95, max(0.30, (total_score / 100.0) * (0.9 if outcome.support_level == SupportLevel.HIGH else 0.75)))

        if not reasons:
            reasons.append(f"Strong historical effectiveness ({round(empirical_rate * 100)}%) for {failure_category.value}")

        return StrategyRankItem(
            action_type=action_type,
            strategy_score=round(total_score, 1),
            empirical_recovery_rate=empirical_rate,
            sample_size=n,
            support_level=outcome.support_level,
            evidence_scope=scope,
            is_policy_eligible=is_policy_eligible,
            confidence=round(confidence, 2),
            factors=factors,
            reasons=reasons,
        )

    def _baseline_action_rate(self, action: ActionType, category: FailureCategory) -> float:
        """Heuristic fallback rate if zero samples exist."""
        if category in [FailureCategory.TEMPORARY_FAILURE, FailureCategory.NETWORK_FAILURE]:
            return 0.70 if action in [ActionType.WAIT_AND_RETRY, ActionType.RETRY_PAYMENT] else 0.40
        if category == FailureCategory.INSUFFICIENT_FUNDS:
            return 0.60 if action in [ActionType.REQUEST_ALTERNATE_PAYMENT_METHOD, ActionType.SEND_PAYMENT_REMINDER] else 0.20
        if category == FailureCategory.AUTHENTICATION_FAILURE:
            return 0.65 if action == ActionType.REQUEST_REAUTHENTICATION else 0.25
        if category == FailureCategory.BANK_FAILURE:
            return 0.55 if action in [ActionType.WAIT_AND_RETRY, ActionType.RETRY_PAYMENT] else 0.35
        return 0.40

    def _compute_context_match(self, action: ActionType, category: FailureCategory, retry_count: int, amount_minor: int) -> float:
        """Context match scoring (max 30 points)."""
        if category == FailureCategory.TEMPORARY_FAILURE:
            return 30.0 if action in [ActionType.WAIT_AND_RETRY, ActionType.RETRY_PAYMENT] else 10.0
        if category == FailureCategory.BANK_FAILURE:
            return 28.0 if action in [ActionType.WAIT_AND_RETRY, ActionType.RETRY_PAYMENT] else 12.0
        if category == FailureCategory.INSUFFICIENT_FUNDS:
            return 30.0 if action in [ActionType.REQUEST_ALTERNATE_PAYMENT_METHOD, ActionType.SEND_PAYMENT_REMINDER] else 8.0
        if category == FailureCategory.AUTHENTICATION_FAILURE:
            return 30.0 if action == ActionType.REQUEST_REAUTHENTICATION else 10.0
        if category == FailureCategory.LIMIT_EXCEEDED:
            return 30.0 if action in [ActionType.MANUAL_REVIEW, ActionType.REQUEST_ALTERNATE_PAYMENT_METHOD] else 5.0
        return 15.0
