import pytest
from app.db.models.payment import Payment
from app.db.base import PaymentStatus


class TestStateTransitions:
    """Test payment state transitions."""
    
    @pytest.fixture
    def payment(self):
        """Create a test payment."""
        import uuid
        payment = Payment(
            id=uuid.uuid4(),
            razorpay_payment_id="pay_123",
            razorpay_order_id="order_123",
            merchant_id=uuid.uuid4(),
            customer_id=uuid.uuid4(),
            amount_minor=1000,
            currency="INR",
            status=PaymentStatus.CREATED
        )
        return payment
    
    def test_valid_transition_created_to_authorized(self, payment):
        """Test valid transition: CREATED -> AUTHORIZED."""
        result = payment.transition_to(PaymentStatus.AUTHORIZED)
        assert result is True
        assert payment.status == PaymentStatus.AUTHORIZED
    
    def test_valid_transition_created_to_failed(self, payment):
        """Test valid transition: CREATED -> FAILED."""
        result = payment.transition_to(PaymentStatus.FAILED)
        assert result is True
        assert payment.status == PaymentStatus.FAILED
    
    def test_valid_transition_authorized_to_captured(self, payment):
        """Test valid transition: AUTHORIZED -> CAPTURED."""
        payment.status = PaymentStatus.AUTHORIZED
        result = payment.transition_to(PaymentStatus.CAPTURED)
        assert result is True
        assert payment.status == PaymentStatus.CAPTURED
    
    def test_valid_transition_authorized_to_failed(self, payment):
        """Test valid transition: AUTHORIZED -> FAILED."""
        payment.status = PaymentStatus.AUTHORIZED
        result = payment.transition_to(PaymentStatus.FAILED)
        assert result is True
        assert payment.status == PaymentStatus.FAILED
    
    def test_valid_transition_failed_to_authorized(self, payment):
        """Test valid transition: FAILED -> AUTHORIZED (out-of-order support)."""
        payment.status = PaymentStatus.FAILED
        result = payment.transition_to(PaymentStatus.AUTHORIZED)
        assert result is True
        assert payment.status == PaymentStatus.AUTHORIZED
    
    def test_valid_transition_failed_to_captured(self, payment):
        """Test valid transition: FAILED -> CAPTURED (out-of-order support)."""
        payment.status = PaymentStatus.FAILED
        result = payment.transition_to(PaymentStatus.CAPTURED)
        assert result is True
        assert payment.status == PaymentStatus.CAPTURED
    
    def test_invalid_transition_captured_to_any(self, payment):
        """Test invalid transition: CAPTURED is terminal state."""
        payment.status = PaymentStatus.CAPTURED
        result = payment.transition_to(PaymentStatus.AUTHORIZED)
        assert result is False
        assert payment.status == PaymentStatus.CAPTURED
    
    def test_invalid_transition_authorized_to_created(self, payment):
        """Test invalid transition: AUTHORIZED -> CREATED."""
        payment.status = PaymentStatus.AUTHORIZED
        result = payment.transition_to(PaymentStatus.CREATED)
        assert result is False
        assert payment.status == PaymentStatus.AUTHORIZED