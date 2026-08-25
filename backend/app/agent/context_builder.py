"""Agent Context Builder for Phase 3 Agent.

Constructs deliberate, typed context for agent reasoning.
Does NOT dump the entire database into the LLM prompt.
"""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.db.models.payment import Payment
from app.db.models.revenue_intelligence import RevenueIntelligenceResult
from app.db.models.recovery_case import RecoveryCase
from app.db.models.merchant import Merchant
from app.agent.schemas import AgentContext
from app.agent.tools import (
    get_payment_context,
    get_recovery_history,
    get_revenue_intelligence,
    get_merchant_context,
    get_recovery_policy,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class AgentContextBuilder:
    """Builds context for agent reasoning."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def build_context(self, opportunity_id: str) -> AgentContext:
        """Build complete context for agent reasoning."""
        # Get intelligence result to find payment
        intelligence = self.db.query(RevenueIntelligenceResult).filter(
            RevenueIntelligenceResult.id == opportunity_id
        ).first()
        
        if not intelligence:
            raise ValueError(f"Intelligence result not found: {opportunity_id}")
        
        payment = self.db.query(Payment).filter(
            Payment.id == intelligence.payment_id
        ).first()
        
        if not payment:
            raise ValueError(f"Payment not found: {intelligence.payment_id}")
        
        merchant = self.db.query(Merchant).filter(
            Merchant.id == payment.merchant_id
        ).first()
        
        # Build context using tools
        payment_ctx = get_payment_context(self.db, str(payment.id))
        recovery_history = get_recovery_history(self.db, str(payment.id))
        intelligence_ctx = get_revenue_intelligence(self.db, str(payment.id))
        merchant_ctx = get_merchant_context(self.db, str(merchant.id)) if merchant else {}
        
        # Get policy context
        policy_ctx = get_recovery_policy({"retry_count": payment_ctx.get("retry_count", 0)})
        
        # Construct AgentContext
        return AgentContext(
            payment_id=str(payment.id),
            payment_amount=payment.amount_minor,
            payment_currency=payment.currency,
            payment_status=payment.status.value,
            payment_method=payment.method,
            failure_category=intelligence.failure_category.value if intelligence.failure_category else None,
            failure_reason=intelligence.failure_reason,
            failure_code=payment.failure_code,
            retry_count=payment_ctx.get("retry_count", 0),
            created_at=payment.created_at,
            
            # Phase 2 intelligence
            revenue_at_risk=intelligence.revenue_at_risk,
            recovery_likelihood=intelligence.recovery_probability,
            opportunity_score=intelligence.opportunity_score,
            priority=intelligence.priority.value if intelligence.priority else "UNKNOWN",
            recommended_intervention=intelligence.recommended_intervention,
            contributing_factors=intelligence.factors,
            
            # Recovery history
            previous_recovery_attempts=recovery_history.get("previous_attempts", 0),
            previous_successful_recovery=recovery_history.get("previous_successful", False),
            previous_failed_recovery=recovery_history.get("previous_failed", False),
            last_action=recovery_history.get("last_action"),
            time_since_last_attempt_hours=recovery_history.get("time_since_last_attempt_hours"),
            
            # Merchant context
            merchant_id=str(merchant.id) if merchant else "",
            merchant_name=merchant.name if merchant else "Unknown",
            historical_recovery_rate=merchant_ctx.get("success_rate", 0.0),
            avg_transaction_value=int(merchant_ctx.get("avg_transaction_value", 0)),
            
            # System context
            allowed_actions=policy_ctx.get("allowed_actions", []),
            action_limits=policy_ctx.get("action_limits", {}),
            approval_requirements=policy_ctx.get("approval_requirements", {}),
            current_system_state="OPERATIONAL",
        )
    
    def build_context_from_payment(self, payment_id: str) -> AgentContext:
        """Build context directly from payment ID."""
        payment = self.db.query(Payment).filter(Payment.id == payment_id).first()
        
        if not payment:
            raise ValueError(f"Payment not found: {payment_id}")
        
        # Get intelligence result
        intelligence = self.db.query(RevenueIntelligenceResult).filter(
            RevenueIntelligenceResult.payment_id == payment_id
        ).first()
        
        merchant = self.db.query(Merchant).filter(
            Merchant.id == payment.merchant_id
        ).first()
        
        # Build context using tools
        payment_ctx = get_payment_context(self.db, str(payment.id))
        recovery_history = get_recovery_history(self.db, str(payment.id))
        intelligence_ctx = get_revenue_intelligence(self.db, str(payment.id)) if intelligence else {}
        merchant_ctx = get_merchant_context(self.db, str(merchant.id)) if merchant else {}
        
        # Get policy context
        policy_ctx = get_recovery_policy({"retry_count": payment_ctx.get("retry_count", 0)})
        
        return AgentContext(
            payment_id=str(payment.id),
            payment_amount=payment.amount_minor,
            payment_currency=payment.currency,
            payment_status=payment.status.value,
            payment_method=payment.method,
            failure_category=intelligence_ctx.get("failure_category") if intelligence_ctx else None,
            failure_reason=intelligence_ctx.get("failure_reason") if intelligence_ctx else payment.failure_description,
            failure_code=payment.failure_code,
            retry_count=payment_ctx.get("retry_count", 0),
            created_at=payment.created_at,
            
            # Phase 2 intelligence
            revenue_at_risk=intelligence_ctx.get("revenue_at_risk", payment.amount_minor) if intelligence_ctx else payment.amount_minor,
            recovery_likelihood=intelligence_ctx.get("recovery_probability", 0.5) if intelligence_ctx else 0.5,
            opportunity_score=intelligence_ctx.get("opportunity_score", 50.0) if intelligence_ctx else 50.0,
            priority=intelligence_ctx.get("priority", "MEDIUM") if intelligence_ctx else "MEDIUM",
            recommended_intervention=intelligence_ctx.get("recommended_intervention") if intelligence_ctx else None,
            contributing_factors=intelligence_ctx.get("factors", []) if intelligence_ctx else [],
            
            # Recovery history
            previous_recovery_attempts=recovery_history.get("previous_attempts", 0),
            previous_successful_recovery=recovery_history.get("previous_successful", False),
            previous_failed_recovery=recovery_history.get("previous_failed", False),
            last_action=recovery_history.get("last_action"),
            time_since_last_attempt_hours=recovery_history.get("time_since_last_attempt_hours"),
            
            # Merchant context
            merchant_id=str(merchant.id) if merchant else "",
            merchant_name=merchant.name if merchant else "Unknown",
            historical_recovery_rate=merchant_ctx.get("success_rate", 0.0),
            avg_transaction_value=int(merchant_ctx.get("avg_transaction_value", 0)),
            
            # System context
            allowed_actions=policy_ctx.get("allowed_actions", []),
            action_limits=policy_ctx.get("action_limits", {}),
            approval_requirements=policy_ctx.get("approval_requirements", {}),
            current_system_state="OPERATIONAL",
        )
