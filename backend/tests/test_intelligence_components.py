"""Unit tests for Revenue Intelligence components."""

import pytest
from datetime import datetime, timedelta
from app.intelligence.failure_classifier import FailureClassifier
from app.intelligence.revenue_calculator import RevenueAtRiskCalculator
from app.intelligence.probability_engine import RecoveryProbabilityEngine
from app.intelligence.opportunity_scorer import OpportunityScorer
from app.intelligence.intervention_engine import InterventionRecommendationEngine
from app.intelligence.schemas import (
    FeatureSet,
    FailureCategory,
    PriorityLevel,
)


class TestFailureClassifier:
    """Tests for FailureClassifier."""
    
    def setup_method(self):
        self.classifier = FailureClassifier()
    
    def test_classify_insufficient_funds(self):
        """Test classification of insufficient funds failure."""
        features = FeatureSet(
            payment_amount=10000,
            currency="INR",
            payment_method="card",
            payment_status="FAILED",
            failure_code="BAD_REQUEST_ERROR",
            failure_message="Insufficient funds in account",
            retry_count=1,
            created_at=datetime.utcnow(),
        )
        
        result = self.classifier.classify(features)
        
        assert result.category == FailureCategory.INSUFFICIENT_FUNDS
        assert "insufficient" in result.normalized_reason.lower()
        assert result.confidence > 0
    
    def test_classify_network_failure(self):
        """Test classification of network failure."""
        features = FeatureSet(
            payment_amount=10000,
            currency="INR",
            payment_method="upi",
            payment_status="FAILED",
            failure_code="NETWORK_ERROR",
            failure_message="Network connectivity issue",
            retry_count=1,
            created_at=datetime.utcnow(),
        )
        
        result = self.classifier.classify(features)
        
        assert result.category == FailureCategory.NETWORK_FAILURE
        assert "network" in result.normalized_reason.lower()
    
    def test_classify_temporary_failure(self):
        """Test classification of temporary failure."""
        features = FeatureSet(
            payment_amount=10000,
            currency="INR",
            payment_method="upi",
            payment_status="FAILED",
            failure_code="TIMEOUT_ERROR",
            failure_message="Request timeout",
            retry_count=1,
            created_at=datetime.utcnow(),
        )
        
        result = self.classifier.classify(features)
        
        assert result.category == FailureCategory.TEMPORARY_FAILURE
    
    def test_classify_unknown_failure(self):
        """Test classification of unknown failure."""
        features = FeatureSet(
            payment_amount=10000,
            currency="INR",
            payment_method="card",
            payment_status="FAILED",
            failure_code="UNKNOWN_ERROR",
            failure_message="Unknown error",
            retry_count=1,
            created_at=datetime.utcnow(),
        )
        
        result = self.classifier.classify(features)
        
        assert result.category == FailureCategory.UNKNOWN
        assert result.confidence < 0.5  # Low confidence for unknown
    
    def test_classify_without_failure_code(self):
        """Test classification without failure code."""
        features = FeatureSet(
            payment_amount=10000,
            currency="INR",
            payment_method="card",
            payment_status="FAILED",
            failure_code=None,
            failure_message="Payment failed",
            retry_count=1,
            created_at=datetime.utcnow(),
        )
        
        result = self.classifier.classify(features)
        
        # Should still return a classification
        assert result.category in FailureCategory


