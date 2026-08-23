"""Recovery probability calculation for revenue intelligence."""

from typing import List, Dict, Any
from app.intelligence.schemas import FeatureSet, FailureCategory, RecoveryProbability


class RecoveryProbabilityEngine:
    """Calculate recovery probability using deterministic rules."""
    
    def __init__(self):
        # Base probability by failure category
        self.category_base_probabilities = {
            FailureCategory.TEMPORARY_FAILURE: 0.75,
            FailureCategory.NETWORK_FAILURE: 0.65,
            FailureCategory.AUTHENTICATION_FAILURE: 0.60,
            FailureCategory.INSUFFICIENT_FUNDS: 0.50,
            FailureCategory.PAYMENT_METHOD_FAILURE: 0.55,
            FailureCategory.BANK_FAILURE: 0.40,
            FailureCategory.LIMIT_EXCEEDED: 0.30,
            FailureCategory.UNKNOWN: 0.25,
        }
    
    def calculate(
        self,
        features: FeatureSet,
        failure_category: FailureCategory
    ) -> RecoveryProbability:
        """Calculate recovery probability with contributing factors."""
        # Start with base probability from category
        base_probability = self.category_base_probabilities.get(
            failure_category, 0.25
        )
        
        factors = []
        probability = base_probability
        
        # Factor 1: Retry count (lower is better)
        if features.retry_count == 0:
            probability += 0.15
            factors.append({"factor": "no_previous_retries", "impact": 0.15, "direction": "positive"})
        elif features.retry_count == 1:
            probability += 0.05
            factors.append({"factor": "single_retry", "impact": 0.05, "direction": "positive"})
        elif features.retry_count >= 3:
            probability -= 0.20
            factors.append({"factor": "multiple_retries", "impact": -0.20, "direction": "negative"})
        
        # Factor 2: Time since failure (fresh failures are more recoverable)
        if features.time_since_failure_hours:
            if features.time_since_failure_hours < 24:
                probability += 0.10
                factors.append({"factor": "recent_failure", "impact": 0.10, "direction": "positive"})
            elif features.time_since_failure_hours > 168:  # 7 days
                probability -= 0.15
                factors.append({"factor": "aged_failure", "impact": -0.15, "direction": "negative"})
        
        # Factor 3: Merchant-relative transaction value (higher relative value may have more recovery effort)
        if features.normalized_value_score > 0.8:  # Top 20% relative to merchant average
            probability += 0.08
            factors.append({"factor": "high_relative_value", "impact": 0.08, "direction": "positive"})
        elif features.normalized_value_score < 0.2:  # Bottom 20% relative to merchant average
            probability -= 0.05
            factors.append({"factor": "low_relative_value", "impact": -0.05, "direction": "negative"})
        
        # Factor 4: Merchant historical recovery rate
        if features.merchant_historical_recovery_rate > 0.5:
            probability += 0.10
            factors.append({"factor": "good_merchant_recovery_rate", "impact": 0.10, "direction": "positive"})
        elif features.merchant_historical_recovery_rate < 0.2:
            probability -= 0.10
            factors.append({"factor": "poor_merchant_recovery_rate", "impact": -0.10, "direction": "negative"})
        
        # Factor 5: Previous recovery attempts
        if features.previous_successful_recovery:
            probability -= 0.30  # Already recovered, low probability of additional recovery
            factors.append({"factor": "already_recovered", "impact": -0.30, "direction": "negative"})
        elif features.previous_failed_recovery:
            probability -= 0.15
            factors.append({"factor": "previous_recovery_failed", "impact": -0.15, "direction": "negative"})
        
        # Factor 6: Payment method (some methods are more recoverable)
        if features.payment_method:
            method_lower = features.payment_method.lower()
            if "upi" in method_lower:
                probability += 0.05
                factors.append({"factor": "upi_payment_method", "impact": 0.05, "direction": "positive"})
            elif "card" in method_lower:
                probability += 0.03
                factors.append({"factor": "card_payment_method", "impact": 0.03, "direction": "positive"})
        
        # Ensure probability is bounded between 0 and 1
        probability = max(0.0, min(1.0, probability))
        
        return RecoveryProbability(
            probability=round(probability, 2),
            factors=factors,
        )
