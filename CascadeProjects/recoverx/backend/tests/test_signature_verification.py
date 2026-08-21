import pytest
import hmac
import hashlib
from app.modules.webhooks.verifier import WebhookVerifier


class TestSignatureVerification:
    """Test webhook signature verification."""
    
    @pytest.fixture
    def webhook_secret(self):
        """Test webhook secret."""
        return "test_webhook_secret"
    
    @pytest.fixture
    def valid_payload(self):
        """Valid webhook payload."""
        return b'{"event": "payment.failed", "entity": {"id": "pay_123"}}'
    
    @pytest.fixture
    def valid_signature(self, webhook_secret, valid_payload):
        """Generate valid signature for payload."""
        signature = hmac.new(
            webhook_secret.encode('utf-8'),
            valid_payload,
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def test_valid_signature_accepted(self, valid_payload, valid_signature, monkeypatch):
        """Test that valid signature is accepted."""
        from app.core.config import settings
        monkeypatch.setattr(settings, 'razorpay_webhook_secret', 'test_webhook_secret')
        
        result = WebhookVerifier.verify_signature(valid_payload, valid_signature)
        assert result is True
    
    def test_invalid_signature_rejected(self, valid_payload, monkeypatch):
        """Test that invalid signature is rejected."""
        from app.core.config import settings
        monkeypatch.setattr(settings, 'razorpay_webhook_secret', 'test_webhook_secret')
        
        invalid_signature = "invalid_signature"
        result = WebhookVerifier.verify_signature(valid_payload, invalid_signature)
        assert result is False
    
    def test_modified_payload_rejected(self, valid_signature, monkeypatch):
        """Test that modified payload is rejected."""
        from app.core.config import settings
        monkeypatch.setattr(settings, 'razorpay_webhook_secret', 'test_webhook_secret')
        
        modified_payload = b'{"event": "payment.captured", "entity": {"id": "pay_123"}}'
        result = WebhookVerifier.verify_signature(modified_payload, valid_signature)
        assert result is False