class TestRevenueAtRiskCalculator:
    """Tests for RevenueAtRiskCalculator."""
    
    def setup_method(self):
        self.calculator = RevenueAtRiskCalculator()
    
    def test_calculate_temporary_failure(self):
        """Test revenue calculation for temporary failure."""
        features = FeatureSet(
            payment_amount=10000,
            currency="INR",
            payment_status="FAILED",
            retry_count=1,
            created_at=datetime.utcnow(),
        )
        
        result = self.calculator.calculate(
            features,
            FailureCategory.TEMPORARY_FAILURE,
            0.75
        )
        
        assert result.gross_failed_revenue == 10000
        assert result.potentially_recoverable_revenue > 0
        assert result.estimated_recoverable_revenue == 7500  # 10000 * 0.75
    
    def test_calculate_already_recovered(self):
        """Test revenue calculation for already recovered payment."""
        features = FeatureSet(
            payment_amount=10000,
            currency="INR",
            payment_status="FAILED",
            retry_count=1,
            created_at=datetime.utcnow(),
            previous_successful_recovery=True,
        )
        
        result = self.calculator.calculate(
            features,
            FailureCategory.TEMPORARY_FAILURE,
            0.75
        )
        
        assert result.recovered_revenue == 10000
        assert result.potentially_recoverable_revenue == 0
        assert result.estimated_recoverable_revenue == 0
    
    def test_calculate_insufficient_funds(self):
        """Test revenue calculation for insufficient funds."""
        features = FeatureSet(
            payment_amount=50000,
            currency="INR",
            payment_status="FAILED",
            retry_count=2,
            created_at=datetime.utcnow(),
        )
        
        result = self.calculator.calculate(
            features,
            FailureCategory.INSUFFICIENT_FUNDS,
            0.50
        )
        
        assert result.gross_failed_revenue == 50000
        assert result.estimated_recoverable_revenue == 25000  # 50000 * 0.50
    
    def test_calculate_zero_amount(self):
        """Test revenue calculation for zero amount."""
        features = FeatureSet(
            payment_amount=0,
            currency="INR",
            payment_status="FAILED",
            retry_count=1,
            created_at=datetime.utcnow(),
        )
        
        result = self.calculator.calculate(
            features,
            FailureCategory.TEMPORARY_FAILURE,
            0.75
        )
        
        assert result.gross_failed_revenue == 0
        assert result.estimated_recoverable_revenue == 0


class TestRecoveryProbabilityEngine:
    """Tests for RecoveryProbabilityEngine."""
    
    def setup_method(self):
        self.engine = RecoveryProbabilityEngine()
    
    def test_calculate_temporary_failure_no_retries(self):
        """Test probability calculation for temporary failure with no retries."""
        features = FeatureSet(
            payment_amount=10000,
            currency="INR",
            payment_status="FAILED",
            retry_count=0,
            time_since_failure_hours=2,
            created_at=datetime.utcnow(),
        )
        
        result = self.engine.calculate(features, FailureCategory.TEMPORARY_FAILURE)
        
        assert 0.0 <= result.probability <= 1.0
        assert len(result.factors) > 0
        assert result.probability > 0.7  # Temporary failure with no retries should have high probability
    
    def test_calculate_multiple_retries(self):
        """Test probability calculation with multiple retries."""
        features = FeatureSet(
            payment_amount=10000,
            currency="INR",
            payment_status="FAILED",
            retry_count=3,
            time_since_failure_hours=2,
            created_at=datetime.utcnow(),
        )
        
        result = self.engine.calculate(features, FailureCategory.TEMPORARY_FAILURE)
        
        assert result.probability < 0.7  # Multiple retries should reduce probability
        assert any(f["factor"] == "multiple_retries" for f in result.factors)
    
    def test_calculate_aged_failure(self):
        """Test probability calculation for aged failure."""
        features = FeatureSet(
            payment_amount=10000,
            currency="INR",
            payment_status="FAILED",
            retry_count=1,
            time_since_failure_hours=200,  # Over 7 days
            created_at=datetime.utcnow(),
        )
        
        result = self.engine.calculate(features, FailureCategory.TEMPORARY_FAILURE)
        
        assert any(f["factor"] == "aged_failure" for f in result.factors)
    
    def test_calculate_high_relative_value_payment(self):
        """Test probability calculation for high relative value payment."""
        features = FeatureSet(
            payment_amount=150000,
            currency="INR",
            payment_status="FAILED",
            retry_count=1,
            time_since_failure_hours=2,
            created_at=datetime.utcnow(),
            normalized_value_score=0.9,  # High relative value
        )
        
        result = self.engine.calculate(features, FailureCategory.TEMPORARY_FAILURE)
        
        assert any(f["factor"] == "high_relative_value" for f in result.factors)
    
    def test_calculate_already_recovered(self):
        """Test probability calculation for already recovered payment."""
        features = FeatureSet(
            payment_amount=10000,
            currency="INR",
            payment_status="FAILED",
            retry_count=1,
            previous_successful_recovery=True,
            created_at=datetime.utcnow(),
        )
        
        result = self.engine.calculate(features, FailureCategory.TEMPORARY_FAILURE)
        
        assert result.probability < 0.5  # Already recovered should have low probability
        assert any(f["factor"] == "already_recovered" for f in result.factors)
    
    def test_probability_bounded(self):
        """Test that probability is always bounded between 0 and 1."""
        features = FeatureSet(
            payment_amount=10000,
            currency="INR",
            payment_status="FAILED",
            retry_count=10,  # Very high retry count
            time_since_failure_hours=1000,  # Very old
            previous_successful_recovery=True,
            previous_failed_recovery=True,
            created_at=datetime.utcnow(),
        )
        
        result = self.engine.calculate(features, FailureCategory.UNKNOWN)
        
        assert 0.0 <= result.probability <= 1.0


