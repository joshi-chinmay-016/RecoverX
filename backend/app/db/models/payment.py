from sqlalchemy import Column, String, Integer, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base, TimestampMixin, PaymentStatus
import uuid


class Payment(Base, TimestampMixin):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    razorpay_payment_id = Column(String, unique=True, nullable=False, index=True)
    razorpay_order_id = Column(String, nullable=True)
    merchant_id = Column(UUID(as_uuid=True), ForeignKey("merchants.id"), nullable=False)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=True)
    amount_minor = Column(Integer, nullable=False)  # Store in paise (minor units)
    currency = Column(String, nullable=False)
    status = Column(SQLEnum(PaymentStatus), nullable=False)
    method = Column(String, nullable=True)
    failure_code = Column(String, nullable=True)
    failure_description = Column(String, nullable=True)

    merchant = relationship("Merchant")
    customer = relationship("Customer", back_populates="payments")
    attempts = relationship("PaymentAttempt", back_populates="payment", cascade="all, delete-orphan")
    recovery_cases = relationship("RecoveryCase", back_populates="payment", cascade="all, delete-orphan")

    def transition_to(self, new_status: PaymentStatus) -> bool:
        """
        Centralized state transition logic.
        Returns True if transition is valid, False otherwise.
        """
        valid_transitions = {
            PaymentStatus.CREATED: [PaymentStatus.AUTHORIZED, PaymentStatus.FAILED],
            PaymentStatus.AUTHORIZED: [PaymentStatus.CAPTURED, PaymentStatus.FAILED],
            PaymentStatus.FAILED: [PaymentStatus.AUTHORIZED, PaymentStatus.CAPTURED],  # Out-of-order support
            PaymentStatus.CAPTURED: [],  # Terminal state
        }

        if new_status in valid_transitions.get(self.status, []):
            self.status = new_status
            return True
        return False
