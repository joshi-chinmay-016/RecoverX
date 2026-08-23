"""Opportunity scoring for revenue intelligence."""

from app.intelligence.schemas import FeatureSet, RecoveryProbability, PriorityLevel, OpportunityScore


class OpportunityScorer:
    """Score recovery opportunities for prioritization."""
    
    def __init__(self):
        # Priority thresholds
        self.priority_thresholds = {
            PriorityLevel.CRITICAL: 80,
            PriorityLevel.HIGH: 60,
            PriorityLevel.MEDIUM: 40,
            PriorityLevel.LOW: 0,
        }
    
    def score(
        self,
        features: FeatureSet,
        recovery_probability: RecoveryProbability,
        revenue_at_risk: int
    ) -> OpportunityScore:
        """Calculate opportunity score and priority using merchant-relative values."""
        score_factors = []
        
        # Use merchant-relative normalized value score instead of absolute amount
        # This prevents large transactions from automatically dominating the score
        value_component = features.normalized_value_score * 40  # 0-40 points
        score_factors.append({
            "name": "transaction_value",
            "impact": round(value_component, 2),
            "explanation": self._get_value_explanation(features)
        })
        
        # Recovery likelihood component (0-40 points)
        likelihood_component = recovery_probability.probability * 40
        score_factors.append({
            "name": "recovery_likelihood",
            "impact": round(likelihood_component, 2),
            "explanation": f"Estimated recovery likelihood is {recovery_probability.probability * 100:.0f}% based on failure category and context"
        })
        
        # Transaction value percentile bonus (0-10 points)
        percentile_bonus = features.transaction_value_percentile * 10
        score_factors.append({
            "name": "value_percentile",
            "impact": round(percentile_bonus, 2),
            "explanation": f"Transaction is in the merchant's top {100 - features.transaction_value_percentile * 100:.0f}% by value"
        })
        
        # Calculate base score
        score = value_component + likelihood_component + percentile_bonus
        
        # Adjust for time sensitivity (±10 points)
        time_adjustment = 0
        if features.time_since_failure_hours:
            if features.time_since_failure_hours < 24:
                time_adjustment = 10
                score_factors.append({
                    "name": "time_sensitivity",
                    "impact": 10,
                    "explanation": "Recent failure (within 24 hours) - higher urgency"
                })
            elif features.time_since_failure_hours > 168:  # 7 days
                time_adjustment = -10
                score_factors.append({
                    "name": "time_sensitivity",
                    "impact": -10,
                    "explanation": "Aged failure (over 7 days) - lower urgency"
                })
        score += time_adjustment
        
        # Adjust for retry count (±15 points)
        retry_adjustment = 0
        if features.retry_count == 0:
            retry_adjustment = 5
            score_factors.append({
                "name": "retry_context",
                "impact": 5,
                "explanation": "No previous retry attempts - good recovery potential"
            })
        elif features.retry_count >= 3:
            retry_adjustment = -15
            score_factors.append({
                "name": "retry_context",
                "impact": -15,
                "explanation": f"{features.retry_count} retry attempts - lower recovery potential"
            })
        score += retry_adjustment
        
        # Ensure score is bounded
        score = max(0.0, min(100.0, score))
        
        # Determine priority using merchant-relative logic
        priority = self._determine_priority(score, features, recovery_probability)
        
        # Generate explanation
        explanation = self._generate_explanation(
            score,
            priority,
            features,
            recovery_probability,
            revenue_at_risk
        )
        
        return OpportunityScore(
            score=round(score, 2),
            priority=priority,
            explanation=explanation,
            score_factors=score_factors
        )
    
    def _determine_priority(
        self,
        score: float,
        features: FeatureSet,
        recovery_probability: RecoveryProbability
    ) -> PriorityLevel:
        """Determine priority level using merchant-relative logic.
        
        No absolute transaction thresholds are used. Priority is determined
        by merchant-relative value percentile and recovery likelihood.
        """
        # Use merchant-relative value percentile instead of absolute amount
        # High percentile (top 10%) with good recovery likelihood gets boosted priority
        if features.transaction_value_percentile >= 0.9 and recovery_probability.probability > 0.6:
            return PriorityLevel.CRITICAL
        
        # Use score-based thresholds (merchant-relative scoring already applied)
        if score >= self.priority_thresholds[PriorityLevel.CRITICAL]:
            return PriorityLevel.CRITICAL
        elif score >= self.priority_thresholds[PriorityLevel.HIGH]:
            return PriorityLevel.HIGH
        elif score >= self.priority_thresholds[PriorityLevel.MEDIUM]:
            return PriorityLevel.MEDIUM
        else:
            return PriorityLevel.LOW
    
    def _generate_explanation(
        self,
        score: float,
        priority: PriorityLevel,
        features: FeatureSet,
        recovery_probability: RecoveryProbability,
        revenue_at_risk: int
    ) -> str:
        """Generate explanation for the opportunity score."""
        amount_inr = features.payment_amount / 100  # Convert paise to rupees
        
        explanation_parts = []
        
        # Value component
        explanation_parts.append(f"Transaction value: ₹{amount_inr:.2f}")
        
        # Probability component
        explanation_parts.append(
            f"Recovery probability: {recovery_probability.probability * 100:.0f}%"
        )
        
        # Retry context
        if features.retry_count == 0:
            explanation_parts.append("No previous retry attempts")
        elif features.retry_count == 1:
            explanation_parts.append("Single retry attempt")
        else:
            explanation_parts.append(f"{features.retry_count} retry attempts")
        
        # Time context
        if features.time_since_failure_hours:
            if features.time_since_failure_hours < 24:
                explanation_parts.append("Recent failure (within 24 hours)")
            elif features.time_since_failure_hours > 168:
                explanation_parts.append("Aged failure (over 7 days)")
        
        # Priority rationale
        if priority == PriorityLevel.CRITICAL:
            explanation_parts.append("High-value with good recovery potential")
        elif priority == PriorityLevel.HIGH:
            explanation_parts.append("Good recovery opportunity")
        elif priority == PriorityLevel.LOW:
            explanation_parts.append("Lower priority due to low value or low probability")
        
        return ". ".join(explanation_parts) + "."
    
    def _get_value_explanation(self, features: FeatureSet) -> str:
        """Generate explanation for transaction value component."""
        amount_inr = features.payment_amount / 100  # Convert paise to rupees
        
        if features.transaction_value_percentile >= 0.9:
            return f"Transaction (₹{amount_inr:.2f}) is in the merchant's top 10% by value"
        elif features.transaction_value_percentile >= 0.75:
            return f"Transaction (₹{amount_inr:.2f}) is in the merchant's top 25% by value"
        elif features.transaction_value_percentile >= 0.5:
            return f"Transaction (₹{amount_inr:.2f}) is above merchant average"
        elif features.transaction_value_percentile >= 0.25:
            return f"Transaction (₹{amount_inr:.2f}) is below merchant average"
        else:
            return f"Transaction (₹{amount_inr:.2f}) is in the merchant's bottom 25% by value"
