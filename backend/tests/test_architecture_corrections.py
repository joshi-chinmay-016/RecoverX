"""Tests for Phase 2 architecture corrections.

Tests verify:
- ₹500 is not universally high-value
- merchant-relative transaction values work
- extremely large transactions do not automatically receive score 100
- small merchants and large merchants behave differently
- scores remain between 0 and 100
- probability/likelihood remains between 0 and 1
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models.merchant import Merchant
from app.db.models.customer import Customer
from app.db.models.payment import Payment
from app.db.models.payment_attempt import PaymentAttempt
from app.db.models.recovery_case import RecoveryCase
from app.db.base import PaymentStatus, RecoveryCaseStatus
from app.intelligence.feature_extractor import FeatureExtractor
from app.intelligence.probability_engine import RecoveryProbabilityEngine
from app.intelligence.opportunity_scorer import OpportunityScorer
from app.intelligence.intelligence_service import IntelligenceService
from app.intelligence.schemas import (
    FeatureSet,
    FailureCategory,
    PriorityLevel,
    RecoveryProbability,
)


@pytest.fixture
def db():
    """Database session fixture."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


class TestMerchantRelativeValue:
    """Tests for merchant-relative transaction value logic."""
    
    def test_500_not_universally_high_value(self, db: Session):
        """Test that ₹500 is not universally high-value across merchants."""
        # Create small merchant (avg transaction ~₹100)
        small_merchant = Merchant(
            name="Small Merchant",
            external_id="small_merchant",
            currency="INR"
        )
        db.add(small_merchant)
        db.flush()
        
        # Add small transactions to establish baseline
        for i in range(10):
            payment = Payment(
                razorpay_payment_id=f"pay_small_{i}",
                razorpay_order_id=f"order_small_{i}",
                merchant_id=small_merchant.id,
                amount_minor=10000,  # ₹100
                currency="INR",
                status=PaymentStatus.CAPTURED,
                created_at=datetime.utcnow(),
            )
            db.add(payment)
        db.commit()
        
        # Create large merchant (avg transaction ~₹50,000)
        large_merchant = Merchant(
            name="Large Merchant",
            external_id="large_merchant",
            currency="INR"
        )
        db.add(large_merchant)
        db.flush()
        
        # Add large transactions to establish baseline
        for i in range(10):
            payment = Payment(
                razorpay_payment_id=f"pay_large_{i}",
                razorpay_order_id=f"order_large_{i}",
                merchant_id=large_merchant.id,
                amount_minor=5000000,  # ₹50,000
                currency="INR",
                status=PaymentStatus.CAPTURED,
                created_at=datetime.utcnow(),
            )
            db.add(payment)
        db.commit()
        
        extractor = FeatureExtractor(db)
        
        # Test ₹500 transaction for small merchant (should be high relative value)
        small_payment = Payment(
            razorpay_payment_id="pay_test_small",
            razorpay_order_id="order_test_small",
            merchant_id=small_merchant.id,
            amount_minor=50000,  # ₹500
            currency="INR",
            status=PaymentStatus.FAILED,
            created_at=datetime.utcnow(),
        )
        db.add(small_payment)
        db.commit()
        db.refresh(small_payment)
        
        features_small = extractor.extract_features(small_payment)
        
        # For small merchant, ₹500 should be high relative value
        assert features_small.normalized_value_score > 0.7
        assert features_small.transaction_value_percentile > 0.8
        
        # Test ₹500 transaction for large merchant (should be low relative value)
        large_payment = Payment(
            razorpay_payment_id="pay_test_large",
            razorpay_order_id="order_test_large",
            merchant_id=large_merchant.id,
            amount_minor=50000,  # ₹500
            currency="INR",
            status=PaymentStatus.FAILED,
            created_at=datetime.utcnow(),
        )
        db.add(large_payment)
        db.commit()
        db.refresh(large_payment)
        
        features_large = extractor.extract_features(large_payment)
        
        # For large merchant, ₹500 should be low relative value
        assert features_large.normalized_value_score < 0.3
        assert features_large.transaction_value_percentile < 0.2
    
    def test_merchant_relative_percentile_calculation(self, db: Session):
        """Test that percentile calculation is merchant-relative."""
        merchant = Merchant(
            name="Test Merchant",
            external_id="test_merchant_percentile",
            currency="INR"
        )
        db.add(merchant)
        db.flush()
        
        # Create transactions with known distribution
        amounts = [1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000]
        for i, amount in enumerate(amounts):
            payment = Payment(
                razorpay_payment_id=f"pay_{i}",
                razorpay_order_id=f"order_{i}",
                merchant_id=merchant.id,
                amount_minor=amount,
                currency="INR",
                status=PaymentStatus.CAPTURED,
                created_at=datetime.utcnow(),
            )
            db.add(payment)
        db.commit()
        
        extractor = FeatureExtractor(db)
        
        # Test payment at median (₹5000)
        test_payment = Payment(
            razorpay_payment_id="pay_test_median",
            razorpay_order_id="order_test_median",
            merchant_id=merchant.id,
            amount_minor=5000,
            currency="INR",
            status=PaymentStatus.FAILED,
            created_at=datetime.utcnow(),
        )
        db.add(test_payment)
        db.commit()
        db.refresh(test_payment)
        
        features = extractor.extract_features(test_payment)
        
        # Should be around median percentile
        assert 0.4 <= features.transaction_value_percentile <= 0.6
        
        # Test payment at maximum (₹10000)
        test_payment_max = Payment(
            razorpay_payment_id="pay_test_max",
            razorpay_order_id="order_test_max",
            merchant_id=merchant.id,
            amount_minor=10000,
            currency="INR",
            status=PaymentStatus.FAILED,
            created_at=datetime.utcnow(),
        )
        db.add(test_payment_max)
        db.commit()
        db.refresh(test_payment_max)
        
        features_max = extractor.extract_features(test_payment_max)
        
        # Should be at or near 100th percentile
        assert features_max.transaction_value_percentile >= 0.9


