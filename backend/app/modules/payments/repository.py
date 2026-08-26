from typing import Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.db.models.payment import Payment
from app.db.models.customer import Customer
from app.db.models.merchant import Merchant
from app.db.base import PaymentStatus
from app.core.logging import logger


class PaymentRepository:
    """Repository for payment-related database operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_razorpay_id(self, razorpay_payment_id: str) -> Optional[Payment]:
        """Get payment by Razorpay payment ID."""
        return self.db.query(Payment).filter(
            Payment.razorpay_payment_id == razorpay_payment_id
        ).first()
    
    def get_by_id(self, payment_id: str, merchant_id: Optional[Any] = None) -> Optional[Payment]:
        """Get payment by internal ID, optionally scoped to tenant."""
        query = self.db.query(Payment).filter(Payment.id == payment_id)
        if merchant_id is not None:
            query = query.filter(Payment.merchant_id == merchant_id)
        return query.first()

    def create_payment(
        self,
        razorpay_payment_id: str,
        razorpay_order_id: Optional[str],
        merchant_id: str,
        customer_id: Optional[str],
        amount_minor: int,
        currency: str,
        method: Optional[str] = None
    ) -> Payment:
        """Create a new payment."""
        payment = Payment(
            razorpay_payment_id=razorpay_payment_id,
            razorpay_order_id=razorpay_order_id,
            merchant_id=merchant_id,
            customer_id=customer_id,
            amount_minor=amount_minor,
            currency=currency or "INR",
            method=method,
            status=PaymentStatus.CREATED
        )
        
        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)
        
        logger.info(f"payment_created razorpay_payment_id={razorpay_payment_id}")
        return payment
    
    def update_payment_status(self, payment: Payment, new_status: PaymentStatus) -> bool:
        """Update payment status using state transition logic."""
        if payment.transition_to(new_status):
            self.db.commit()
            logger.info(
                f"payment_status_updated "
                f"razorpay_payment_id={payment.razorpay_payment_id} "
                f"old_status={payment.status} "
                f"new_status={new_status}"
            )
            return True
        else:
            logger.warning(
                f"invalid_status_transition "
                f"razorpay_payment_id={payment.razorpay_payment_id} "
                f"current_status={payment.status} "
                f"requested_status={new_status}"
            )
            return False
    
    def list_payments(
        self,
        status: Optional[PaymentStatus] = None,
        merchant_id: Optional[Any] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[list[Payment], int]:
        """List payments with filters, tenant isolation, and pagination."""
        query = self.db.query(Payment)
        
        if merchant_id is not None:
            query = query.filter(Payment.merchant_id == merchant_id)

        if status:
            query = query.filter(Payment.status == status)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        payments = query.order_by(Payment.created_at.desc()).offset(offset).limit(page_size).all()
        
        return payments, total
    
    def get_or_create_merchant(self, external_id: str, name: str, currency: str = "INR") -> Merchant:
        """Get existing merchant or create new one."""
        merchant = self.db.query(Merchant).filter(
            Merchant.external_id == external_id
        ).first()
        
        if not merchant:
            merchant = Merchant(
                external_id=external_id,
                name=name,
                currency=currency
            )
            self.db.add(merchant)
            self.db.commit()
            self.db.refresh(merchant)
            logger.info(f"merchant_created external_id={external_id}")
        
        return merchant
    
    def get_or_create_customer(
        self,
        external_customer_id: str,
        email: Optional[str] = None,
        phone: Optional[str] = None
    ) -> Customer:
        """Get existing customer or create new one."""
        customer = self.db.query(Customer).filter(
            Customer.external_customer_id == external_customer_id
        ).first()
        
        if not customer:
            customer = Customer(
                external_customer_id=external_customer_id,
                email=email,
                phone=phone
            )
            self.db.add(customer)
            self.db.commit()
            self.db.refresh(customer)
            logger.info(f"customer_created external_customer_id={external_customer_id}")
        
        return customer