"""Database model for granular Learning Outcome Records (Phase 5)."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.db.base import Base, TimestampMixin, ActionStatus
from app.intelligence.schemas import FailureCategory
from app.agent.schemas import ActionType


class LearningOutcomeRecord(Base, TimestampMixin):
    """Historical record of a confirmed recovery attempt outcome used for learning."""
    __tablename__ = "learning_outcome_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id = Column(UUID(as_uuid=True), ForeignKey("merchants.id"), nullable=False, index=True)
    payment_id = Column(UUID(as_uuid=True), ForeignKey("payments.id"), nullable=False, index=True)
    recovery_action_id = Column(UUID(as_uuid=True), ForeignKey("recovery_actions.id"), nullable=True)
    
    failure_category = Column(SQLEnum(FailureCategory), nullable=False, index=True)
    action_type = Column(SQLEnum(ActionType), nullable=False, index=True)
    
    amount_minor = Column(Integer, nullable=False, default=0)
    retry_count = Column(Integer, nullable=False, default=0)
    payment_method = Column(String, nullable=True)
    
    # Confirmed outcome: SUCCESS, FAILURE, UNKNOWN, BLOCKED
    outcome_status = Column(SQLEnum(ActionStatus), nullable=False, index=True)
    
    execution_latency_ms = Column(Integer, nullable=False, default=0)
    occurred_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    context_metadata = Column(JSONB, nullable=True)

    merchant = relationship("Merchant")
    payment = relationship("Payment")
    recovery_action = relationship("RecoveryAction")
