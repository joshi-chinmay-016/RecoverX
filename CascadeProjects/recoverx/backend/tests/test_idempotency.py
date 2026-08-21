import pytest
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.modules.webhooks.service import WebhookService
from app.db.models.webhook_event import WebhookEvent
from app.db.base import ProcessingStatus
import redis as redis_lib


class TestIdempotency:
    """Test idempotent event processing."""
    
    @pytest.fixture
    def db(self):
        """Database session fixture."""
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    @pytest.fixture
    def redis_client(self):
        """Redis client fixture."""
        redis_client = redis_lib.from_url("redis://localhost:6379/0")
        yield redis_client
        redis_client.close()
    
    @pytest.fixture
    def webhook_service(self, db, redis_client):
        """Webhook service fixture."""
        return WebhookService(db, redis_client)
    
    def test_duplicate_event_detection(self, webhook_service):
        """Test that duplicate events are detected."""
        provider_event_id = "evt_123"
        
        # Create first event
        first_event = webhook_service.create_webhook_event(
            provider_event_id=provider_event_id,
            event_type="payment.failed",
            payload={"test": "data"},
            signature_verified=True
        )
        
        # Check for duplicate
        duplicate = webhook_service.check_duplicate(provider_event_id)
        
        assert duplicate is not None
        assert duplicate.id == first_event.id
        assert duplicate.provider_event_id == provider_event_id
    
    def test_no_duplicate_for_new_event(self, webhook_service):
        """Test that new events are not detected as duplicates."""
        provider_event_id = "evt_123"
        
        # Check for non-existent event
        duplicate = webhook_service.check_duplicate(provider_event_id)
        
        assert duplicate is None
    
    def test_duplicate_event_not_processed_again(self, webhook_service):
        """Test that duplicate events are not processed again."""
        provider_event_id = "evt_123"
        
        # Create first event
        first_event = webhook_service.create_webhook_event(
            provider_event_id=provider_event_id,
            event_type="payment.failed",
            payload={"test": "data"},
            signature_verified=True
        )
        
        # Attempt to create duplicate
        duplicate = webhook_service.check_duplicate(provider_event_id)
        
        # Should return existing event, not create new one
        assert duplicate.id == first_event.id
        assert duplicate.provider_event_id == provider_event_id