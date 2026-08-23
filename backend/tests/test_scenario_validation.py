"""Validation tests for Phase 2 architecture corrections demo scenarios.

Validates the required demo scenarios:
Scenario A: High-value + recoverable failure -> HIGH/CRITICAL
Scenario B: Low-value + low recovery likelihood -> LOW/MEDIUM
Scenario C: High-value + low recovery likelihood -> not automatically CRITICAL
Scenario D: Repeated failures -> lower recovery likelihood / different recommendation
"""

import pytest
from datetime import datetime
from app.intelligence.probability_engine import RecoveryProbabilityEngine
from app.intelligence.opportunity_scorer import OpportunityScorer
from app.intelligence.failure_classifier import FailureClassifier
from app.intelligence.schemas import (
    FeatureSet,
    FailureCategory,
    PriorityLevel,
)


class TestScenarioValidation:
    """Validation tests for demo scenarios."""
    
    def test_scenario_a_high_value_recoverable(self):
        """Scenario A: High relative value + recoverable failure -> HIGH/CRITICAL."""
        # High merchant-relative value (top 10%) with recoverable failure
        features = FeatureSet(
            payment_amount=2500000,  # ₹25,000
            currency="INR",
            payment_status="FAILED",
            failure_code="BANK_ERROR",
            failure_description="Bank processing error - temporary failure",
            retry_count=1,
            time_since_failure_hours=2,
            created_at=datetime.utcnow(),
            normalized_value_score=0.95,  # Top 5% relative value
            transaction_value_percentile=0.95,  # Top 5% percentile
            payment_method="upi",
            merchant_historical_recovery_rate=0.7,  # Good merchant recovery rate
        )
        
        classifier = FailureClassifier()
        prob_engine = RecoveryProbabilityEngine()
        scorer = OpportunityScorer()
        
        classification = classifier.classify(features)
        recovery_prob = prob_engine.calculate(features, classification.category)
        score = scorer.score(features, recovery_prob, 0)
        
        # Should be HIGH or CRITICAL
        assert score.priority in [PriorityLevel.HIGH, PriorityLevel.CRITICAL], \
            f"Scenario A should be HIGH/CRITICAL, got {score.priority.value}"
        # With good merchant recovery rate, should have reasonable recovery likelihood
        assert recovery_prob.probability > 0.5, \
            f"Scenario A should have reasonable recovery likelihood, got {recovery_prob.probability}"
    
    def test_scenario_b_low_value_low_likelihood(self):
        """Scenario B: Low relative value + low recovery likelihood -> LOW/MEDIUM."""
        # Low merchant-relative value with low recovery likelihood
        features = FeatureSet(
            payment_amount=50000,  # ₹500
            currency="INR",
            payment_status="FAILED",
            failure_code="BAD_REQUEST_ERROR",
            failure_description="Insufficient funds",
            retry_count=3,  # Multiple retries
            time_since_failure_hours=48,  # Aged
            created_at=datetime.utcnow(),
            normalized_value_score=0.1,  # Bottom 10% relative value
            transaction_value_percentile=0.1,  # Bottom 10% percentile
            payment_method="card",
        )
        
        classifier = FailureClassifier()
        prob_engine = RecoveryProbabilityEngine()
        scorer = OpportunityScorer()
        
        classification = classifier.classify(features)
        recovery_prob = prob_engine.calculate(features, classification.category)
        score = scorer.score(features, recovery_prob, 0)
        
        # Should be LOW or MEDIUM
        assert score.priority in [PriorityLevel.LOW, PriorityLevel.MEDIUM], \
            f"Scenario B should be LOW/MEDIUM, got {score.priority.value}"
        assert recovery_prob.probability < 0.6, \
            f"Scenario B should have low recovery likelihood, got {recovery_prob.probability}"
    
    def test_scenario_c_high_value_low_likelihood_not_critical(self):
        """Scenario C: High relative value + low recovery likelihood -> not automatically CRITICAL."""
        # High merchant-relative value but low recovery likelihood
        features = FeatureSet(
            payment_amount=5000000,  # ₹50,000
            currency="INR",
            payment_status="FAILED",
            failure_code="AUTHENTICATION_ERROR",
            failure_description="Authentication failed",
            retry_count=2,
            time_since_failure_hours=24,
            created_at=datetime.utcnow(),
            normalized_value_score=0.9,  # High relative value
            transaction_value_percentile=0.9,  # High percentile
            payment_method="netbanking",
        )
        
        classifier = FailureClassifier()
        prob_engine = RecoveryProbabilityEngine()
        scorer = OpportunityScorer()
        
        classification = classifier.classify(features)
        recovery_prob = prob_engine.calculate(features, classification.category)
        score = scorer.score(features, recovery_prob, 0)
        
        # Should NOT be automatically CRITICAL due to low recovery likelihood
        assert score.priority != PriorityLevel.CRITICAL or recovery_prob.probability > 0.6, \
            f"Scenario C should not be CRITICAL with low recovery likelihood"
    
    def test_scenario_d_repeated_failures_lower_likelihood(self):
        """Scenario D: Repeated failures -> lower recovery likelihood."""
        # Same failure with different retry counts
        features_single_retry = FeatureSet(
            payment_amount=10000,
            currency="INR",
            payment_status="FAILED",
            failure_code="NETWORK_ERROR",
            failure_description="Network connectivity issue",
            retry_count=1,  # Single retry
            time_since_failure_hours=2,
            created_at=datetime.utcnow(),
            normalized_value_score=0.5,
            transaction_value_percentile=0.5,
            payment_method="upi",
        )
        
        features_multiple_retries = FeatureSet(
            payment_amount=10000,
            currency="INR",
            payment_status="FAILED",
            failure_code="NETWORK_ERROR",
            failure_description="Network connectivity issue",
            retry_count=3,  # Multiple retries
            time_since_failure_hours=2,
            created_at=datetime.utcnow(),
            normalized_value_score=0.5,
            transaction_value_percentile=0.5,
            payment_method="upi",
        )
        
        classifier = FailureClassifier()
        prob_engine = RecoveryProbabilityEngine()
        
        classification = classifier.classify(features_single_retry)
        prob_single = prob_engine.calculate(features_single_retry, classification.category)
        
        classification = classifier.classify(features_multiple_retries)
        prob_multiple = prob_engine.calculate(features_multiple_retries, classification.category)
        
        # Multiple retries should have lower recovery likelihood
        assert prob_multiple.probability < prob_single.probability, \
            f"Multiple retries should have lower recovery likelihood"
        
        # Check that multiple_retries factor is present
        assert any(f["factor"] == "multiple_retries" for f in prob_multiple.factors), \
            "Multiple retries factor should be present"
    
    def test_merchant_relative_behavior(self):
        """Validate that same absolute amount behaves differently for different merchants."""
        # Same ₹500 amount with different relative values
        features_small_merchant = FeatureSet(
            payment_amount=50000,  # ₹500
            currency="INR",
            payment_status="FAILED",
            retry_count=1,
            time_since_failure_hours=2,
            created_at=datetime.utcnow(),
            normalized_value_score=0.9,  # High relative to small merchant
            transaction_value_percentile=0.9,
        )
        
        features_large_merchant = FeatureSet(
            payment_amount=50000,  # Same ₹500
            currency="INR",
            payment_status="FAILED",
            retry_count=1,
            time_since_failure_hours=2,
            created_at=datetime.utcnow(),
            normalized_value_score=0.1,  # Low relative to large merchant
            transaction_value_percentile=0.1,
        )
        
        prob_engine = RecoveryProbabilityEngine()
        scorer = OpportunityScorer()
        
        prob_small = prob_engine.calculate(features_small_merchant, FailureCategory.TEMPORARY_FAILURE)
        prob_large = prob_engine.calculate(features_large_merchant, FailureCategory.TEMPORARY_FAILURE)
        
        score_small = scorer.score(features_small_merchant, prob_small, 0)
        score_large = scorer.score(features_large_merchant, prob_large, 0)
        
        # Small merchant should get higher score for same amount
        assert score_small.score > score_large.score, \
            "Same amount should score higher for small merchant (higher relative value)"
