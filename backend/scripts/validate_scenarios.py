"""Validation script for Phase 2 architecture corrections.

Validates the required demo scenarios:
Scenario A: High-value + recoverable failure -> HIGH/CRITICAL
Scenario B: Low-value + low recovery likelihood -> LOW/MEDIUM
Scenario C: High-value + low recovery likelihood -> not automatically CRITICAL
Scenario D: Repeated failures -> lower recovery likelihood / different recommendation
"""

from datetime import datetime
from app.intelligence.feature_extractor import FeatureExtractor
from app.intelligence.probability_engine import RecoveryProbabilityEngine
from app.intelligence.opportunity_scorer import OpportunityScorer
from app.intelligence.failure_classifier import FailureClassifier
from app.intelligence.schemas import (
    FeatureSet,
    FailureCategory,
    PriorityLevel,
)


def validate_scenario_a():
    """Scenario A: High relative value + recoverable failure -> HIGH/CRITICAL."""
    print("\n=== Scenario A: High relative value + recoverable failure ===")
    
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
    )
    
    classifier = FailureClassifier()
    prob_engine = RecoveryProbabilityEngine()
    scorer = OpportunityScorer()
    
    classification = classifier.classify(features)
    recovery_prob = prob_engine.calculate(features, classification.category)
    score = scorer.score(features, recovery_prob, 0)
    
    print(f"Failure Category: {classification.category.value}")
    print(f"Recovery Likelihood: {recovery_prob.probability:.2f}")
    print(f"Opportunity Score: {score.score:.2f}")
    print(f"Priority: {score.priority.value}")
    print(f"Score Factors: {[f['name'] for f in score.score_factors]}")
    
    # Should be HIGH or CRITICAL
    assert score.priority in [PriorityLevel.HIGH, PriorityLevel.CRITICAL], \
        f"Scenario A should be HIGH/CRITICAL, got {score.priority.value}"
    assert recovery_prob.probability > 0.6, \
        f"Scenario A should have good recovery likelihood, got {recovery_prob.probability}"
    
    print("✅ Scenario A validated: HIGH/CRITICAL as expected")


def validate_scenario_b():
    """Scenario B: Low relative value + low recovery likelihood -> LOW/MEDIUM."""
    print("\n=== Scenario B: Low relative value + low recovery likelihood ===")
    
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
    
    print(f"Failure Category: {classification.category.value}")
    print(f"Recovery Likelihood: {recovery_prob.probability:.2f}")
    print(f"Opportunity Score: {score.score:.2f}")
    print(f"Priority: {score.priority.value}")
    
    # Should be LOW or MEDIUM
    assert score.priority in [PriorityLevel.LOW, PriorityLevel.MEDIUM], \
        f"Scenario B should be LOW/MEDIUM, got {score.priority.value}"
    assert recovery_prob.probability < 0.6, \
        f"Scenario B should have low recovery likelihood, got {recovery_prob.probability}"
    
    print("✅ Scenario B validated: LOW/MEDIUM as expected")


def validate_scenario_c():
    """Scenario C: High relative value + low recovery likelihood -> not automatically CRITICAL."""
    print("\n=== Scenario C: High relative value + low recovery likelihood ===")
    
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
    
    print(f"Failure Category: {classification.category.value}")
    print(f"Recovery Likelihood: {recovery_prob.probability:.2f}")
    print(f"Opportunity Score: {score.score:.2f}")
    print(f"Priority: {score.priority.value}")
    
    # Should NOT be automatically CRITICAL due to low recovery likelihood
    # Even with high relative value, if recovery likelihood is low, priority should be MEDIUM
    assert score.priority != PriorityLevel.CRITICAL or recovery_prob.probability > 0.6, \
        f"Scenario C should not be CRITICAL with low recovery likelihood"
    
    print("✅ Scenario C validated: Not automatically CRITICAL as expected")


