"""Strategy Evidence Read-Only Tool for Phase 3 AI Recovery Agent (Phase 5 Extension)."""

from typing import Dict, Any, Optional
import uuid
from sqlalchemy.orm import Session

from app.db.models.payment import Payment
from app.db.models.revenue_intelligence import RevenueIntelligenceResult
from app.intelligence.schemas import FailureCategory
from app.learning.service import LearningService
from app.core.logging import get_logger

logger = get_logger(__name__)


def get_recovery_strategy_evidence(
    db: Session,
    opportunity_id: Optional[str] = None,
    payment_id: Optional[str] = None,
    failure_category: Optional[str] = None,
) -> Dict[str, Any]:
    """Retrieve empirical strategy ranking and adaptive probability evidence for the AI Agent."""
    service = LearningService(db)

    resolved_category = FailureCategory.UNKNOWN
    merchant_id = None
    retry_count = 0
    amount_minor = 0

    if opportunity_id:
        opp = db.query(RevenueIntelligenceResult).filter(RevenueIntelligenceResult.id == opportunity_id).first()
        if opp:
            resolved_category = opp.failure_category
            payment = db.query(Payment).filter(Payment.id == opp.payment_id).first()
            if payment:
                merchant_id = payment.merchant_id
                amount_minor = payment.amount_minor
                retry_count = len(payment.attempts) if payment.attempts else 0

    elif payment_id:
        payment = db.query(Payment).filter(Payment.id == payment_id).first()
        if payment:
            merchant_id = payment.merchant_id
            amount_minor = payment.amount_minor
            retry_count = len(payment.attempts) if payment.attempts else 0
            opp = db.query(RevenueIntelligenceResult).filter(RevenueIntelligenceResult.payment_id == payment.id).first()
            if opp:
                resolved_category = opp.failure_category

    if failure_category and resolved_category == FailureCategory.UNKNOWN:
        try:
            resolved_category = FailureCategory(failure_category)
        except ValueError:
            resolved_category = FailureCategory.TEMPORARY_FAILURE

    # Evaluate ranked strategies
    strategies = service.strategy_selector.evaluate_strategies(
        failure_category=resolved_category,
        merchant_id=merchant_id,
        retry_count=retry_count,
        payment_amount_minor=amount_minor,
    )

    top_strategy = strategies[0] if strategies else None
    base_prob = service._get_baseline_for_category(resolved_category)
    calib = service.calibrator.calibrate(
        baseline_probability=base_prob,
        failure_category=resolved_category,
        action_type=top_strategy.action_type if top_strategy else None,
        merchant_id=merchant_id,
    )

    alternatives = []
    if len(strategies) > 1:
        for alt in strategies[1:4]:
            alternatives.append({
                "action_type": alt.action_type.value,
                "strategy_score": alt.strategy_score,
                "empirical_rate": alt.empirical_recovery_rate,
                "sample_size": alt.sample_size,
                "is_policy_eligible": alt.is_policy_eligible,
            })

    return {
        "failure_category": resolved_category.value,
        "recommended_action": top_strategy.action_type.value if top_strategy else "RETRY_PAYMENT",
        "strategy_score": top_strategy.strategy_score if top_strategy else 70.0,
        "empirical_recovery_rate": top_strategy.empirical_recovery_rate if top_strategy else 0.50,
        "sample_size": top_strategy.sample_size if top_strategy else 0,
        "support_level": top_strategy.support_level.value if top_strategy else "SPARSE",
        "evidence_scope": top_strategy.evidence_scope.value if top_strategy else "BASELINE_FALLBACK",
        "adaptive_probability": calib.adaptive_probability,
        "baseline_probability": calib.baseline_probability,
        "is_cold_start": calib.is_cold_start,
        "reasons": top_strategy.reasons if top_strategy else ["Standard baseline recovery rule"],
        "alternatives": alternatives,
    }
