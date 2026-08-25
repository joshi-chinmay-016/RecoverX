"""Tool: Get merchant context for agent reasoning."""

from typing import Dict, Any
from sqlalchemy.orm import Session
from app.db.models.merchant import Merchant
from app.db.models.payment import Payment


def get_merchant_context(db: Session, merchant_id: str) -> Dict[str, Any]:
    """Get merchant context for agent reasoning (read-only)."""
    merchant = db.query(Merchant).filter(Merchant.id == merchant_id).first()
    
    if not merchant:
        return {"error": "Merchant not found"}
    
    # Calculate merchant statistics
    payments = db.query(Payment).filter(Payment.merchant_id == merchant_id).all()
    
    total_count = len(payments)
    failed_count = sum(1 for p in payments if p.status.value == "FAILED")
    captured_count = sum(1 for p in payments if p.status.value == "CAPTURED")
    
    total_amount = sum(p.amount_minor for p in payments)
    avg_transaction_value = total_amount / total_count if total_count > 0 else 0
    
    return {
        "merchant_id": str(merchant.id),
        "merchant_name": merchant.name,
        "external_id": merchant.external_id,
        "currency": merchant.currency,
        "total_payments": total_count,
        "failed_payments": failed_count,
        "successful_payments": captured_count,
        "success_rate": captured_count / total_count if total_count > 0 else 0.0,
        "failure_rate": failed_count / total_count if total_count > 0 else 0.0,
        "total_revenue": total_amount,
        "avg_transaction_value": avg_transaction_value,
    }
