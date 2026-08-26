import json
import uuid
from fastapi import APIRouter, Request, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from app.db.session import get_db
from app.modules.webhooks.verifier import WebhookVerifier
from app.modules.webhooks.service import WebhookService
from app.modules.webhooks.schemas import WebhookEventResponse, WebhookEventListResponse
import redis as redis_lib
from app.core.config import settings
from app.core.logging import logger

webhook_router = APIRouter()


@webhook_router.post("/razorpay")
async def receive_razorpay_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Receive Razorpay webhook events.
    
    This endpoint:
    1. Verifies webhook signature using raw body
    2. Checks for duplicate events (idempotency)
    3. Persists the raw event
    4. Queues event for background processing
    5. Returns quickly to avoid Razorpay timeout
    """
    try:
        # Step 1: Verify signature using raw body
        raw_body, signature = await WebhookVerifier.extract_and_verify(request)
        
        # Step 2: Parse JSON after verification
        payload = json.loads(raw_body.decode('utf-8'))
        
        # Extract event information
        provider_event_id = request.headers.get("x-razorpay-event-id")
        event_type = payload.get("event")
        
        if not provider_event_id:
            logger.warning("webhook_missing_event_id")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing event ID header"
            )
        
        if not event_type:
            logger.warning("webhook_missing_event_type")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing event type in payload"
            )
        
        # Step 3: Initialize Redis and service
        try:
            redis_client = redis_lib.from_url(settings.redis_url)
        except Exception:
            redis_client = None
        webhook_service = WebhookService(db, redis_client)
        
        # Step 4: Check for duplicate (idempotency)
        existing_event = webhook_service.check_duplicate(provider_event_id)
        if existing_event:
            logger.info(f"duplicate_webhook_acknowledged provider_event_id={provider_event_id}")
            return {"status": "acknowledged", "message": "Duplicate event"}
        
        # Step 5: Create webhook event
        webhook_event = webhook_service.create_webhook_event(
            provider_event_id=provider_event_id,
            event_type=event_type,
            payload=payload,
            signature_verified=True
        )
        
        # Step 6: Queue for background processing
        webhook_service.queue_for_processing(str(webhook_event.id))
        
        # Step 7: Create audit event
        from app.utils.audit import AuditService
        from app.db.base import AuditEventType, ActorType
        
        AuditService.create_audit_event(
            db=db,
            entity_type="WebhookEvent",
            entity_id=str(webhook_event.id),
            event_type=AuditEventType.WEBHOOK_RECEIVED,
            actor_type=ActorType.WEBHOOK,
            metadata={
                "provider_event_id": provider_event_id,
                "event_type": event_type
            }
        )
        
        logger.info(
            f"webhook_received_and_queued "
            f"provider_event_id={provider_event_id} "
            f"event_type={event_type}"
        )
        
        return {"status": "received", "message": "Webhook received and queued"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"webhook_processing_error error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@webhook_router.get("/events", response_model=WebhookEventListResponse)
async def list_webhook_events(
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    processing_status: Optional[str] = Query(None, description="Filter by processing status"),
    from_date: Optional[datetime] = Query(None, description="Filter from date"),
    to_date: Optional[datetime] = Query(None, description="Filter to date"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db)
):
    """List webhook events with filters and pagination."""
    webhook_service = WebhookService(db, None)
    
    events, total = webhook_service.list_webhook_events(
        event_type=event_type,
        processing_status=processing_status,
        from_date=from_date,
        to_date=to_date,
        page=page,
        page_size=page_size
    )
    
    return WebhookEventListResponse(
        events=events,
        total=total,
        page=page,
        page_size=page_size
    )


@webhook_router.get("/events/{event_id}", response_model=WebhookEventResponse)
async def get_webhook_event(
    event_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific webhook event by ID."""
    webhook_service = WebhookService(db, None)
    
    event = webhook_service.get_webhook_event(event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook event not found"
        )
    
    return event