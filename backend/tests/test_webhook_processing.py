import pytest
import json
import uuid
import hmac
import hashlib
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.db.session import SessionLocal
from app.db.models.webhook_event import WebhookEvent
from app.db.models.payment import Payment
from app.db.models.recovery_case import RecoveryCase
from app.db.models.merchant import Merchant
from app.db.base import ProcessingStatus, PaymentStatus, RecoveryCaseStatus


class TestWebhookProcessing:
    """Test webhook processing."""
    
    @pytest.fixture
    def client(self):
        """Test client fixture."""
        return TestClient(app)
    
    @pytest.fixture
    def db(self):
        """Database session fixture."""
        db_session = SessionLocal()
        try:
            yield db_session
        finally:
            db_session.rollback()
            db_session.close()
    
    @pytest.fixture
    def webhook_secret(self):
        """Test webhook secret."""
        return "test_webhook_secret"
    
    def _sign_payload(self, payload: dict, secret: str) -> str:
        payload_bytes = json.dumps(payload).encode('utf-8')
        return hmac.new(
            secret.encode('utf-8'),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()
    
    def test_payment_failed_creates_recovery_case(self, client, db, webhook_secret, monkeypatch):
        """Test that payment.failed creates recovery case."""
        from app.core.config import settings
        monkeypatch.setattr(settings, 'razorpay_webhook_secret', webhook_secret)
        
        unique_suffix = uuid.uuid4().hex[:8]
        merchant = Merchant(
            id=uuid.uuid4(),
            name=f"Test Merchant {unique_suffix}",
            external_id=f"test_merchant_{unique_suffix}",
            currency="INR"
        )
        db.add(merchant)
        db.commit()
        
        payload = {
            "event": "payment.failed",
            "entity": {
                "id": f"pay_{unique_suffix}",
                "amount": 1000,
                "currency": "INR",
                "status": "failed",
                "method": "upi",
                "error_code": "BAD_REQUEST_ERROR",
                "error_description": "Payment failed"
            }
        }
        payload_bytes = json.dumps(payload).encode('utf-8')
        signature = self._sign_payload(payload, webhook_secret)
        
        # Send webhook
        response = client.post(
            "/api/v1/webhooks/razorpay",
            content=payload_bytes,
            headers={
                "Content-Type": "application/json",
                "x-razorpay-signature": signature,
                "x-razorpay-event-id": f"evt_{unique_suffix}"
            }
        )
        
        assert response.status_code == 200
        
        # Verify payment was created
        payment = db.query(Payment).filter(
            Payment.razorpay_payment_id == f"pay_{unique_suffix}"
        ).first()
        assert payment is not None
        assert payment.status == PaymentStatus.FAILED
        
        # Verify recovery case was created
        recovery_case = db.query(RecoveryCase).filter(
            RecoveryCase.payment_id == payment.id
        ).first()
        assert recovery_case is not None
        assert recovery_case.status == RecoveryCaseStatus.OPEN
    
    def test_unknown_event_type_ignored(self, client, webhook_secret, monkeypatch):
        """Test that unknown event types are ignored."""
        from app.core.config import settings
        monkeypatch.setattr(settings, 'razorpay_webhook_secret', webhook_secret)
        
        unique_suffix = uuid.uuid4().hex[:8]
        payload = {
            "event": "unknown.event",
            "entity": {
                "id": f"pay_{unique_suffix}",
                "amount": 1000,
            }
        }
        payload_bytes = json.dumps(payload).encode('utf-8')
        signature = self._sign_payload(payload, webhook_secret)
        
        response = client.post(
            "/api/v1/webhooks/razorpay",
            content=payload_bytes,
            headers={
                "Content-Type": "application/json",
                "x-razorpay-signature": signature,
                "x-razorpay-event-id": f"evt_unknown_{unique_suffix}"
            }
        )
        
        assert response.status_code == 200
    
    def test_invalid_signature_rejected(self, client, webhook_secret, monkeypatch):
        """Test that invalid signature is rejected."""
        from app.core.config import settings
        monkeypatch.setattr(settings, 'razorpay_webhook_secret', webhook_secret)
        
        unique_suffix = uuid.uuid4().hex[:8]
        payload = {
            "event": "payment.failed",
            "entity": {
                "id": f"pay_{unique_suffix}",
            }
        }
        payload_bytes = json.dumps(payload).encode('utf-8')
        
        response = client.post(
            "/api/v1/webhooks/razorpay",
            content=payload_bytes,
            headers={
                "Content-Type": "application/json",
                "x-razorpay-signature": "invalid_signature_string",
                "x-razorpay-event-id": f"evt_invalid_{unique_suffix}"
            }
        )
        
        assert response.status_code == 401