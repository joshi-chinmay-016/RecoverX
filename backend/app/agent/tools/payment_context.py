"""Tool: Get payment context for agent reasoning."""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.db.models.payment import Payment
from app.db.models.payment_attempt import PaymentAttempt
from datetime import datetime


def get_payment_context(db: Session, payment_id: str) -> Dict[str, Any]:
    """Get payment context for agent reasoning (read-only)."""
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    
    if not payment:
        return {"error": "Payment not found"}
    
    # Get payment attempts
    attempts = db.query(PaymentAttempt).filter(
        PaymentAttempt.payment_id == payment_id
    ).order_by(PaymentAttempt.attempt_number).all()
    
    return {
        "payment_id": str(payment.id),
        "razorpay_payment_id": payment.razorpay_payment_id,
        "amount_minor": payment.amount_minor,
        "currency": payment.currency,
        "status": payment.status.value,
        "method": payment.method,
        "failure_code": payment.failure_code,
        "failure_description": payment.failure_description,
        "created_at": payment.created_at.isoformat() if payment.created_at else None,
        "retry_count": len(attempts),
        "attempts": [
            {
                "attempt_number": a.attempt_number,
                "status": a.status.value,
                "failure_code": a.failure_code,
                "failure_description": a.failure_description,
                "method": a.method,
                "started_at": a.started_at.isoformat() if a.started_at else None,
                "completed_at": a.completed_at.isoformat() if a.completed_at else None,
            }
            for a in attempts
        ],
    }
