"""Feature extraction for revenue intelligence."""

from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from app.db.models.payment import Payment
from app.db.models.payment_attempt import PaymentAttempt
from app.db.models.recovery_case import RecoveryCase
from app.db.models.merchant import Merchant
from app.intelligence.schemas import FeatureSet


class FeatureExtractor:
    """Extract features from payment/recovery data for intelligence analysis."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def extract_features(self, payment: Payment) -> FeatureSet:
        """Extract features from a payment."""
        # Get payment attempts
        attempts = self.db.query(PaymentAttempt).filter(
            PaymentAttempt.payment_id == payment.id
        ).order_by(PaymentAttempt.attempt_number).all()
        
        # Get recovery case
        recovery_case = self.db.query(RecoveryCase).filter(
            RecoveryCase.payment_id == payment.id
        ).first()
        
        # Get merchant
        merchant = self.db.query(Merchant).filter(
            Merchant.id == payment.merchant_id
        ).first()
        
        # Calculate time since failure
        last_attempt = attempts[-1] if attempts else None
        time_since_failure = None
        if last_attempt and last_attempt.completed_at:
            time_since_failure = (datetime.utcnow() - last_attempt.completed_at).total_seconds() / 3600
        
        # Calculate recovery case age
        recovery_case_age = None
        if recovery_case:
            recovery_case_age = (datetime.utcnow() - recovery_case.created_at).total_seconds() / 3600
        
        # Get merchant-level statistics
        merchant_stats = self._get_merchant_statistics(merchant.id if merchant else None)
        
        # Calculate merchant-relative transaction value features
        transaction_value_percentile = self._calculate_transaction_value_percentile(
            payment.amount_minor, merchant.id if merchant else None
        )
        normalized_value_score = self._calculate_normalized_value_score(
            payment.amount_minor, merchant_stats["avg_transaction_value"]
        )
        
        # Check previous recovery attempts
        previous_recovery_attempts = 0
        previous_successful_recovery = False
        previous_failed_recovery = False
        if recovery_case:
            # For Phase 2, we'll use simple heuristics
            # In Phase 3, this could be enhanced with actual recovery history
            previous_recovery_attempts = 1 if recovery_case.status.value != "OPEN" else 0
            previous_successful_recovery = recovery_case.status.value == "RESOLVED"
            previous_failed_recovery = recovery_case.status.value == "CLOSED"
        
        return FeatureSet(
            payment_amount=payment.amount_minor,
            currency=payment.currency,
            payment_method=payment.method,
            payment_status=payment.status.value,
            failure_code=payment.failure_code,
            failure_message=payment.failure_description,
            retry_count=len(attempts),
            created_at=payment.created_at or datetime.utcnow(),
            last_attempt_at=last_attempt.completed_at if last_attempt else None,
            time_since_failure_hours=time_since_failure,
            merchant_historical_success_rate=merchant_stats["success_rate"],
            merchant_historical_failure_rate=merchant_stats["failure_rate"],
            merchant_historical_recovery_rate=merchant_stats["recovery_rate"],
            merchant_avg_transaction_value=merchant_stats["avg_transaction_value"],
            transaction_value_percentile=transaction_value_percentile,
            normalized_value_score=normalized_value_score,
            previous_recovery_attempts=previous_recovery_attempts,
            previous_successful_recovery=previous_successful_recovery,
            previous_failed_recovery=previous_failed_recovery,
            recovery_case_age_hours=recovery_case_age,
        )
    
    def _get_merchant_statistics(self, merchant_id: Optional[str]) -> dict:
        """Calculate merchant-level statistics."""
        if not merchant_id:
            return {
                "success_rate": 0.0,
                "failure_rate": 0.0,
                "recovery_rate": 0.0,
                "avg_transaction_value": 0,
            }
        
        # Get all payments for merchant
        payments = self.db.query(Payment).filter(
            Payment.merchant_id == merchant_id
        ).all()
        
        if not payments:
            return {
                "success_rate": 0.0,
                "failure_rate": 0.0,
                "recovery_rate": 0.0,
                "avg_transaction_value": 0,
            }
        
        total_count = len(payments)
        failed_count = sum(1 for p in payments if p.status.value == "FAILED")
        captured_count = sum(1 for p in payments if p.status.value == "CAPTURED")
        
        # Calculate recovery rate (resolved recovery cases / total recovery cases)
        recovery_cases = self.db.query(RecoveryCase).join(Payment).filter(
            Payment.merchant_id == merchant_id
        ).all()
        
        recovery_rate = 0.0
        if recovery_cases:
            resolved_count = sum(1 for rc in recovery_cases if rc.status.value == "RESOLVED")
            recovery_rate = resolved_count / len(recovery_cases)
        
        captured_payments = [p for p in payments if p.status.value == "CAPTURED"]
        avg_transaction_value = (
            sum(p.amount_minor for p in captured_payments) / len(captured_payments)
            if captured_payments
            else 0
        )
        
        return {
            "success_rate": captured_count / total_count if total_count > 0 else 0.0,
            "failure_rate": failed_count / total_count if total_count > 0 else 0.0,
            "recovery_rate": recovery_rate,
            "avg_transaction_value": int(avg_transaction_value),
        }
    
    def _calculate_transaction_value_percentile(self, payment_amount: int, merchant_id: Optional[str]) -> float:
        """Calculate transaction value percentile (0.0 to 1.0) within merchant's transaction distribution.
        
        Uses deterministic fallback for small datasets to ensure consistent behavior.
        No external ML dependencies are used.
        """
        if not merchant_id:
            return 0.5  # Neutral fallback for unknown merchant
        
        # Get all payment amounts for merchant
        payments = self.db.query(Payment).filter(
            Payment.merchant_id == merchant_id
        ).all()
        
        if not payments or len(payments) <= 1:
            return 0.5  # Neutral fallback for merchant with no prior history
        
        amounts = [p.amount_minor for p in payments]
        amounts.sort()
        
        # Calculate percentile using deterministic method
        rank = sum(1 for a in amounts if a <= payment_amount)
        percentile = rank / len(amounts) if len(amounts) > 0 else 0.5
        
        return max(0.0, min(1.0, percentile))
    
    def _calculate_normalized_value_score(self, payment_amount: int, merchant_avg: int) -> float:
        """Calculate normalized value score (0.0 to 1.0) relative to merchant average.
        
        Uses bounded logistic scaling to prevent extreme values from dominating.
        Ensures no single raw amount can automatically drive score to 100.
        """
        if merchant_avg == 0:
            return 0.5  # Neutral fallback
        
        import math
        ratio = payment_amount / merchant_avg
        
        # Logistic sigmoid centered at ratio = 1.0
        normalized = 1.0 / (1.0 + math.exp(-1.5 * (ratio - 1.0)))
        
        return max(0.0, min(1.0, normalized))
