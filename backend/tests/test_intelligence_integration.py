"""Integration tests for Revenue Intelligence system."""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models.merchant import Merchant
from app.db.models.customer import Customer
from app.db.models.payment import Payment
from app.db.models.payment_attempt import PaymentAttempt
from app.db.models.recovery_case import RecoveryCase
from app.db.models.revenue_intelligence import RevenueIntelligenceResult
from app.db.base import PaymentStatus, RecoveryCaseStatus
from app.intelligence.intelligence_service import IntelligenceService
from app.intelligence.schemas import PriorityLevel, FailureCategory


@pytest.fixture
def db():
    """Database session fixture."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


import uuid
from app.auth.dependencies import TenantContext


@pytest.fixture
def sample_payment(db: Session, sample_tenant: TenantContext):
    """Create a sample payment for testing bound to sample_tenant."""
    merchant = sample_tenant.merchant
    unique_suffix = uuid.uuid4().hex[:8]
    
    # Create customer
    customer = Customer(
        external_customer_id=f"test_customer_{unique_suffix}",
        email=f"test_{unique_suffix}@example.com"
    )
    db.add(customer)
    db.flush()
    
    # Create payment
    payment = Payment(
        razorpay_payment_id=f"pay_test_{unique_suffix}",
        razorpay_order_id=f"order_test_{unique_suffix}",
        merchant_id=merchant.id,
        customer_id=customer.id,
        amount_minor=25000,  # ₹250
        currency="INR",
        status=PaymentStatus.FAILED,
        method="upi",
        failure_code="BANK_ERROR",
        failure_description="Bank processing error",
        created_at=datetime.utcnow() - timedelta(hours=2),
    )
    db.add(payment)
    db.flush()
    
    # Create payment attempt
    attempt = PaymentAttempt(
        payment_id=payment.id,
        attempt_number=1,
        status=PaymentStatus.FAILED,
        failure_code="BANK_ERROR",
        failure_description="Bank processing error",
        method="upi",
        started_at=datetime.utcnow() - timedelta(hours=2),
        completed_at=datetime.utcnow() - timedelta(hours=2, minutes=1),
    )
    db.add(attempt)
    
    # Create recovery case
    recovery_case = RecoveryCase(
        payment_id=payment.id,
        status=RecoveryCaseStatus.OPEN,
        amount_at_risk_minor=payment.amount_minor
    )
    db.add(recovery_case)
    
    db.commit()
    db.refresh(payment)
    
    return payment


class TestIntelligenceServiceIntegration:
    """Integration tests for IntelligenceService."""
    
    def test_analyze_payment_creates_intelligence_result(self, db: Session, sample_payment: Payment):
        """Test that analyzing a payment creates an intelligence result."""
        service = IntelligenceService(db)
        
        # Analyze payment
        result = service.analyze_payment(sample_payment)
        
        # Verify result was created
        assert result is not None
        assert result.payment_id == str(sample_payment.id)
        assert result.failure_category in FailureCategory
        assert 0.0 <= result.recovery_probability <= 1.0
        assert result.opportunity_score >= 0.0
        assert result.priority in PriorityLevel
        assert result.recommended_intervention is not None
        assert result.model_version == "rules-v1"
        
        # Verify it was persisted
        db_result = db.query(RevenueIntelligenceResult).filter(
            RevenueIntelligenceResult.payment_id == sample_payment.id
        ).first()
        assert db_result is not None
    
    def test_analyze_payment_idempotent(self, db: Session, sample_payment: Payment):
        """Test that analyzing the same payment twice is idempotent."""
        service = IntelligenceService(db)
        
        # First analysis
        result1 = service.analyze_payment(sample_payment)
        result1_id = result1.id
        
        # Second analysis without force
        result2 = service.analyze_payment(sample_payment, force_reanalyze=False)
        
        # Should return the same result
        assert result2.id == result1_id
        assert result2.payment_id == result1.payment_id
    
    def test_analyze_payment_force_reanalyze(self, db: Session, sample_payment: Payment):
        """Test that force_reanalyze updates the result."""
        service = IntelligenceService(db)
        
        # First analysis
        result1 = service.analyze_payment(sample_payment)
        
        # Update payment to change the analysis
        sample_payment.amount_minor = 50000
        sample_payment.failure_code = "NETWORK_ERROR"
        db.commit()
        
        # Force re-analysis
        result2 = service.analyze_payment(sample_payment, force_reanalyze=True)
        
        # Should have updated values
        assert result2.id == result1.id  # Same record
        assert result2.updated_at > result1.updated_at
    
    def test_get_intelligence_by_payment(self, db: Session, sample_payment: Payment):
        """Test getting intelligence result by payment ID."""
        service = IntelligenceService(db)
        
        # Analyze payment
        service.analyze_payment(sample_payment)
        
        # Get by payment ID
        result = service.get_intelligence_by_payment(str(sample_payment.id))
        
        assert result is not None
        assert result.payment_id == str(sample_payment.id)
    
    def test_list_opportunities_without_filters(self, db: Session, sample_payment: Payment):
        """Test listing opportunities without filters."""
        service = IntelligenceService(db)
        
        # Analyze payment
        service.analyze_payment(sample_payment)
        
        # List opportunities
        result = service.list_opportunities(page=1, page_size=20)
        
        assert result.total >= 1
        assert len(result.opportunities) >= 1
        assert result.page == 1
        assert result.page_size == 20
    
    def test_list_opportunities_with_priority_filter(self, db: Session, sample_payment: Payment):
        """Test listing opportunities with priority filter."""
        service = IntelligenceService(db)
        
        # Analyze payment
        service.analyze_payment(sample_payment)
        
        # Get the priority of the created result
        result = service.get_intelligence_by_payment(str(sample_payment.id))
        priority = result.priority
        
        # List with priority filter
        filtered_result = service.list_opportunities(
            priority=priority,
            page=1,
            page_size=20
        )
        
        # All results should have the specified priority
        for opp in filtered_result.opportunities:
            assert opp.priority == priority
    
    def test_get_overview(self, db: Session, sample_payment: Payment):
        """Test getting intelligence overview."""
        service = IntelligenceService(db)
        
        # Analyze payment
        service.analyze_payment(sample_payment)
        
        # Get overview
        overview = service.get_overview()
        
        assert overview.total_revenue >= 0
        assert overview.failed_revenue >= 0
        assert overview.revenue_at_risk >= 0
        assert overview.estimated_recoverable_revenue >= 0
        assert overview.recovery_opportunity_count >= 1
        assert overview.high_priority_opportunities >= 0
        assert isinstance(overview.failure_distribution, dict)
        assert isinstance(overview.top_failure_reasons, list)
        assert isinstance(overview.priority_distribution, dict)
    
    def test_analyze_payment_without_recovery_case(self, db: Session):
        """Test analyzing a payment that doesn't have a recovery case."""
        unique_suffix = uuid.uuid4().hex[:8]
        # Create merchant
        merchant = Merchant(
            name=f"Test Merchant {unique_suffix}",
            external_id=f"test_merchant_{unique_suffix}",
            currency="INR"
        )
        db.add(merchant)
        db.flush()
        
        # Create payment without recovery case
        payment = Payment(
            razorpay_payment_id=f"pay_test_{unique_suffix}",
            razorpay_order_id=f"order_test_{unique_suffix}",
            merchant_id=merchant.id,
            amount_minor=10000,
            currency="INR",
            status=PaymentStatus.FAILED,
            method="card",
            failure_code="BAD_REQUEST_ERROR",
            failure_description="Insufficient funds",
            created_at=datetime.utcnow(),
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)
        
        # Analyze payment
        service = IntelligenceService(db)
        result = service.analyze_payment(payment)
        
        # Should still work
        assert result is not None
        assert result.recovery_case_id is None  # No recovery case


