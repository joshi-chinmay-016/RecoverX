import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.db.base import Base, TimestampMixin, ActionStatus
from app.agent.schemas import ActionType


class RecoveryAction(Base, TimestampMixin):
    """Represents a planned, authorized, or executed recovery action in Phase 4."""
    __tablename__ = "recovery_actions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    action_id = Column(String, unique=True, nullable=False, index=True)
    opportunity_id = Column(UUID(as_uuid=True), ForeignKey("revenue_intelligence_results.id"), nullable=False, index=True)
    payment_id = Column(UUID(as_uuid=True), ForeignKey("payments.id"), nullable=False, index=True)
    merchant_id = Column(UUID(as_uuid=True), ForeignKey("merchants.id"), nullable=False, index=True)
    recovery_plan_id = Column(String, nullable=True, index=True)
    agent_run_id = Column(UUID(as_uuid=True), ForeignKey("agent_runs.id"), nullable=True)

    action_type = Column(SQLEnum(ActionType), nullable=False)
    status = Column(SQLEnum(ActionStatus), nullable=False, default=ActionStatus.PROPOSED, index=True)
    
    parameters = Column(JSONB, nullable=True)
    policy_decision = Column(JSONB, nullable=True)
    idempotency_key = Column(String, unique=True, nullable=False, index=True)
    
    execution_attempts_count = Column(Integer, default=0, nullable=False)
    max_attempts = Column(Integer, default=3, nullable=False)
    
    provider_reference = Column(String, nullable=True, index=True)
    last_result = Column(JSONB, nullable=True)
    last_error_code = Column(String, nullable=True)
    last_error_message = Column(Text, nullable=True)
    
    policy_version = Column(String, default="policy-v1", nullable=False)
    execution_version = Column(String, default="execution-v1", nullable=False)
    
    requested_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    authorized_at = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    payment = relationship("Payment")
    merchant = relationship("Merchant")
    attempts = relationship("ExecutionAttempt", back_populates="action", cascade="all, delete-orphan", order_by="ExecutionAttempt.attempt_number")
