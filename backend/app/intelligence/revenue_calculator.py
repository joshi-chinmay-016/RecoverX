"""Revenue at risk calculation for revenue intelligence."""

from typing import Optional
from app.intelligence.schemas import FeatureSet, FailureCategory, RevenueAtRisk


class RevenueAtRiskCalculator:
    """Calculate revenue at risk metrics."""
    
    def __init__(self):
        # Define recoverability by failure category
        # These are baseline estimates for Phase 2
        self.category_recoverability = {
            FailureCategory.TEMPORARY_FAILURE: 0.85,  # 85% recoverable
            FailureCategory.NETWORK_FAILURE: 0.75,     # 75% recoverable
            FailureCategory.INSUFFICIENT_FUNDS: 0.60,  # 60% recoverable
            FailureCategory.AUTHENTICATION_FAILURE: 0.70,  # 70% recoverable
            FailureCategory.BANK_FAILURE: 0.50,        # 50% recoverable
            FailureCategory.PAYMENT_METHOD_FAILURE: 0.65,  # 65% recoverable
            FailureCategory.LIMIT_EXCEEDED: 0.40,      # 40% recoverable
            FailureCategory.UNKNOWN: 0.30,             # 30% recoverable
        }
    
    def calculate(
        self,
        features: FeatureSet,
        failure_category: FailureCategory,
        recovery_probability: float
    ) -> RevenueAtRisk:
        """Calculate revenue at risk for a payment."""
        payment_amount = features.payment_amount
        
        # Gross failed revenue is the full amount
        gross_failed_revenue = payment_amount
        
        # Check if already recovered
        if features.previous_successful_recovery:
            return RevenueAtRisk(
                gross_failed_revenue=gross_failed_revenue,
                potentially_recoverable_revenue=0,
                estimated_recoverable_revenue=0,
                recovered_revenue=payment_amount,
                unrecoverable_revenue=0,
            )
        
        # Calculate potentially recoverable based on failure category
        category_recoverability = self.category_recoverability.get(
            failure_category, 0.30
        )
        potentially_recoverable_revenue = int(
            payment_amount * category_recoverability
        )
        
        # Calculate estimated recoverable based on probability
        estimated_recoverable_revenue = int(
            payment_amount * recovery_probability
        )
        
        # Unrecoverable is the difference
        unrecoverable_revenue = gross_failed_revenue - estimated_recoverable_revenue
        
        return RevenueAtRisk(
            gross_failed_revenue=gross_failed_revenue,
            potentially_recoverable_revenue=potentially_recoverable_revenue,
            estimated_recoverable_revenue=estimated_recoverable_revenue,
            recovered_revenue=0,
            unrecoverable_revenue=unrecoverable_revenue,
        )
    
    def calculate_merchant_aggregate(
        self,
        payments_data: list
    ) -> dict:
        """Calculate aggregate revenue metrics for a merchant."""
        total_revenue = 0
        failed_revenue = 0
        revenue_at_risk = 0
        estimated_recoverable_revenue = 0
        recovered_revenue = 0
        
        for payment_data in payments_data:
            amount = payment_data.get("amount_minor", 0)
            status = payment_data.get("status", "")
            estimated_recoverable = payment_data.get("estimated_recoverable_revenue", 0)
            is_recovered = payment_data.get("is_recovered", False)
            
            total_revenue += amount
            
            if status == "FAILED":
                failed_revenue += amount
                revenue_at_risk += amount
                estimated_recoverable_revenue += estimated_recoverable
            
            if is_recovered:
                recovered_revenue += amount
        
        return {
            "total_revenue": total_revenue,
            "failed_revenue": failed_revenue,
            "revenue_at_risk": revenue_at_risk,
            "estimated_recoverable_revenue": estimated_recoverable_revenue,
            "recovered_revenue": recovered_revenue,
        }
