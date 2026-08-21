from datetime import datetime
from sqlalchemy import Column, String, Boolean, Enum as SQLEnum, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db.base import Base, TimestampMixin, ProcessingStatus
import uuid


class WebhookEvent(Base, TimestampMixin):
    __tablename__ = "webhook_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider_event_id = Column(String, unique=True, nullable=False, index=True)
    provider = Column(String, nullable=False, default="razorpay")
    event_type = Column(String, nullable=False, index=True)
    payload = Column(JSONB, nullable=False)
    signature_verified = Column(Boolean, nullable=False, default=False)
    processing_status = Column(SQLEnum(ProcessingStatus), nullable=False, default=ProcessingStatus.RECEIVED)
    received_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
