import asyncio
import json
import sys
from datetime import datetime
from sqlalchemy.orm import Session
import redis as redis_lib
from app.db.session import SessionLocal
from app.db.models.webhook_event import WebhookEvent
from app.db.base import ProcessingStatus
from app.modules.payments.service import PaymentService
from app.modules.recovery.service import RecoveryService
from app.utils.audit import AuditService
from app.db.base import AuditEventType, ActorType
from app.core.config import settings
from app.core.logging import logger, setup_logging


class WebhookWorker:
    """Background worker for processing webhook events."""
    
    def __init__(self):
        self.redis = redis_lib.from_url(settings.redis_url)
        self.running = True
    
    async def process_event(self, webhook_event_id: str) -> None:
        """Process a single webhook event."""
        db: Session = SessionLocal()
        try:
            # Get webhook event
            webhook_event = db.query(WebhookEvent).filter(
                WebhookEvent.id == webhook_event_id
            ).first()
            
            if not webhook_event:
                logger.error(f"webhook_event_not_found id={webhook_event_id}")
                return
            
            # Update status to PROCESSING
            webhook_event.processing_status = ProcessingStatus.PROCESSING
            db.commit()
            
            # Process based on event type
            event_type = webhook_event.event_type
            payload = webhook_event.payload
            
            logger.info(
                f"processing_webhook_event "
                f"provider_event_id={webhook_event.provider_event_id} "
                f"event_type={event_type}"
            )
            
            try:
                if event_type == "payment.failed":
                    self._process_payment_failed(db, payload, webhook_event)
                elif event_type == "payment.authorized":
                    self._process_payment_authorized(db, payload, webhook_event)
                elif event_type == "payment.captured":
                    self._process_payment_captured(db, payload, webhook_event)
                else:
                    # Unknown event type - mark as IGNORED
                    webhook_event.processing_status = ProcessingStatus.IGNORED
                    db.commit()
                    logger.info(f"unknown_event_type_ignored event_type={event_type}")
                
                # Update processed timestamp
                webhook_event.processed_at = datetime.utcnow()
                webhook_event.processing_status = ProcessingStatus.PROCESSED
                db.commit()
                
                logger.info(
                    f"webhook_event_processed "
                    f"provider_event_id={webhook_event.provider_event_id}"
                )
                
            except Exception as e:
                # Update status to FAILED
                webhook_event.processing_status = ProcessingStatus.FAILED
                webhook_event.error_message = str(e)
                webhook_event.processed_at = datetime.utcnow()
                db.commit()
                
                logger.error(
                    f"webhook_event_processing_failed "
                    f"provider_event_id={webhook_event.provider_event_id} "
                    f"error={str(e)}"
                )
                
        except Exception as e:
            logger.error(f"worker_processing_error error={str(e)}")
        finally:
            db.close()
    
    def _process_payment_failed(self, db: Session, payload: dict, webhook_event: WebhookEvent) -> None:
        """Process payment.failed event."""
        payment_service = PaymentService(db)
        recovery_service = RecoveryService(db)
        
        # Process payment failure
        payment = payment_service.process_payment_failed(payload)
        
        # Create recovery case
        recovery_service.create_recovery_case_for_payment(payment)
        
        # Create audit event
        AuditService.create_audit_event(
            db=db,
            entity_type="Payment",
            entity_id=str(payment.id),
            event_type=AuditEventType.PAYMENT_STATUS_CHANGED,
            actor_type=ActorType.WEBHOOK,
            metadata={"razorpay_payment_id": payment.razorpay_payment_id, "status": "FAILED"}
        )
    
    def _process_payment_authorized(self, db: Session, payload: dict, webhook_event: WebhookEvent) -> None:
        """Process payment.authorized event."""
        payment_service = PaymentService(db)
        
        # Process payment authorization
        payment = payment_service.process_payment_authorized(payload)
        
        # Create audit event
        AuditService.create_audit_event(
            db=db,
            entity_type="Payment",
            entity_id=str(payment.id),
            event_type=AuditEventType.PAYMENT_STATUS_CHANGED,
            actor_type=ActorType.WEBHOOK,
            metadata={"razorpay_payment_id": payment.razorpay_payment_id, "status": "AUTHORIZED"}
        )
    
    def _process_payment_captured(self, db: Session, payload: dict, webhook_event: WebhookEvent) -> None:
        """Process payment.captured event."""
        payment_service = PaymentService(db)
        recovery_service = RecoveryService(db)
        
        # Process payment capture
        payment = payment_service.process_payment_captured(payload)
        
        # Resolve recovery case if exists
        recovery_service.resolve_recovery_case(payment)
        
        # Create audit event
        AuditService.create_audit_event(
            db=db,
            entity_type="Payment",
            entity_id=str(payment.id),
            event_type=AuditEventType.PAYMENT_STATUS_CHANGED,
            actor_type=ActorType.WEBHOOK,
            metadata={"razorpay_payment_id": payment.razorpay_payment_id, "status": "CAPTURED"}
        )
    
    async def run(self) -> None:
        """Main worker loop."""
        logger.info("webhook_worker_started")
        
        while self.running:
            try:
                # Pop event from queue (blocking with timeout)
                result = self.redis.brpop("webhook_queue", timeout=5)
                
                if result:
                    _, webhook_event_id = result
                    webhook_event_id = webhook_event_id.decode('utf-8')
                    
                    logger.info(f"webhook_dequeued webhook_event_id={webhook_event_id}")
                    
                    # Process the event
                    await self.process_event(webhook_event_id)
                
            except Exception as e:
                logger.error(f"worker_loop_error error={str(e)}")
                await asyncio.sleep(1)
        
        logger.info("webhook_worker_stopped")
    
    def stop(self) -> None:
        """Stop the worker."""
        self.running = False


async def main():
    """Main entry point for the worker."""
    setup_logging()
    worker = WebhookWorker()
    
    try:
        await worker.run()
    except KeyboardInterrupt:
        logger.info("worker_interrupted")
        worker.stop()


if __name__ == "__main__":
    asyncio.run(main())