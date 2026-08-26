from datetime import datetime
from typing import Optional, List, Any
from sqlalchemy.orm import Session
from app.db.models.payment import Payment
from app.db.models.payment_attempt import PaymentAttempt
from app.db.base import PaymentStatus
from app.modules.payments.repository import PaymentRepository
from app.core.logging import logger


class PaymentService:
    """Service for payment-related business logic."""
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = PaymentRepository(db)
    
    def process_payment_failed(self, payload: dict) -> Payment:
        """Process payment.failed event."""
        razorpay_payment_id = payload.get("entity", {}).get("id")
        if not razorpay_payment_id:
            raise ValueError("Missing payment ID in payload")
        
        # Get or create payment
        payment = self.repository.get_by_razorpay_id(razorpay_payment_id)
        if not payment:
            # Create payment from payload
            payment = self._create_payment_from_payload(payload)
        
        # Update status to FAILED
        self.repository.update_payment_status(payment, PaymentStatus.FAILED)
        
        # Create payment attempt
        self._create_payment_attempt(payment, payload, PaymentStatus.FAILED)
        
        return payment
    
    def process_payment_authorized(self, payload: dict) -> Payment:
        """Process payment.authorized event."""
        razorpay_payment_id = payload.get("entity", {}).get("id")
        if not razorpay_payment_id:
            raise ValueError("Missing payment ID in payload")
        
        # Get or create payment
        payment = self.repository.get_by_razorpay_id(razorpay_payment_id)
        if not payment:
            # Create payment from payload
            payment = self._create_payment_from_payload(payload)
        
        # Update status to AUTHORIZED
        self.repository.update_payment_status(payment, PaymentStatus.AUTHORIZED)
        
        return payment
    
    def process_payment_captured(self, payload: dict) -> Payment:
        """Process payment.captured event."""
        razorpay_payment_id = payload.get("entity", {}).get("id")
        if not razorpay_payment_id:
            raise ValueError("Missing payment ID in payload")
        
        # Get or create payment
        payment = self.repository.get_by_razorpay_id(razorpay_payment_id)
        if not payment:
            # Create payment from payload
            payment = self._create_payment_from_payload(payload)
        
        # Update status to CAPTURED
        self.repository.update_payment_status(payment, PaymentStatus.CAPTURED)
        
        return payment
    
    def _create_payment_from_payload(self, payload: dict) -> Payment:
        """Create payment from Razorpay webhook payload."""
        entity = payload.get("entity", {})
        
        # Get or create merchant
        merchant = self.repository.get_or_create_merchant(
            external_id="default_merchant",  # Phase 1: single merchant
            name="Default Merchant"
        )
        
        # Get or create customer
        customer = None
        customer_info = entity.get("customer", {})
        if customer_info:
            customer = self.repository.get_or_create_customer(
                external_customer_id=customer_info.get("id"),
                email=customer_info.get("email"),
                phone=customer_info.get("contact")
            )
        
        # Create payment
        payment = self.repository.create_payment(
            razorpay_payment_id=entity.get("id"),
            razorpay_order_id=entity.get("order_id"),
            merchant_id=merchant.id,
            customer_id=customer.id if customer else None,
            amount_minor=int(entity.get("amount", 0)),  # Razorpay sends in paise
            currency=entity.get("currency", "INR"),
            method=entity.get("method")
        )
        
        return payment
    
    def _create_payment_attempt(
        self,
        payment: Payment,
        payload: dict,
        status: PaymentStatus
    ) -> PaymentAttempt:
        """Create a payment attempt."""
        entity = payload.get("entity", {})
        
        # Get next attempt number
        attempt_number = len(payment.attempts) + 1
        
        attempt = PaymentAttempt(
            payment_id=payment.id,
            attempt_number=attempt_number,
            status=status,
            failure_code=entity.get("error_code"),
            failure_description=entity.get("error_description"),
            method=entity.get("method"),
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )
        
        self.db.add(attempt)
        self.db.commit()
        self.db.refresh(attempt)
        
        logger.info(
            f"payment_attempt_created "
            f"payment_id={payment.id} "
            f"attempt_number={attempt_number}"
        )
        
        return attempt
    
    def get_payment(self, payment_id: str, merchant_id: Optional[Any] = None) -> Optional[Payment]:
        """Get payment by ID with attempts, optionally scoped to tenant."""
        return self.repository.get_by_id(payment_id, merchant_id=merchant_id)
    
    def list_payments(
        self,
        status: Optional[PaymentStatus] = None,
        merchant_id: Optional[Any] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[list[Payment], int]:
        """List payments with filters and tenant scoping."""
        return self.repository.list_payments(status, merchant_id=merchant_id, page=page, page_size=page_size)