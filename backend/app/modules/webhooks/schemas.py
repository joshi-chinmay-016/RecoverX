from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class WebhookEventCreate(BaseModel):
    """Schema for creating a webhook event."""
    provider_event_id: str = Field(..., description="External event ID from provider")
    event_type: str = Field(..., description="Type of webhook event")
    payload: Dict[str, Any] = Field(..., description="Raw webhook payload")
    signature_verified: bool = Field(default=False, description="Whether signature was verified")


class WebhookEventResponse(BaseModel):
    """Schema for webhook event response."""
    id: str
    provider_event_id: str
    provider: str
    event_type: str
    payload: Dict[str, Any]
    signature_verified: bool
    processing_status: str
    received_at: datetime
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class WebhookEventListResponse(BaseModel):
    """Schema for paginated webhook event list."""
    events: List[WebhookEventResponse]
    total: int
    page: int
    page_size: int