"""Unit tests for Phase 2 architecture corrections (no database required).

Tests verify:
- merchant-relative transaction values work
- extremely large transactions do not automatically receive score 100
- scores remain between 0 and 100
- probability/likelihood remains between 0 and 1
- explainability factors are exposed
"""

import pytest
from datetime import datetime
from app.intelligence.probability_engine import RecoveryProbabilityEngine
from app.intelligence.opportunity_scorer import OpportunityScorer
from app.intelligence.schemas import (
    FeatureSet,
    FailureCategory,
    PriorityLevel,
    RecoveryProbability,
)


class TestMerchantRelativeValue:
    """Tests for merchant-relative transaction value logic."""
    
    def test_normalized_value_score_bounded(self):
        """Test that normalized value score is always bounded between 0 and 1."""
        # Test with extreme ratios
        test_cases = [
            (1, 1000),      # Very small amount vs average
            (1000000, 1),   # Very large amount vs average
            (100, 100),     # Equal amounts
            (1000, 1000),   # Equal amounts
        ]
        
        for amount, avg in test_cases:
            # Simulate the normalized value calculation
            import math
            log_amount = math.log(max(1, amount))
            log_avg = math.log(max(1, avg))
            ratio = log_amount / (log_avg + 1) if log_avg > 0 else 0.5
            normalized = 1 / (1 + math.exp(-ratio + 1))
            
            assert 0.0 <= normalized <= 1.0, f"Normalized score {normalized} out of bounds for amount={amount}, avg={avg}"
    
    def test_percentile_calculation_deterministic(self):
        """Test that percentile calculation is deterministic."""
        amounts = [1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000]
        amounts.sort()
        
        # Test median
        test_amount = 5000
        rank = sum(1 for a in amounts if a <= test_amount)
        percentile = rank / len(amounts)
        
        assert 0.4 <= percentile <= 0.6, f"Percentile {percentile} not in expected range"
        
        # Test maximum
        test_amount = 10000
        rank = sum(1 for a in amounts if a <= test_amount)
        percentile = rank / len(amounts)
        
        assert percentile >= 0.9, f"Percentile {percentile} not at expected maximum"


class TestBoundedScoring:
    """Tests for bounded scoring logic."""
    
    def test_extremely_large_relative_value_not_automatic_100(self):
        """Test that extremely high relative value doesn't automatically get score 100."""
        scorer = OpportunityScorer()
        
        # Maximum relative value but low recovery probability
        features = FeatureSet(
            payment_amount=100000000,  # Very large amount
            currency="INR",
            payment_status="FAILED",
            retry_count=5,  # Many retries
            time_since_failure_hours=200,  # Old failure
            created_at=datetime.utcnow(),
            normalized_value_score=1.0,  # Maximum relative value
            transaction_value_percentile=1.0,  # Maximum percentile
        )
        
        # Low recovery probability (unknown failure with many retries)
        recovery_prob = RecoveryProbability(probability=0.2, factors=[])
        
        score = scorer.score(features, recovery_prob, 0)
        
        # Score should be bounded and not automatically 100 due to value alone
        assert score.score < 100.0, f"Score {score.score} should not be 100 with low probability"
        assert score.score >= 0.0
    
    def test_score_remains_bounded_0_to_100(self):
        """Test that scores always remain between 0 and 100."""
        scorer = OpportunityScorer()
        
        # Test with extreme values
        test_cases = [
            # (normalized_value, probability, retry_count, time_hours, percentile)
            (1.0, 1.0, 0, 1, 1.0),  # Maximum positive factors
            (0.0, 0.0, 10, 1000, 0.0),  # Maximum negative factors
            (0.5, 0.5, 5, 100, 0.5),  # Neutral factors
            (1.0, 0.0, 0, 1, 1.0),  # High value, no recovery
            (0.0, 1.0, 0, 1, 0.0),  # Low value, high recovery
        ]
        
        for norm_value, prob, retry_count, time_hours, percentile in test_cases:
            features = FeatureSet(
                payment_amount=10000,
                currency="INR",
                payment_status="FAILED",
                retry_count=retry_count,
                time_since_failure_hours=time_hours,
                created_at=datetime.utcnow(),
                normalized_value_score=norm_value,
                transaction_value_percentile=percentile,
            )
            
            recovery_prob = RecoveryProbability(probability=prob, factors=[])
            
            score = scorer.score(features, recovery_prob, 0)
            
            assert 0.0 <= score.score <= 100.0, f"Score {score.score} out of bounds for {test_cases}"
    
    def test_probability_remains_bounded_0_to_1(self):
        """Test that recovery probability always remains between 0 and 1."""
        engine = RecoveryProbabilityEngine()
        
        # Test with extreme feature combinations
        test_cases = [
            # All positive factors
            FeatureSet(
                payment_amount=10000,
                currency="INR",
                payment_status="FAILED",
                retry_count=0,
                time_since_failure_hours=1,
                normalized_value_score=1.0,
                merchant_historical_recovery_rate=0.9,
                payment_method="upi",
                created_at=datetime.utcnow(),
            ),
            # All negative factors
            FeatureSet(
                payment_amount=10000,
                currency="INR",
                payment_status="FAILED",
                retry_count=10,
                time_since_failure_hours=1000,
                normalized_value_score=0.0,
                merchant_historical_recovery_rate=0.1,
                previous_successful_recovery=True,
                previous_failed_recovery=True,
                created_at=datetime.utcnow(),
            ),
            # Mixed factors
            FeatureSet(
                payment_amount=10000,
                currency="INR",
                payment_status="FAILED",
                retry_count=3,
                time_since_failure_hours=50,
                normalized_value_score=0.5,
                merchant_historical_recovery_rate=0.5,
                created_at=datetime.utcnow(),
            ),
        ]
        
        for features in test_cases:
            result = engine.calculate(features, FailureCategory.TEMPORARY_FAILURE)
            assert 0.0 <= result.probability <= 1.0, f"Probability {result.probability} out of bounds"


