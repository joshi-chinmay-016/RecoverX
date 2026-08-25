"""Tool: Get revenue intelligence for agent reasoning."""

from typing import Dict, Any, Union
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.db.models.revenue_intelligence import RevenueIntelligenceResult


def get_revenue_intelligence(db: Session, identifier: str) -> Dict[str, Any]:
    """Get revenue intelligence for agent reasoning by payment_id or opportunity_id (read-only)."""
    # Support lookup by payment_id or opportunity_id
    query = db.query(RevenueIntelligenceResult)
    
    # Try by id (opportunity_id) or payment_id
    intelligence = query.filter(
        or_(
            RevenueIntelligenceResult.payment_id == identifier,
            RevenueIntelligenceResult.id == identifier,
        )
    ).first()
    
    if not intelligence:
        return {"error": f"No revenue intelligence found for identifier: {identifier}"}
    
    return {
        "intelligence_id": str(intelligence.id),
        "opportunity_id": str(intelligence.id),
        "payment_id": str(intelligence.payment_id),
        "failure_category": intelligence.failure_category.value if intelligence.failure_category else None,
        "failure_reason": intelligence.failure_reason,
        "revenue_at_risk": intelligence.revenue_at_risk,
        "recovery_probability": intelligence.recovery_probability,
        "estimated_recoverable_revenue": intelligence.estimated_recoverable_revenue,
        "opportunity_score": intelligence.opportunity_score,
        "priority": intelligence.priority.value if intelligence.priority else None,
        "recommended_intervention": intelligence.recommended_intervention,
        "intervention_reason": intelligence.intervention_reason,
        "confidence": intelligence.confidence,
        "explanation": intelligence.explanation,
        "factors": intelligence.factors,
        "model_version": intelligence.model_version,
        "created_at": intelligence.created_at.isoformat() if intelligence.created_at else None,
    }