class TestOpportunityScorer:
    """Tests for OpportunityScorer."""
    
    def setup_method(self):
        self.scorer = OpportunityScorer()
    
    def test_score_high_value_high_probability(self):
        """Test scoring for high-value, high-probability opportunity."""
        features = FeatureSet(
            payment_amount=50000,
            currency="INR",
            payment_status="FAILED",
            retry_count=1,
            time_since_failure_hours=2,
            created_at=datetime.utcnow(),
        )
        
        recovery_prob = type('obj', (object,), {
            'probability': 0.75,
            'factors': []
        })()
        
        result = self.scorer.score(features, recovery_prob, 37500)
        
        assert 0.0 <= result.score <= 100.0
        assert result.priority in PriorityLevel
    
    def test_score_low_value_low_probability(self):
        """Test scoring for low-value, low-probability opportunity."""
        features = FeatureSet(
            payment_amount=500,  # Low value
            currency="INR",
            payment_status="FAILED",
            retry_count=3,
            time_since_failure_hours=48,
            created_at=datetime.utcnow(),
        )
        
        recovery_prob = type('obj', (object,), {
            'probability': 0.30,
            'factors': []
        })()
        
        result = self.scorer.score(features, recovery_prob, 150)
        
        assert result.score < 50  # Should be low score
        assert result.priority in [PriorityLevel.LOW, PriorityLevel.MEDIUM]
    
    def test_score_critical_priority(self):
        """Test that high merchant-relative value with good probability gets critical priority."""
        features = FeatureSet(
            payment_amount=60000,
            currency="INR",
            payment_status="FAILED",
            retry_count=1,
            time_since_failure_hours=2,
            created_at=datetime.utcnow(),
            transaction_value_percentile=0.95,  # Top 5% for merchant
            normalized_value_score=0.9,
        )
        
        recovery_prob = type('obj', (object,), {
            'probability': 0.70,
            'factors': []
        })()
        
        result = self.scorer.score(features, recovery_prob, 42000)
        
        assert result.priority == PriorityLevel.CRITICAL
    
    def test_score_aged_failure_penalty(self):
        """Test that aged failures get score penalty."""
        features = FeatureSet(
            payment_amount=10000,
            currency="INR",
            payment_status="FAILED",
            retry_count=1,
            time_since_failure_hours=200,  # Over 7 days
            created_at=datetime.utcnow(),
        )
        
        recovery_prob = type('obj', (object,), {
            'probability': 0.50,
            'factors': []
        })()
        
        result = self.scorer.score(features, recovery_prob, 5000)
        
        assert "aged" in result.explanation.lower() or "old" in result.explanation.lower()


