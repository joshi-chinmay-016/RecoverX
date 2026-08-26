import json
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.db.models.webhook_event import WebhookEvent
from app.db.base import ProcessingStatus
from app.core.logging import logger
import redis as redis_lib


class WebhookService:
    """Service for handling webhook events."""
    
    def __init__(self, db: Session, redis_client: Optional[redis_lib.Redis] = None):
        self.db = db
        self.redis = redis_client
    
    def check_duplicate(self, provider_event_id: str) -> Optional[WebhookEvent]:
        """Check if webhook event already exists (idempotency)."""
        event = self.db.query(WebhookEvent).filter(
            WebhookEvent.provider_event_id == provider_event_id
        ).first()
        
        if event:
            logger.info(f"duplicate_webhook_detected provider_event_id={provider_event_id}")
        
        return event
    
    def create_webhook_event(
        self,
        provider_event_id: str,
        event_type: str,
        payload: dict,
        signature_verified: bool
    ) -> WebhookEvent:
        """Create a new webhook event."""
        webhook_event = WebhookEvent(
            provider_event_id=provider_event_id,
            event_type=event_type,
            payload=payload,
            signature_verified=signature_verified,
            processing_status=ProcessingStatus.RECEIVED,
            received_at=datetime.utcnow()
        )
        
        self.db.add(webhook_event)
        self.db.commit()
        self.db.refresh(webhook_event)
        
        logger.info(
            f"webhook_event_created "
            f"provider_event_id={provider_event_id} "
            f"event_type={event_type}"
        )
        
        return webhook_event
    
    def queue_for_processing(self, webhook_event_id: str) -> None:
        """Queue webhook event for background processing, with sync fallback."""
        if self.redis is not None:
            try:
                self.redis.lpush("webhook_queue", webhook_event_id)
                logger.info(f"webhook_queued webhook_event_id={webhook_event_id}")
                return
            except Exception as e:
                logger.warning(f"webhook_queue_fallback webhook_event_id={webhook_event_id} error={str(e)}")
        
        # Fallback to synchronous inline processing
        self._process_event_sync(webhook_event_id)
    
    def _process_event_sync(self, webhook_event_id: str) -> None:
        """Process event synchronously when Redis is not available."""
        from app.modules.payments.service import PaymentService
        from app.modules.recovery.service import RecoveryService
        from app.utils.audit import AuditService
        from app.db.base import AuditEventType, ActorType
        
        webhook_event = self.db.query(WebhookEvent).filter(
            WebhookEvent.id == webhook_event_id
        ).first()
        if not webhook_event:
            return
            
        webhook_event.processing_status = ProcessingStatus.PROCESSING
        self.db.commit()
        
        try:
            event_type = webhook_event.event_type
            payload = webhook_event.payload
            
            if event_type == "payment.failed":
                payment_service = PaymentService(self.db)
                recovery_service = RecoveryService(self.db)
                payment = payment_service.process_payment_failed(payload)
                recovery_service.create_recovery_case_for_payment(payment)
                AuditService.create_audit_event(
                    db=self.db,
                    entity_type="Payment",
                    entity_id=str(payment.id),
                    event_type=AuditEventType.PAYMENT_STATUS_CHANGED,
                    actor_type=ActorType.WEBHOOK,
                    metadata={"razorpay_payment_id": payment.razorpay_payment_id, "status": "FAILED"}
                )
            elif event_type == "payment.authorized":
                payment_service = PaymentService(self.db)
                payment_service.process_payment_authorized(payload)
            elif event_type == "payment.captured":
                payment_service = PaymentService(self.db)
                payment_service.process_payment_captured(payload)
            else:
                webhook_event.processing_status = ProcessingStatus.IGNORED
                self.db.commit()
                return

            webhook_event.processed_at = datetime.utcnow()
            webhook_event.processing_status = ProcessingStatus.PROCESSED
            self.db.commit()
        except Exception as e:
            webhook_event.processing_status = ProcessingStatus.FAILED
            webhook_event.error_message = str(e)
            webhook_event.processed_at = datetime.utcnow()
            self.db.commit()
            logger.error(f"sync_webhook_processing_failed error={str(e)}")
    
    def get_webhook_event(self, event_id: str) -> Optional[WebhookEvent]:
        """Get webhook event by ID."""
        return self.db.query(WebhookEvent).filter(
            WebhookEvent.id == event_id
        ).first()
    
    def list_webhook_events(
        self,
        event_type: Optional[str] = None,
        processing_status: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[list[WebhookEvent], int]:
        """List webhook events with filters and pagination."""
        query = self.db.query(WebhookEvent)
        
        if event_type:
            query = query.filter(WebhookEvent.event_type == event_type)
        
        if processing_status:
            query = query.filter(WebhookEvent.processing_status == processing_status)
        
        if from_date:
            query = query.filter(WebhookEvent.received_at >= from_date)
        
        if to_date:
            query = query.filter(WebhookEvent.received_at <= to_date)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        events = query.order_by(WebhookEvent.received_at.desc()).offset(offset).limit(page_size).all()
        
        return events, total