class TestIntelligenceAPIEndpoints:
    """Integration tests for intelligence API endpoints."""
    
    def test_get_overview_endpoint(self, db: Session, sample_payment: Payment, client):
        """Test GET /api/v1/intelligence/overview endpoint."""
        # Analyze payment first
        service = IntelligenceService(db)
        service.analyze_payment(sample_payment)
        
        # Call endpoint
        response = client.get("/api/v1/intelligence/overview")
        
        assert response.status_code == 200
        data = response.json()
        assert "total_revenue" in data
        assert "failed_revenue" in data
        assert "revenue_at_risk" in data
        assert "estimated_recoverable_revenue" in data
        assert "recovery_opportunity_count" in data
    
    def test_list_opportunities_endpoint(self, db: Session, sample_payment: Payment, client):
        """Test GET /api/v1/intelligence/opportunities endpoint."""
        # Analyze payment first
        service = IntelligenceService(db)
        service.analyze_payment(sample_payment)
        
        # Call endpoint
        response = client.get("/api/v1/intelligence/opportunities")
        
        assert response.status_code == 200
        data = response.json()
        assert "opportunities" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert len(data["opportunities"]) >= 1
    
    def test_list_opportunities_with_filters(self, db: Session, sample_payment: Payment, client):
        """Test GET /api/v1/intelligence/opportunities with filters."""
        # Analyze payment first
        service = IntelligenceService(db)
        service.analyze_payment(sample_payment)
        
        # Get the priority
        result = service.get_intelligence_by_payment(str(sample_payment.id))
        priority = result.priority.value
        
        # Call endpoint with filter
        response = client.get(f"/api/v1/intelligence/opportunities?priority={priority}")
        
        assert response.status_code == 200
        data = response.json()
        # All results should have the specified priority
        for opp in data["opportunities"]:
            assert opp["priority"] == priority
    
    def test_analyze_payment_endpoint(self, db: Session, sample_payment: Payment, client):
        """Test POST /api/v1/intelligence/analyze/{payment_id} endpoint."""
        # Call endpoint
        response = client.post(f"/api/v1/intelligence/analyze/{sample_payment.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert "payment_id" in data
        assert "failure_category" in data
        assert "recovery_probability" in data
        assert "opportunity_score" in data
        assert "priority" in data
        assert "recommended_intervention" in data
    
    def test_analyze_payment_not_found(self, client):
        """Test analyzing a non-existent payment."""
        import uuid
        fake_id = uuid.uuid4()
        
        response = client.post(f"/api/v1/intelligence/analyze/{fake_id}")
        
        assert response.status_code == 404
    
    def test_batch_analyze_endpoint(self, db: Session, sample_payment: Payment, client):
        """Test POST /api/v1/intelligence/analyze endpoint."""
        # Call endpoint
        response = client.post("/api/v1/intelligence/analyze", json={
            "payment_ids": [str(sample_payment.id)],
            "force_reanalyze": False
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "analyzed_count" in data
        assert "errors" in data
        assert data["analyzed_count"] >= 1
    
    def test_get_opportunity_endpoint(self, db: Session, sample_payment: Payment, client):
        """Test GET /api/v1/intelligence/opportunities/{result_id} endpoint."""
        # Analyze payment first
        service = IntelligenceService(db)
        result = service.analyze_payment(sample_payment)
        
        # Call endpoint
        response = client.get(f"/api/v1/intelligence/opportunities/{result.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == result.id
        assert data["payment_id"] == str(sample_payment.id)
        assert "factors" in data
    
    def test_get_opportunity_not_found(self, client):
        """Test getting a non-existent opportunity."""
        import uuid
        fake_id = uuid.uuid4()
        
        response = client.get(f"/api/v1/intelligence/opportunities/{fake_id}")
        
        assert response.status_code == 404


class TestEndToEndIntelligenceFlow:
    """End-to-end tests for the complete intelligence flow."""
    
    def test_complete_intelligence_flow(self, db: Session):
        """Test the complete flow from payment to intelligence result."""
        unique_suffix = uuid.uuid4().hex[:8]
        # Create merchant
        merchant = Merchant(
            name=f"E2E Test Merchant {unique_suffix}",
            external_id=f"e2e_merchant_{unique_suffix}",
            currency="INR"
        )
        db.add(merchant)
        db.flush()
        
        # Create customer
        customer = Customer(
            external_customer_id=f"e2e_customer_{unique_suffix}",
            email=f"e2e_{unique_suffix}@example.com"
        )
        db.add(customer)
        db.flush()
        
        # Create high-value temporary failure payment
        payment = Payment(
            razorpay_payment_id=f"pay_e2e_{unique_suffix}",
            razorpay_order_id=f"order_e2e_{unique_suffix}",
            merchant_id=merchant.id,
            customer_id=customer.id,
            amount_minor=2500000,  # ₹25,000
            currency="INR",
            status=PaymentStatus.FAILED,
            method="upi",
            failure_code="BANK_ERROR",
            failure_description="Bank processing error - temporary failure",
            created_at=datetime.utcnow() - timedelta(hours=2),
        )
        db.add(payment)
        db.flush()
        
        # Create payment attempt
        attempt = PaymentAttempt(
            payment_id=payment.id,
            attempt_number=1,
            status=PaymentStatus.FAILED,
            failure_code="BANK_ERROR",
            failure_description="Bank processing error",
            method="upi",
            started_at=datetime.utcnow() - timedelta(hours=2),
            completed_at=datetime.utcnow() - timedelta(hours=2, minutes=1),
        )
        db.add(attempt)
        
        # Create recovery case
        recovery_case = RecoveryCase(
            payment_id=payment.id,
            status=RecoveryCaseStatus.OPEN,
            amount_at_risk_minor=payment.amount_minor
        )
        db.add(recovery_case)
        db.commit()
        db.refresh(payment)
        
        # Run intelligence analysis
        service = IntelligenceService(db)
        result = service.analyze_payment(payment)
        
        # Verify the intelligence result
        assert result.payment_id == str(payment.id)
        assert result.recovery_case_id == str(recovery_case.id)
        assert result.revenue_at_risk == 2500000
        assert result.failure_category == FailureCategory.BANK_FAILURE
        assert result.recovery_probability >= 0.5  # Should be reasonably high for temporary failure
        assert result.opportunity_score > 50  # High value should give good score
        assert result.priority in [PriorityLevel.MEDIUM, PriorityLevel.HIGH, PriorityLevel.CRITICAL]
        assert "RETRY" in result.recommended_intervention.upper() or "MANUAL" in result.recommended_intervention.upper()
        
        # Verify factors are present
        assert len(result.factors) > 0
        
        # Verify it's queryable via API
        overview = service.get_overview()
        assert overview.recovery_opportunity_count >= 1
        assert overview.revenue_at_risk >= 2500000
