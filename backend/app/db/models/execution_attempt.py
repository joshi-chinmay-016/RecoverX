import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.db.base import Base, TimestampMixin, ExecutionAttemptStatus


class ExecutionAttempt(Base, TimestampMixin):
    """Represents an individual execution attempt against a provider adapter."""
    __tablename__ = "execution_attempts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    action_id = Column(UUID(as_uuid=True), ForeignKey("recovery_actions.id"), nullable=False, index=True)
    attempt_number = Column(Integer, nullable=False)
    idempotency_key = Column(String, nullable=False, index=True)
    adapter_name = Column(String, nullable=False)
    
    status = Column(SQLEnum(ExecutionAttemptStatus), nullable=False, default=ExecutionAttemptStatus.PENDING)
    request_payload = Column(JSONB, nullable=True)
    response_payload = Column(JSONB, nullable=True)
    
    provider_reference = Column(String, nullable=True, index=True)
    error_code = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    is_retryable = Column(Boolean, default=False, nullable=False)
    execution_latency_ms = Column(Integer, default=0, nullable=False)
    
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    action = relationship("RecoveryAction", back_populates="attempts")