class TestBoundedScoring:
    """Tests for bounded scoring logic."""
    
    def test_extremely_large_transaction_not_automatic_100(self, db: Session):
        """Test that extremely large transactions don't automatically get score 100."""
        merchant = Merchant(
            name="Test Merchant",
            external_id="test_merchant_large",
            currency="INR"
        )
        db.add(merchant)
        db.flush()
        
        # Create average transactions
        for i in range(10):
            payment = Payment(
                razorpay_payment_id=f"pay_avg_{i}",
                razorpay_order_id=f"order_avg_{i}",
                merchant_id=merchant.id,
                amount_minor=10000,  # ₹100 average
                currency="INR",
                status=PaymentStatus.CAPTURED,
                created_at=datetime.utcnow(),
            )
            db.add(payment)
        db.commit()
        
        # Create extremely large failed payment (₹1,000,000)
        large_payment = Payment(
            razorpay_payment_id="pay_large_extreme",
            razorpay_order_id="order_large_extreme",
            merchant_id=merchant.id,
            amount_minor=100000000,  # ₹1,000,000
            currency="INR",
            status=PaymentStatus.FAILED,
            failure_code="UNKNOWN_ERROR",
            failure_description="Unknown error",
            created_at=datetime.utcnow(),
        )
        db.add(large_payment)
        db.commit()
        db.refresh(large_payment)
        
        extractor = FeatureExtractor(db)
        features = extractor.extract_features(large_payment)
        
        # Even with extreme value, normalized score should be bounded
        assert features.normalized_value_score <= 1.0
        
        # With low recovery probability (unknown failure), score should not be 100
        prob_engine = RecoveryProbabilityEngine()
        recovery_prob = prob_engine.calculate(features, FailureCategory.UNKNOWN)
        
        scorer = OpportunityScorer()
        opportunity_score = scorer.score(features, recovery_prob, 0)
        
        # Score should be bounded and not automatically 100 due to amount alone
        assert opportunity_score.score < 100.0
        assert opportunity_score.score >= 0.0
    
    def test_score_remains_bounded_0_to_100(self):
        """Test that scores always remain between 0 and 100."""
        scorer = OpportunityScorer()
        
        # Test with extreme values
        test_cases = [
            # (normalized_value, probability, retry_count, time_hours)
            (1.0, 1.0, 0, 1),  # Maximum positive factors
            (0.0, 0.0, 10, 1000),  # Maximum negative factors
            (0.5, 0.5, 5, 100),  # Neutral factors
        ]
        
        for norm_value, prob, retry_count, time_hours in test_cases:
            features = FeatureSet(
                payment_amount=10000,
                currency="INR",
                payment_status="FAILED",
                retry_count=retry_count,
                time_since_failure_hours=time_hours,
                created_at=datetime.utcnow(),
                normalized_value_score=norm_value,
                transaction_value_percentile=norm_value,
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
        ]
        
        for features in test_cases:
            result = engine.calculate(features, FailureCategory.TEMPORARY_FAILURE)
            assert 0.0 <= result.probability <= 1.0


