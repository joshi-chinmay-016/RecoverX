from datetime import datetime
from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, UniqueConstraint, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base, TimestampMixin, PaymentStatus
import uuid


class PaymentAttempt(Base, TimestampMixin):
    __tablename__ = "payment_attempts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payment_id = Column(UUID(as_uuid=True), ForeignKey("payments.id"), nullable=False)
    attempt_number = Column(Integer, nullable=False)
    status = Column(SQLEnum(PaymentStatus), nullable=False)
    failure_code = Column(String, nullable=True)
    failure_description = Column(String, nullable=True)
    method = Column(String, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    payment = relationship("Payment", back_populates="attempts")

    __table_args__ = (
        UniqueConstraint("payment_id", "attempt_number", name="uq_payment_attempt"),
    )
