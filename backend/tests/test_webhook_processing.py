import pytest
import json
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.db.session import SessionLocal
from app.db.models.webhook_event import WebhookEvent
from app.db.models.payment import Payment
from app.db.models.recovery_case import RecoveryCase
from app.db.base import ProcessingStatus, PaymentStatus, RecoveryCaseStatus
import hmac
import hashlib


class TestWebhookProcessing:
    """Test webhook processing."""
    
    @pytest.fixture
    def client(self):
        """Test client fixture."""
        return TestClient(app)
    
    @pytest.fixture
    def db(self):
        """Database session fixture."""
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    @pytest.fixture
    def webhook_secret(self):
        """Test webhook secret."""
        return "test_webhook_secret"
    
    @pytest.fixture
    def sample_payload(self):
        """Sample webhook payload."""
        return {
            "event": "payment.failed",
            "entity": {
                "id": "pay_123",
                "amount": 1000,
                "currency": "INR",
                "status": "failed",
                "method": "upi",
                "error_code": "BAD_REQUEST_ERROR",
                "error_description": "Payment failed"
            }
        }
    
    @pytest.fixture
    def valid_signature(self, webhook_secret, sample_payload):
        """Generate valid signature."""
        payload_bytes = json.dumps(sample_payload).encode('utf-8')
        signature = hmac.new(
            webhook_secret.encode('utf-8'),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def test_payment_failed_creates_recovery_case(self, client, db, sample_payload, valid_signature, monkeypatch):
        """Test that payment.failed creates recovery case."""
        from app.core.config import settings
        monkeypatch.setattr(settings, 'razorpay_webhook_secret', 'test_webhook_secret')
        
        # Create merchant first
        from app.db.models.merchant import Merchant
        from app.db.models.customer import Customer
        import uuid
        
        merchant = Merchant(
            id=uuid.uuid4(),
            name="Test Merchant",
            external_id="test_merchant",
            currency="INR"
        )
        db.add(merchant)
        db.commit()
        
        # Send webhook
        response = client.post(
            "/api/v1/webhooks/razorpay",
            json=sample_payload,
            headers={
                "x-razorpay-signature": valid_signature,
                "x-razorpay-event-id": "evt_123"
            }
        )
        
        assert response.status_code == 200
        
        # Verify payment was created
        payment = db.query(Payment).filter(
            Payment.razorpay_payment_id == "pay_123"
        ).first()
        assert payment is not None
        assert payment.status == PaymentStatus.FAILED
        
        # Verify recovery case was created
        recovery_case = db.query(RecoveryCase).filter(
            RecoveryCase.payment_id == payment.id
        ).first()
        assert recovery_case is not None
        assert recovery_case.status == RecoveryCaseStatus.OPEN
    
    def test_unknown_event_type_ignored(self, client, sample_payload, valid_signature, monkeypatch):
        """Test that unknown event types are ignored."""
        from app.core.config import settings
        monkeypatch.setattr(settings, 'razorpay_webhook_secret', 'test_webhook_secret')
        
        sample_payload["event"] = "unknown.event"
        
        response = client.post(
            "/api/v1/webhooks/razorpay",
            json=sample_payload,
            headers={
                "x-razorpay-signature": valid_signature,
                "x-razorpay-event-id": "evt_456"
            }
        )
        
        assert response.status_code == 200
    
    def test_invalid_signature_rejected(self, client, sample_payload, monkeypatch):
        """Test that invalid signature is rejected."""
        from app.core.config import settings
        monkeypatch.setattr(settings, 'razorpay_webhook_secret', 'test_webhook_secret')
        
        response = client.post(
            "/api/v1/webhooks/razorpay",
            json=sample_payload,
            headers={
                "x-razorpay-signature": "invalid_signature",
                "x-razorpay-event-id": "evt_789"
            }
        )
        
        assert response.status_code == 401