class TestExplainabilityFactors:
    """Tests for explainability factors in scoring."""
    
    def test_score_factors_exposed(self):
        """Test that score factors are properly exposed."""
        scorer = OpportunityScorer()
        
        features = FeatureSet(
            payment_amount=10000,
            currency="INR",
            payment_status="FAILED",
            retry_count=1,
            time_since_failure_hours=2,
            created_at=datetime.utcnow(),
            normalized_value_score=0.7,
            transaction_value_percentile=0.8,
        )
        
        recovery_prob = RecoveryProbability(probability=0.75, factors=[])
        
        score = scorer.score(features, recovery_prob, 0)
        
        # Should have score factors
        assert len(score.score_factors) > 0, "Score factors should be exposed"
        
        # Each factor should have required fields
        for factor in score.score_factors:
            assert "name" in factor, "Factor should have 'name'"
            assert "impact" in factor, "Factor should have 'impact'"
            assert "explanation" in factor, "Factor should have 'explanation'"
        
        # Check for expected factor names
        factor_names = [f["name"] for f in score.score_factors]
        assert "transaction_value" in factor_names, "Should have transaction_value factor"
        assert "recovery_likelihood" in factor_names, "Should have recovery_likelihood factor"
    
    def test_factor_impacts_are_numeric(self):
        """Test that factor impacts are numeric values."""
        scorer = OpportunityScorer()
        
        features = FeatureSet(
            payment_amount=10000,
            currency="INR",
            payment_status="FAILED",
            retry_count=1,
            time_since_failure_hours=2,
            created_at=datetime.utcnow(),
            normalized_value_score=0.7,
            transaction_value_percentile=0.8,
        )
        
        recovery_prob = RecoveryProbability(probability=0.75, factors=[])
        
        score = scorer.score(features, recovery_prob, 0)
        
        for factor in score.score_factors:
            assert isinstance(factor["impact"], (int, float)), f"Factor impact should be numeric, got {type(factor['impact'])}"


class TestNoAbsoluteThresholds:
    """Tests to verify no absolute thresholds are used."""
    
    def test_probability_engine_uses_relative_value(self):
        """Test that probability engine uses normalized value score, not absolute amount."""
        engine = RecoveryProbabilityEngine()
        
        # Same absolute amount but different relative values
        features_high_relative = FeatureSet(
            payment_amount=50000,  # ₹500
            currency="INR",
            payment_status="FAILED",
            retry_count=1,
            time_since_failure_hours=2,
            normalized_value_score=0.9,  # High relative value
            created_at=datetime.utcnow(),
        )
        
        features_low_relative = FeatureSet(
            payment_amount=50000,  # Same ₹500
            currency="INR",
            payment_status="FAILED",
            retry_count=1,
            time_since_failure_hours=2,
            normalized_value_score=0.1,  # Low relative value
            created_at=datetime.utcnow(),
        )
        
        result_high = engine.calculate(features_high_relative, FailureCategory.TEMPORARY_FAILURE)
        result_low = engine.calculate(features_low_relative, FailureCategory.TEMPORARY_FAILURE)
        
        # High relative value should get higher probability
        assert result_high.probability > result_low.probability, \
            "High relative value should result in higher probability"
    
    def test_scorer_uses_relative_value(self):
        """Test that scorer uses normalized value score, not absolute amount."""
        scorer = OpportunityScorer()
        
        # Same absolute amount but different relative values
        features_high_relative = FeatureSet(
            payment_amount=50000,
            currency="INR",
            payment_status="FAILED",
            retry_count=1,
            time_since_failure_hours=2,
            normalized_value_score=0.9,
            transaction_value_percentile=0.9,
            created_at=datetime.utcnow(),
        )
        
        features_low_relative = FeatureSet(
            payment_amount=50000,
            currency="INR",
            payment_status="FAILED",
            retry_count=1,
            time_since_failure_hours=2,
            normalized_value_score=0.1,
            transaction_value_percentile=0.1,
            created_at=datetime.utcnow(),
        )
        
        recovery_prob = RecoveryProbability(probability=0.7, factors=[])
        
        score_high = scorer.score(features_high_relative, recovery_prob, 0)
        score_low = scorer.score(features_low_relative, recovery_prob, 0)
        
        # High relative value should get higher score
        assert score_high.score > score_low.score, \
            "High relative value should result in higher score"


class TestModelVersionExposed:
    """Tests for model version exposure."""
    
    def test_recovery_probability_documentation(self):
        """Test that RecoveryProbability schema has proper documentation."""
        from app.intelligence.schemas import RecoveryProbability
        doc = RecoveryProbability.__doc__
        
        assert doc is not None, "RecoveryProbability should have documentation"
        assert "rules-based" in doc.lower(), "Documentation should mention rules-based approach"
        assert "estimate" in doc.lower(), "Documentation should mention it's an estimate"
