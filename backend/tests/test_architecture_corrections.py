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
import uuid
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
    db_session = SessionLocal()
    try:
        yield db_session
    finally:
        db_session.rollback()
        db_session.close()


class TestMerchantRelativeValue:
    """Tests for merchant-relative transaction value logic."""
    
    def test_500_not_universally_high_value(self, db: Session):
        """Test that ₹500 is not universally high-value across merchants."""
        unique_suffix = uuid.uuid4().hex[:8]
        # Create small merchant (avg transaction ~₹100)
        small_merchant = Merchant(
            name=f"Small Merchant {unique_suffix}",
            external_id=f"small_merchant_{unique_suffix}",
            currency="INR"
        )
        db.add(small_merchant)
        db.flush()
        
        # Add small transactions to establish baseline
        for i in range(10):
            payment = Payment(
                razorpay_payment_id=f"pay_small_{unique_suffix}_{i}",
                razorpay_order_id=f"order_small_{unique_suffix}_{i}",
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
            name=f"Large Merchant {unique_suffix}",
            external_id=f"large_merchant_{unique_suffix}",
            currency="INR"
        )
        db.add(large_merchant)
        db.flush()
        
        # Add large transactions to establish baseline
        for i in range(10):
            payment = Payment(
                razorpay_payment_id=f"pay_large_{unique_suffix}_{i}",
                razorpay_order_id=f"order_large_{unique_suffix}_{i}",
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
            razorpay_payment_id=f"pay_test_small_{unique_suffix}",
            razorpay_order_id=f"order_test_small_{unique_suffix}",
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
            razorpay_payment_id=f"pay_test_large_{unique_suffix}",
            razorpay_order_id=f"order_test_large_{unique_suffix}",
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
        unique_suffix = uuid.uuid4().hex[:8]
        merchant = Merchant(
            name=f"Test Merchant {unique_suffix}",
            external_id=f"test_merchant_percentile_{unique_suffix}",
            currency="INR"
        )
        db.add(merchant)
        db.flush()
        
        # Create transactions with known distribution
        amounts = [1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000]
        for i, amount in enumerate(amounts):
            payment = Payment(
                razorpay_payment_id=f"pay_{unique_suffix}_{i}",
                razorpay_order_id=f"order_{unique_suffix}_{i}",
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
            razorpay_payment_id=f"pay_test_median_{unique_suffix}",
            razorpay_order_id=f"order_test_median_{unique_suffix}",
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
        
        # Percentile should be around 0.5 (middle of distribution)
        assert 0.4 <= features.transaction_value_percentile <= 0.6


class TestBoundedScoring:
    """Tests for bounded scoring behavior."""
    
    def test_extremely_large_transaction_not_automatic_100(self, db: Session):
        """Test that a huge transaction does NOT automatically get score 100."""
        unique_suffix = uuid.uuid4().hex[:8]
        merchant = Merchant(
            name=f"Test Merchant {unique_suffix}",
            external_id=f"test_merchant_bounded_{unique_suffix}",
            currency="INR"
        )
        db.add(merchant)
        db.flush()
        
        # Add normal baseline
        for i in range(10):
            payment = Payment(
                razorpay_payment_id=f"pay_{unique_suffix}_{i}",
                razorpay_order_id=f"order_{unique_suffix}_{i}",
                merchant_id=merchant.id,
                amount_minor=100000,  # ₹1,000
                currency="INR",
                status=PaymentStatus.CAPTURED,
                created_at=datetime.utcnow(),
            )
            db.add(payment)
        db.commit()
        
        extractor = FeatureExtractor(db)
        
        # Test massive payment (₹10,00,000) with permanent failure
        huge_payment = Payment(
            razorpay_payment_id=f"pay_huge_{unique_suffix}",
            razorpay_order_id=f"order_huge_{unique_suffix}",
            merchant_id=merchant.id,
            amount_minor=100000000,  # ₹10,00,000
            currency="INR",
            status=PaymentStatus.FAILED,
            method="card",
            failure_code="BAD_REQUEST_ERROR",
            failure_description="Card expired",  # Permanent failure
            created_at=datetime.utcnow(),
        )
        db.add(huge_payment)
        db.commit()
        db.refresh(huge_payment)
        
        features = extractor.extract_features(huge_payment)
        
        # Probability engine should give low likelihood due to payment method failure
        prob_engine = RecoveryProbabilityEngine()
        prob_result = prob_engine.calculate(
            features=features,
            failure_category=FailureCategory.PAYMENT_METHOD_FAILURE
        )
        
        # Score should NOT be 100 despite massive amount
        scorer = OpportunityScorer()
        score_result = scorer.score(
            features=features,
            recovery_probability=prob_result,
            revenue_at_risk=huge_payment.amount_minor
        )
        
        # Score must be bounded and not 100 despite large amount
        assert score_result.score < 100
        assert score_result.score >= 0
    
    def test_score_remains_bounded_0_to_100(self):
        """Test that opportunity scores always stay between 0 and 100."""
        scorer = OpportunityScorer()
        
        # Test extreme combinations
        extreme_cases = [
            (0.0, 0.0),      # Minimum everything
            (1.0, 1.0),      # Maximum everything
            (0.0, 1.0),      # Low value, high probability
            (1.0, 0.0),      # High value, low probability
            (0.5, 0.5),      # Balanced
        ]
        
        for norm_val, prob in extreme_cases:
            features = FeatureSet(
                payment_amount=100000,
                currency="INR",
                payment_status="FAILED",
                normalized_value_score=norm_val,
                transaction_value_percentile=norm_val,
                merchant_avg_transaction_value=50000,
                retry_count=0,
                failure_code="TEST",
                failure_message="Test",
                payment_method="card",
                created_at=datetime.utcnow(),
            )
            
            prob_result = RecoveryProbability(
                probability=prob,
                factors=[],
            )
            
            score_result = scorer.score(
                features=features,
                recovery_probability=prob_result,
                revenue_at_risk=100000
            )
            
            assert 0 <= score_result.score <= 100
    
    def test_probability_remains_bounded_0_to_1(self):
        """Test that probability always stays between 0 and 1."""
        prob_engine = RecoveryProbabilityEngine()
        
        for category in FailureCategory:
            for retry_count in range(0, 10):
                features = FeatureSet(
                    payment_amount=100000,
                    currency="INR",
                    payment_status="FAILED",
                    normalized_value_score=0.5,
                    transaction_value_percentile=0.5,
                    merchant_avg_transaction_value=50000,
                    retry_count=retry_count,
                    failure_code="TEST",
                    failure_message="Test",
                    payment_method="upi",
                    created_at=datetime.utcnow(),
                )
                
                result = prob_engine.calculate(
                    features=features,
                    failure_category=category
                )
                
                assert 0.0 <= result.probability <= 1.0


class TestSmallVsLargeMerchantBehavior:
    """Tests that same transaction value produces different scores for different merchant sizes."""
    
    def test_small_and_large_merchant_different_scoring(self, db: Session):
        """Test that a ₹5,000 transaction scores differently for small vs large merchants."""
        unique_suffix = uuid.uuid4().hex[:8]
        # Small merchant (avg ₹500)
        small_merchant = Merchant(
            name=f"Small Merchant {unique_suffix}",
            external_id=f"small_mer_{unique_suffix}",
            currency="INR"
        )
        db.add(small_merchant)
        db.flush()
        
        for i in range(10):
            db.add(Payment(
                razorpay_payment_id=f"pay_s_{unique_suffix}_{i}",
                razorpay_order_id=f"order_s_{unique_suffix}_{i}",
                merchant_id=small_merchant.id,
                amount_minor=50000,  # ₹500
                currency="INR",
                status=PaymentStatus.CAPTURED,
                created_at=datetime.utcnow(),
            ))
        
        # Large merchant (avg ₹50,000)
        large_merchant = Merchant(
            name=f"Large Merchant {unique_suffix}",
            external_id=f"large_mer_{unique_suffix}",
            currency="INR"
        )
        db.add(large_merchant)
        db.flush()
        
        for i in range(10):
            db.add(Payment(
                razorpay_payment_id=f"pay_l_{unique_suffix}_{i}",
                razorpay_order_id=f"order_l_{unique_suffix}_{i}",
                merchant_id=large_merchant.id,
                amount_minor=5000000,  # ₹50,000
                currency="INR",
                status=PaymentStatus.CAPTURED,
                created_at=datetime.utcnow(),
            ))
        db.commit()
        
        # Test ₹5,000 payment on both
        service = IntelligenceService(db)
        
        small_payment = Payment(
            razorpay_payment_id=f"pay_test_s_{unique_suffix}",
            razorpay_order_id=f"order_test_s_{unique_suffix}",
            merchant_id=small_merchant.id,
            amount_minor=500000,  # ₹5,000
            currency="INR",
            status=PaymentStatus.FAILED,
            method="upi",
            failure_code="BANK_ERROR",
            failure_description="Bank error",
            created_at=datetime.utcnow(),
        )
        db.add(small_payment)
        
        large_payment = Payment(
            razorpay_payment_id=f"pay_test_l_{unique_suffix}",
            razorpay_order_id=f"order_test_l_{unique_suffix}",
            merchant_id=large_merchant.id,
            amount_minor=500000,  # ₹5,000
            currency="INR",
            status=PaymentStatus.FAILED,
            method="upi",
            failure_code="BANK_ERROR",
            failure_description="Bank error",
            created_at=datetime.utcnow(),
        )
        db.add(large_payment)
        db.commit()
        
        result_small = service.analyze_payment(small_payment)
        result_large = service.analyze_payment(large_payment)
        
        # For small merchant, ₹5,000 is 10x average -> high score
        # For large merchant, ₹5,000 is 0.1x average -> lower score
        assert result_small.opportunity_score > result_large.opportunity_score


class TestExplainabilityFactors:
    """Tests that explainability factors are always produced."""
    
    def test_score_factors_exposed(self, db: Session):
        """Test that score explanation factors are always populated."""
        unique_suffix = uuid.uuid4().hex[:8]
        merchant = Merchant(
            name=f"Factor Test Merchant {unique_suffix}",
            external_id=f"factor_test_merchant_{unique_suffix}",
            currency="INR"
        )
        db.add(merchant)
        db.flush()
        
        payment = Payment(
            razorpay_payment_id=f"pay_factor_test_{unique_suffix}",
            razorpay_order_id=f"order_factor_test_{unique_suffix}",
            merchant_id=merchant.id,
            amount_minor=100000,
            currency="INR",
            status=PaymentStatus.FAILED,
            method="card",
            failure_code="BANK_ERROR",
            failure_description="Bank error",
            created_at=datetime.utcnow(),
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)
        
        service = IntelligenceService(db)
        result = service.analyze_payment(payment)
        
        assert len(result.factors) > 0
        for factor in result.factors:
            assert factor.get("name") is not None
            assert factor.get("impact") is not None
            assert factor.get("explanation") is not None


class TestDeterministicFallback:
    """Tests for deterministic fallback when history is missing."""
    
    def test_no_merchant_history_fallback(self, db: Session):
        """Test fallback behavior when merchant has no prior transaction history."""
        unique_suffix = uuid.uuid4().hex[:8]
        merchant = Merchant(
            name=f"Brand New Merchant {unique_suffix}",
            external_id=f"brand_new_merchant_{unique_suffix}",
            currency="INR"
        )
        db.add(merchant)
        db.flush()
        
        payment = Payment(
            razorpay_payment_id=f"pay_new_merchant_{unique_suffix}",
            razorpay_order_id=f"order_new_merchant_{unique_suffix}",
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
        """Test fallback behavior when merchant is unknown in-memory."""
        payment = Payment(
            amount_minor=50000,
            currency="INR",
            status=PaymentStatus.FAILED,
            merchant_id=None,
        )
        
        extractor = FeatureExtractor(db)
        features = extractor.extract_features(payment)
        
        # Should use neutral fallback values
        assert features.transaction_value_percentile == 0.5
        assert features.normalized_value_score == 0.5
