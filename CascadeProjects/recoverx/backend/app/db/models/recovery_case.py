from sqlalchemy import Column, Integer, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base, TimestampMixin, RecoveryCaseStatus
import uuid


class RecoveryCase(Base, TimestampMixin):
    __tablename__ = "recovery_cases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payment_id = Column(UUID(as_uuid=True), ForeignKey("payments.id"), nullable=False)
    status = Column(SQLEnum(RecoveryCaseStatus), nullable=False)
    amount_at_risk_minor = Column(Integer, nullable=False)

    payment = relationship("Payment", back_populates="recovery_cases")
