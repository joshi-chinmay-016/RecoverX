"""Tool: Get recovery history for agent reasoning."""

from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.db.models.recovery_case import RecoveryCase
from app.db.models.payment import Payment
from datetime import datetime, timedelta


def get_recovery_history(db: Session, payment_id: str) -> Dict[str, Any]:
    """Get recovery history for agent reasoning (read-only)."""
    recovery_case = db.query(RecoveryCase).filter(
        RecoveryCase.payment_id == payment_id
    ).first()
    
    if not recovery_case:
        return {
            "has_recovery_case": False,
            "previous_attempts": 0,
            "previous_successful": False,
            "previous_failed": False,
        }
    
    # Get payment to check for previous successful attempts
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    
    # Calculate time since last attempt
    last_attempt_time = None
    time_since_last_attempt_hours = None
    
    if payment and payment.created_at:
        last_attempt_time = payment.created_at
        time_since_last_attempt_hours = (
            (datetime.utcnow() - payment.created_at).total_seconds() / 3600
        )
    
    return {
        "has_recovery_case": True,
        "recovery_case_id": str(recovery_case.id),
        "status": recovery_case.status.value,
        "amount_at_risk_minor": recovery_case.amount_at_risk_minor,
        "created_at": recovery_case.created_at.isoformat() if recovery_case.created_at else None,
        "updated_at": recovery_case.updated_at.isoformat() if recovery_case.updated_at else None,
        "previous_attempts": 1 if recovery_case.status.value != "OPEN" else 0,
        "previous_successful": recovery_case.status.value == "RESOLVED",
        "previous_failed": recovery_case.status.value == "CLOSED",
        "last_action": recovery_case.status.value,
        "time_since_last_attempt_hours": time_since_last_attempt_hours,
    }
