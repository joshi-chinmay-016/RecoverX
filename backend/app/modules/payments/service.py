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
    
    @staticmethod
    def _extract_payment_entity(payload: dict) -> dict:
        """Safely extract Razorpay payment entity dictionary from various payload structures."""
        if not isinstance(payload, dict):
            return {}
        
        # 1. Standard Razorpay Webhook format: payload.payload.payment.entity
        if "payload" in payload and isinstance(payload["payload"], dict):
            payment_wrapper = payload["payload"].get("payment", {})
            if isinstance(payment_wrapper, dict) and "entity" in payment_wrapper and isinstance(payment_wrapper["entity"], dict):
                return payment_wrapper["entity"]
                
        # 2. Wrapped payment format: payload.payment.entity
        if "payment" in payload and isinstance(payload["payment"], dict):
            entity = payload["payment"].get("entity", {})
            if isinstance(entity, dict):
                return entity

        # 3. Direct entity if dictionary: payload.entity
        entity = payload.get("entity")
        if isinstance(entity, dict):
            return entity

        # 4. Top-level dictionary if it is already a payment entity
        if "id" in payload and str(payload.get("id", "")).startswith("pay_"):
            return payload

        return {}

    def process_payment_failed(self, payload: dict) -> Payment:
        """Process payment.failed event."""
        entity = self._extract_payment_entity(payload)
        razorpay_payment_id = entity.get("id")
        if not razorpay_payment_id:
            logger.error(f"missing_payment_id_in_payload payload_keys={list(payload.keys()) if isinstance(payload, dict) else 'non-dict'}")
            raise ValueError("Missing payment ID in payload")
        
        logger.info(f"processing_payment_failed razorpay_payment_id={razorpay_payment_id} amount={entity.get('amount')}")

        # Get or create payment
        payment = self.repository.get_by_razorpay_id(razorpay_payment_id)
        if not payment:
            # Create payment from payload
            payment = self._create_payment_from_payload(payload)
        else:
            # Update status to FAILED
            self.repository.update_payment_status(payment, PaymentStatus.FAILED)
        
        # Create payment attempt
        self._create_payment_attempt(payment, payload, PaymentStatus.FAILED)
        
        return payment
    
    def process_payment_authorized(self, payload: dict) -> Payment:
        """Process payment.authorized event."""
        entity = self._extract_payment_entity(payload)
        razorpay_payment_id = entity.get("id")
        if not razorpay_payment_id:
            raise ValueError("Missing payment ID in payload")
        
        # Get or create payment
        payment = self.repository.get_by_razorpay_id(razorpay_payment_id)
        if not payment:
            # Create payment from payload
            payment = self._create_payment_from_payload(payload)
        else:
            # Update status to AUTHORIZED
            self.repository.update_payment_status(payment, PaymentStatus.AUTHORIZED)
        
        return payment
    
    def process_payment_captured(self, payload: dict) -> Payment:
        """Process payment.captured event."""
        entity = self._extract_payment_entity(payload)
        razorpay_payment_id = entity.get("id")
        if not razorpay_payment_id:
            raise ValueError("Missing payment ID in payload")
        
        # Get or create payment
        payment = self.repository.get_by_razorpay_id(razorpay_payment_id)
        if not payment:
            # Create payment from payload
            payment = self._create_payment_from_payload(payload)
        else:
            # Update status to CAPTURED
            self.repository.update_payment_status(payment, PaymentStatus.CAPTURED)
        
        return payment
    
    def _create_payment_from_payload(self, payload: dict) -> Payment:
        """Create payment from Razorpay webhook payload."""
        entity = self._extract_payment_entity(payload)
        
        # Get or create primary merchant so data appears on demo tenant workspace
        merchant = self.repository.get_or_create_merchant(
            external_id="demo_merchant_agent",
            name="Demo Merchant Agent"
        )
        
        # Extract customer info from top-level entity fields or nested customer object
        customer_email = entity.get("email")
        customer_phone = entity.get("contact")
        customer_id_val = entity.get("customer_id")
        
        if isinstance(entity.get("customer"), dict):
            customer_email = customer_email or entity["customer"].get("email")
            customer_phone = customer_phone or entity["customer"].get("contact")
            customer_id_val = customer_id_val or entity["customer"].get("id")
            
        customer = None
        if customer_id_val or customer_email or customer_phone:
            ext_cust_id = customer_id_val or f"cust_{customer_email or customer_phone or entity.get('id')}"
            customer = self.repository.get_or_create_customer(
                external_customer_id=ext_cust_id,
                email=customer_email,
                phone=customer_phone
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
        
        # Align initial status if payload indicates failure or capture
        status_str = str(entity.get("status", "")).lower()
        event_name = str(payload.get("event", "")).lower()
        if status_str == "failed" or event_name == "payment.failed":
            self.repository.update_payment_status(payment, PaymentStatus.FAILED)
        elif status_str == "captured" or event_name == "payment.captured":
            self.repository.update_payment_status(payment, PaymentStatus.CAPTURED)
        elif status_str == "authorized" or event_name == "payment.authorized":
            self.repository.update_payment_status(payment, PaymentStatus.AUTHORIZED)

        return payment
    
    def _create_payment_attempt(
        self,
        payment: Payment,
        payload: dict,
        status: PaymentStatus
    ) -> PaymentAttempt:
        """Create a payment attempt."""
        entity = self._extract_payment_entity(payload)
        
        # Get next attempt number
        attempt_number = len(payment.attempts) + 1
        
        attempt = PaymentAttempt(
            payment_id=payment.id,
            attempt_number=attempt_number,
            status=status,
            failure_code=entity.get("error_code") or entity.get("error_reason") or entity.get("error_source"),
            failure_description=entity.get("error_description") or entity.get("description"),
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
            f"attempt_number={attempt_number} "
            f"failure_code={attempt.failure_code}"
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