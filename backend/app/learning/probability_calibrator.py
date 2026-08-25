"""Probability Calibrator for Phase 5 Adaptive Recovery Intelligence.

Implements Beta-Binomial Bayesian estimation to calibrate baseline recovery probabilities
with empirical historical evidence, bounded by a strict maximum delta (|Δ| <= 0.20).
"""

from typing import Optional, Dict, Any
import uuid
from datetime import datetime

from app.intelligence.schemas import FailureCategory, FeatureSet
from app.agent.schemas import ActionType
from app.learning.schemas import (
    AdaptiveProbabilityResult,
    EvidenceScope,
    SupportLevel,
)
from app.learning.outcome_aggregator import OutcomeAggregator, AggregatedOutcome
from app.core.logging import get_logger

logger = get_logger(__name__)

# Constants
PRIOR_SAMPLE_WEIGHT = 10.0  # Equivalent weight (N0) of the baseline prior
MAX_ADAPTIVE_DELTA = 0.20   # Maximum allowed deviation from Phase 2 baseline


class AdaptiveProbabilityCalibrator:
    """Calculates bounded, calibrated recovery probability using Bayesian smoothing."""

    def __init__(self, aggregator: OutcomeAggregator):
        self.aggregator = aggregator

    def calibrate(
        self,
        baseline_probability: float,
        failure_category: FailureCategory,
        action_type: Optional[ActionType] = None,
        merchant_id: Optional[uuid.UUID] = None,
        as_of_time: Optional[datetime] = None,
    ) -> AdaptiveProbabilityResult:
        """Compute calibrated adaptive recovery probability."""
        # Query aggregated empirical evidence using hierarchical fallback
        outcome, scope, fallback_desc = self.aggregator.aggregate_for_context(
            failure_category=failure_category,
            action_type=action_type,
            merchant_id=merchant_id,
            as_of_time=as_of_time,
        )

        n = outcome.confirmed_attempts
        k = outcome.successes
        empirical_rate = outcome.empirical_recovery_rate

        # Cold-start / fallback handling
        if n == 0 or scope == EvidenceScope.BASELINE_FALLBACK:
            return AdaptiveProbabilityResult(
                adaptive_probability=baseline_probability,
                baseline_probability=baseline_probability,
                empirical_rate=0.0,
                sample_size=0,
                successes=0,
                support_level=SupportLevel.SPARSE,
                evidence_scope=EvidenceScope.BASELINE_FALLBACK,
                fallback_level="Phase 2 deterministic baseline (Cold start / sparse history)",
                model_version="adaptive-v1",
                is_cold_start=True,
                explanation="No statistically significant historical recovery attempts observed. Relying on baseline heuristics.",
            )

        # Beta-Binomial Bayesian Updating:
        # alpha_0 = baseline * N0, beta_0 = (1 - baseline) * N0
        alpha_0 = baseline_probability * PRIOR_SAMPLE_WEIGHT
        beta_0 = (1.0 - baseline_probability) * PRIOR_SAMPLE_WEIGHT

        posterior = (k + alpha_0) / (n + alpha_0 + beta_0)

        # Bounded influence: never allow probability to deviate more than MAX_ADAPTIVE_DELTA from baseline
        min_allowed = max(0.05, baseline_probability - MAX_ADAPTIVE_DELTA)
        max_allowed = min(0.95, baseline_probability + MAX_ADAPTIVE_DELTA)
        bounded_probability = max(min_allowed, min(max_allowed, posterior))
        rounded_prob = round(bounded_probability, 2)

        # Explainability text
        explanation = (
            f"Calibrated from {n} confirmed recovery attempts ({k} successes, {round(empirical_rate * 100)}% empirical yield). "
            f"Bayesian smoothed with prior baseline ({round(baseline_probability * 100)}%) to {round(rounded_prob * 100)}% "
            f"under {scope.value} scope."
        )

        return AdaptiveProbabilityResult(
            adaptive_probability=rounded_prob,
            baseline_probability=round(baseline_probability, 2),
            empirical_rate=empirical_rate,
            sample_size=n,
            successes=k,
            support_level=outcome.support_level,
            evidence_scope=scope,
            fallback_level=fallback_desc,
            model_version="adaptive-v1",
            is_cold_start=False,
            explanation=explanation,
        )