def validate_scenario_d():
    """Scenario D: Repeated failures -> lower recovery likelihood."""
    print("\n=== Scenario D: Repeated failures -> lower recovery likelihood ===")
    
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
    
    print(f"Single retry recovery likelihood: {prob_single.probability:.2f}")
    print(f"Multiple retries recovery likelihood: {prob_multiple.probability:.2f}")
    
    # Multiple retries should have lower recovery likelihood
    assert prob_multiple.probability < prob_single.probability, \
        f"Multiple retries should have lower recovery likelihood"
    
    # Check that multiple_retries factor is present
    assert any(f["factor"] == "multiple_retries" for f in prob_multiple.factors), \
        "Multiple retries factor should be present"
    
    print("✅ Scenario D validated: Repeated failures have lower recovery likelihood")


def validate_merchant_relative_behavior():
    """Validate that same absolute amount behaves differently for different merchants."""
    print("\n=== Merchant-Relative Value Behavior ===")
    
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
    
    print(f"₹500 for small merchant: Score={score_small.score:.2f}, Priority={score_small.priority.value}")
    print(f"₹500 for large merchant: Score={score_large.score:.2f}, Priority={score_large.priority.value}")
    
    # Small merchant should get higher score for same amount
    assert score_small.score > score_large.score, \
        "Same amount should score higher for small merchant (higher relative value)"
    
    print("✅ Merchant-relative behavior validated: Same amount scores differently")


def validate_bounded_scoring():
    """Validate that scores remain bounded 0-100 and probabilities 0-1."""
    print("\n=== Bounded Scoring Validation ===")
    
    scorer = OpportunityScorer()
    prob_engine = RecoveryProbabilityEngine()
    
    # Test extreme cases
    extreme_cases = [
        ("Maximum positive", 1.0, 1.0, 0, 1),
        ("Maximum negative", 0.0, 0.0, 10, 1000),
    ]
    
    for name, norm_val, prob, retries, hours in extreme_cases:
        features = FeatureSet(
            payment_amount=10000,
            currency="INR",
            payment_status="FAILED",
            retry_count=retries,
            time_since_failure_hours=hours,
            created_at=datetime.utcnow(),
            normalized_value_score=norm_val,
            transaction_value_percentile=norm_val,
        )
        
        recovery_prob = type('obj', (object,), {'probability': prob, 'factors': []})()
        score = scorer.score(features, recovery_prob, 0)
        
        print(f"{name}: Score={score.score:.2f}")
        assert 0.0 <= score.score <= 100.0, f"Score out of bounds: {score.score}"
    
    # Test probability bounds
    features = FeatureSet(
        payment_amount=10000,
        currency="INR",
        payment_status="FAILED",
        retry_count=10,
        time_since_failure_hours=1000,
        previous_successful_recovery=True,
        previous_failed_recovery=True,
        created_at=datetime.utcnow(),
        normalized_value_score=0.0,
    )
    
    prob = prob_engine.calculate(features, FailureCategory.UNKNOWN)
    print(f"Extreme negative case probability: {prob.probability:.2f}")
    assert 0.0 <= prob.probability <= 1.0, f"Probability out of bounds: {prob.probability}"
    
    print("✅ Bounded scoring validated: All scores 0-100, probabilities 0-1")


def main():
    """Run all validation scenarios."""
    print("=" * 60)
    print("Phase 2 Architecture Corrections Validation")
    print("=" * 60)
    
    try:
        validate_scenario_a()
        validate_scenario_b()
        validate_scenario_c()
        validate_scenario_d()
        validate_merchant_relative_behavior()
        validate_bounded_scoring()
        
        print("\n" + "=" * 60)
        print("✅ ALL SCENARIOS VALIDATED SUCCESSFULLY")
        print("=" * 60)
        print("\nSummary:")
        print("- Scenario A: High relative value + recoverable → HIGH/CRITICAL ✓")
        print("- Scenario B: Low relative value + low likelihood → LOW/MEDIUM ✓")
        print("- Scenario C: High relative value + low likelihood → Not auto CRITICAL ✓")
        print("- Scenario D: Repeated failures → Lower recovery likelihood ✓")
        print("- Merchant-relative behavior: Same amount scores differently ✓")
        print("- Bounded scoring: All scores 0-100, probabilities 0-1 ✓")
        
    except AssertionError as e:
        print(f"\n❌ VALIDATION FAILED: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