class TestInterventionRecommendationEngine:
    """Tests for InterventionRecommendationEngine."""
    
    def setup_method(self):
        self.engine = InterventionRecommendationEngine()
    
    def test_recommend_temporary_failure(self):
        """Test recommendation for temporary failure."""
        features = FeatureSet(
            payment_amount=10000,
            currency="INR",
            payment_status="FAILED",
            retry_count=1,
            created_at=datetime.utcnow(),
        )
        
        result = self.engine.recommend(
            features,
            FailureCategory.TEMPORARY_FAILURE,
            PriorityLevel.HIGH,
            0.75
        )
        
        assert "RETRY" in result.recommended_action.upper()
        assert result.confidence > 0.7
    
    def test_recommend_insufficient_funds(self):
        """Test recommendation for insufficient funds."""
        features = FeatureSet(
            payment_amount=10000,
            currency="INR",
            payment_status="FAILED",
            retry_count=1,
            created_at=datetime.utcnow(),
        )
        
        result = self.engine.recommend(
            features,
            FailureCategory.INSUFFICIENT_FUNDS,
            PriorityLevel.MEDIUM,
            0.50
        )
        
        assert "ALTERNATE" in result.recommended_action.upper() or "METHOD" in result.recommended_action.upper()
    
    def test_recommend_authentication_failure(self):
        """Test recommendation for authentication failure."""
        features = FeatureSet(
            payment_amount=10000,
            currency="INR",
            payment_status="FAILED",
            retry_count=1,
            created_at=datetime.utcnow(),
        )
        
        result = self.engine.recommend(
            features,
            FailureCategory.AUTHENTICATION_FAILURE,
            PriorityLevel.MEDIUM,
            0.60
        )
        
        assert "AUTH" in result.recommended_action.upper()
    
    def test_recommend_high_relative_value_critical(self):
        """Test recommendation for high relative value critical case."""
        features = FeatureSet(
            payment_amount=60000,
            currency="INR",
            payment_status="FAILED",
            retry_count=1,
            created_at=datetime.utcnow(),
            normalized_value_score=0.9,  # High relative value
        )
        
        result = self.engine.recommend(
            features,
            FailureCategory.TEMPORARY_FAILURE,
            PriorityLevel.CRITICAL,
            0.75
        )
        
        assert "MANUAL" in result.recommended_action.upper() or "PRIORITIZE" in result.recommended_action.upper()
    
    def test_recommend_multiple_retries(self):
        """Test recommendation after multiple retries."""
        features = FeatureSet(
            payment_amount=10000,
            currency="INR",
            payment_status="FAILED",
            retry_count=3,
            created_at=datetime.utcnow(),
        )
        
        result = self.engine.recommend(
            features,
            FailureCategory.INSUFFICIENT_FUNDS,
            PriorityLevel.MEDIUM,
            0.40
        )
        
        # After multiple retries, should recommend alternate method or manual review
        assert "ALTERNATE" in result.recommended_action.upper() or "MANUAL" in result.recommended_action.upper()
    
    def test_recommend_low_probability(self):
        """Test recommendation for low recovery probability."""
        features = FeatureSet(
            payment_amount=10000,
            currency="INR",
            payment_status="FAILED",
            retry_count=1,
            created_at=datetime.utcnow(),
        )
        
        result = self.engine.recommend(
            features,
            FailureCategory.UNKNOWN,
            PriorityLevel.LOW,
            0.20
        )
        
        assert "MANUAL" in result.recommended_action.upper()
    
    def test_recommend_unknown_failure(self):
        """Test recommendation for unknown failure."""
        features = FeatureSet(
            payment_amount=10000,
            currency="INR",
            payment_status="FAILED",
            retry_count=1,
            created_at=datetime.utcnow(),
        )
        
        result = self.engine.recommend(
            features,
            FailureCategory.UNKNOWN,
            PriorityLevel.LOW,
            0.25
        )
        
        assert "MANUAL" in result.recommended_action.upper()
