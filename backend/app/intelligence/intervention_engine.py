"""Intervention recommendation engine for revenue intelligence."""

from app.intelligence.schemas import FeatureSet, FailureCategory, PriorityLevel, InterventionRecommendation


class InterventionRecommendationEngine:
    """Recommend appropriate interventions for failed payments."""
    
    # Intervention rules by failure category
    CATEGORY_INTERVENTIONS = {
        FailureCategory.TEMPORARY_FAILURE: {
            "action": "RETRY_PAYMENT",
            "reason": "Temporary failure - retry the payment",
            "base_confidence": 0.85,
        },
        FailureCategory.NETWORK_FAILURE: {
            "action": "RETRY_LATER",
            "reason": "Network issue - retry after a short delay",
            "base_confidence": 0.75,
        },
        FailureCategory.INSUFFICIENT_FUNDS: {
            "action": "REQUEST_ALTERNATE_PAYMENT_METHOD",
            "reason": "Insufficient funds - request alternate payment method",
            "base_confidence": 0.70,
        },
        FailureCategory.AUTHENTICATION_FAILURE: {
            "action": "REQUEST_REAUTHENTICATION",
            "reason": "Authentication failed - request customer to re-authenticate",
            "base_confidence": 0.75,
        },
        FailureCategory.BANK_FAILURE: {
            "action": "RETRY_WITH_ALTERNATE_METHOD",
            "reason": "Bank processing error - retry with alternate payment method",
            "base_confidence": 0.60,
        },
        FailureCategory.PAYMENT_METHOD_FAILURE: {
            "action": "RETRY_PAYMENT",
            "reason": "Payment method error - retry the payment",
            "base_confidence": 0.65,
        },
        FailureCategory.LIMIT_EXCEEDED: {
            "action": "REQUEST_MANUAL_REVIEW",
            "reason": "Transaction limit exceeded - requires manual review",
            "base_confidence": 0.50,
        },
        FailureCategory.UNKNOWN: {
            "action": "MANUAL_REVIEW",
            "reason": "Unknown failure - requires manual investigation",
            "base_confidence": 0.30,
        },
    }
    
    def recommend(
        self,
        features: FeatureSet,
        failure_category: FailureCategory,
        priority: PriorityLevel,
        recovery_probability: float
    ) -> InterventionRecommendation:
        """Recommend intervention based on failure analysis."""
        # Get base intervention for category
        base_intervention = self.CATEGORY_INTERVENTIONS.get(
            failure_category,
            self.CATEGORY_INTERVENTIONS[FailureCategory.UNKNOWN]
        )
        
        recommended_action = base_intervention["action"]
        reason = base_intervention["reason"]
        confidence = base_intervention["base_confidence"]
        
        # Adjust recommendation based on priority
        if priority == PriorityLevel.CRITICAL and features.payment_amount > 50000:
            # High-value critical cases get manual review
            recommended_action = "PRIORITIZE_MANUAL_REVIEW"
            reason = f"High-value payment (₹{features.payment_amount / 100:.2f}) with {failure_category.value} - prioritize manual review"
            confidence = 0.80
        
        # Adjust based on retry count
        if features.retry_count >= 3:
            # After multiple retries, recommend alternate method or manual review
            if failure_category in [FailureCategory.INSUFFICIENT_FUNDS, FailureCategory.BANK_FAILURE]:
                recommended_action = "REQUEST_ALTERNATE_PAYMENT_METHOD"
                reason = f"Multiple retries failed - request alternate payment method"
                confidence = 0.75
            else:
                recommended_action = "MANUAL_REVIEW"
                reason = f"Multiple retries ({features.retry_count}) failed - requires manual investigation"
                confidence = 0.70
        
        # Adjust based on recovery probability
        if recovery_probability < 0.3:
            recommended_action = "MANUAL_REVIEW"
            reason = f"Low recovery probability ({recovery_probability:.0%}) - requires manual assessment"
            confidence = 0.60
        
        # Adjust based on time since failure
        if features.time_since_failure_hours and features.time_since_failure_hours > 168:  # 7 days
            if recommended_action in ["RETRY_PAYMENT", "RETRY_LATER"]:
                recommended_action = "MANUAL_REVIEW"
                reason = "Aged failure (over 7 days) - manual review recommended before retry"
                confidence = 0.65
        
        return InterventionRecommendation(
            recommended_action=recommended_action,
            reason=reason,
            confidence=round(confidence, 2),
        )