class TestSmallVsLargeMerchantBehavior:
    """Tests for different behavior between small and large merchants."""
    
    def test_small_and_large_merchant_different_scoring(self, db: Session):
        """Test that small and large merchants behave differently for same amount."""
        # Small merchant (avg ~₹100)
        small_merchant = Merchant(
            name="Small Merchant",
            external_id="small_merchant_behavior",
            currency="INR"
        )
        db.add(small_merchant)
        db.flush()
        
        for i in range(10):
            payment = Payment(
                razorpay_payment_id=f"pay_small_{i}",
                razorpay_order_id=f"order_small_{i}",
                merchant_id=small_merchant.id,
                amount_minor=10000,
                currency="INR",
                status=PaymentStatus.CAPTURED,
                created_at=datetime.utcnow(),
            )
            db.add(payment)
        db.commit()
        
        # Large merchant (avg ~₹100,000)
        large_merchant = Merchant(
            name="Large Merchant",
            external_id="large_merchant_behavior",
            currency="INR"
        )
        db.add(large_merchant)
        db.flush()
        
        for i in range(10):
            payment = Payment(
                razorpay_payment_id=f"pay_large_{i}",
                razorpay_order_id=f"order_large_{i}",
                merchant_id=large_merchant.id,
                amount_minor=10000000,
                currency="INR",
                status=PaymentStatus.CAPTURED,
                created_at=datetime.utcnow(),
            )
            db.add(payment)
        db.commit()
        
        extractor = FeatureExtractor(db)
        scorer = OpportunityScorer()
        prob_engine = RecoveryProbabilityEngine()
        
        # Same ₹1000 transaction for both merchants
        amount = 100000  # ₹1000
        
        small_payment = Payment(
            razorpay_payment_id="pay_test_small_behavior",
            razorpay_order_id="order_test_small_behavior",
            merchant_id=small_merchant.id,
            amount_minor=amount,
            currency="INR",
            status=PaymentStatus.FAILED,
            failure_code="TEMPORARY_ERROR",
            failure_description="Temporary error",
            created_at=datetime.utcnow(),
        )
        db.add(small_payment)
        db.commit()
        db.refresh(small_payment)
        
        large_payment = Payment(
            razorpay_payment_id="pay_test_large_behavior",
            razorpay_order_id="order_test_large_behavior",
            merchant_id=large_merchant.id,
            amount_minor=amount,
            currency="INR",
            status=PaymentStatus.FAILED,
            failure_code="TEMPORARY_ERROR",
            failure_description="Temporary error",
            created_at=datetime.utcnow(),
        )
        db.add(large_payment)
        db.commit()
        db.refresh(large_payment)
        
        features_small = extractor.extract_features(small_payment)
        features_large = extractor.extract_features(large_payment)
        
        # Small merchant should see this as high relative value
        assert features_small.normalized_value_score > features_large.normalized_value_score
        
        # Calculate scores
        prob_small = prob_engine.calculate(features_small, FailureCategory.TEMPORARY_FAILURE)
        prob_large = prob_engine.calculate(features_large, FailureCategory.TEMPORARY_FAILURE)
        
        score_small = scorer.score(features_small, prob_small, 0)
        score_large = scorer.score(features_large, prob_large, 0)
        
        # Small merchant should get higher score for same amount
        assert score_small.score > score_large.score


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
        assert len(score.score_factors) > 0
        
        # Each factor should have required fields
        for factor in score.score_factors:
            assert "name" in factor
            assert "impact" in factor
            assert "explanation" in factor
        
        # Check for expected factor names
        factor_names = [f["name"] for f in score.score_factors]
        assert "transaction_value" in factor_names
        assert "recovery_likelihood" in factor_names


class TestDeterministicFallback:
    """Tests for deterministic fallback behavior."""
    
    def test_no_merchant_history_fallback(self, db: Session):
        """Test fallback behavior when merchant has no history."""
        merchant = Merchant(
            name="New Merchant",
            external_id="new_merchant",
            currency="INR"
        )
        db.add(merchant)
        db.flush()
        
        payment = Payment(
            razorpay_payment_id="pay_new_merchant",
            razorpay_order_id="order_new_merchant",
            merchant_id=merchant.id,
            amount_minor=50000,
            currency="INR",
            status=PaymentStatus.FAILED,
            created_at=datetime.utcnow(),
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)
        
        extractor = FeatureExtractor(db)
        features = extractor.extract_features(payment)
        
        # Should use neutral fallback values
        assert features.transaction_value_percentile == 0.5
        assert features.normalized_value_score == 0.5
        assert features.merchant_avg_transaction_value == 0
    
    def test_unknown_merchant_fallback(self, db: Session):
        """Test fallback behavior when merchant is unknown."""
        payment = Payment(
            razorpay_payment_id="pay_unknown_merchant",
            razorpay_order_id="order_unknown_merchant",
            merchant_id=None,  # No merchant
            amount_minor=50000,
            currency="INR",
            status=PaymentStatus.FAILED,
            created_at=datetime.utcnow(),
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)
        
        extractor = FeatureExtractor(db)
        features = extractor.extract_features(payment)
        
        # Should use neutral fallback values
        assert features.transaction_value_percentile == 0.5
        assert features.normalized_value_score == 0.5
