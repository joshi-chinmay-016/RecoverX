"""Synthetic demo data seed script for Phase 2 Revenue Intelligence.

This script creates realistic payment/recovery data to demonstrate:
1. A low-value low-priority failure
2. A high-value high-probability recovery
3. A high-value low-probability recovery
4. Multiple failures caused by one category
5. A merchant with significant revenue at risk
"""

import sys
import os
from datetime import datetime, timedelta
from uuid import uuid4

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models.merchant import Merchant
from app.db.models.customer import Customer
from app.db.models.payment import Payment
from app.db.models.payment_attempt import PaymentAttempt
from app.db.models.recovery_case import RecoveryCase
from app.db.base import PaymentStatus, RecoveryCaseStatus


def create_demo_data():
    """Create synthetic demo data for Phase 2."""
    db = SessionLocal()
    
    try:
        print("Creating demo data...")
        
        # Create merchant
        merchant = db.query(Merchant).filter(Merchant.external_id == "demo_merchant").first()
        if not merchant:
            merchant = Merchant(
                name="Demo Merchant",
                external_id="demo_merchant",
                currency="INR"
            )
            db.add(merchant)
            db.commit()
            db.refresh(merchant)
            print(f"Created merchant: {merchant.id}")
        
        # Create customers
        customers = []
        for i in range(10):
            customer = db.query(Customer).filter(
                Customer.external_customer_id == f"demo_customer_{i}"
            ).first()
            if not customer:
                customer = Customer(
                    external_customer_id=f"demo_customer_{i}",
                    email=f"customer{i}@demo.com",
                    phone=f"+9198765432{i:02d}"
                )
                db.add(customer)
                db.commit()
                db.refresh(customer)
            customers.append(customer)
        
        print(f"Created {len(customers)} customers")
        
        # Scenario 1: High-value temporary bank failure (₹25,000) - HIGH priority
        payment1 = create_payment(
            db=db,
            merchant=merchant,
            customer=customers[0],
            amount=2500000,  # ₹25,000 in paise
            razorpay_id="pay_demo_001",
            status=PaymentStatus.FAILED,
            method="upi",
            failure_code="BANK_ERROR",
            failure_description="Bank processing error - temporary failure",
            retry_count=1,
            hours_ago=2
        )
        create_recovery_case(db, payment1)
        print(f"Scenario 1: High-value temporary failure (₹25,000) - {payment1.id}")
        
        # Scenario 2: Low-value insufficient funds (₹500) - LOW priority
        payment2 = create_payment(
            db=db,
            merchant=merchant,
            customer=customers[1],
            amount=50000,  # ₹500 in paise
            razorpay_id="pay_demo_002",
            status=PaymentStatus.FAILED,
            method="card",
            failure_code="BAD_REQUEST_ERROR",
            failure_description="Insufficient funds",
            retry_count=3,
            hours_ago=48
        )
        create_recovery_case(db, payment2)
        print(f"Scenario 2: Low-value insufficient funds (₹500) - {payment2.id}")
        
        # Scenario 3: High-value authentication failure (₹50,000) - MEDIUM priority
        payment3 = create_payment(
            db=db,
            merchant=merchant,
            customer=customers[2],
            amount=5000000,  # ₹50,000 in paise
            razorpay_id="pay_demo_003",
            status=PaymentStatus.FAILED,
            method="netbanking",
            failure_code="AUTHENTICATION_ERROR",
            failure_description="Authentication failed",
            retry_count=2,
            hours_ago=24
        )
        create_recovery_case(db, payment3)
        print(f"Scenario 3: High-value authentication failure (₹50,000) - {payment3.id}")
        
        # Scenario 4: Multiple network failures (same category)
        for i in range(4, 7):
            payment = create_payment(
                db=db,
                merchant=merchant,
                customer=customers[i],
                amount=random_amount(10000, 50000),  # ₹100-₹500
                razorpay_id=f"pay_demo_00{i}",
                status=PaymentStatus.FAILED,
                method="upi",
                failure_code="NETWORK_ERROR",
                failure_description="Network connectivity issue",
                retry_count=1,
                hours_ago=random_hours(1, 12)
            )
            create_recovery_case(db, payment)
            print(f"Scenario 4: Network failure #{i-3} (₹{payment.amount_minor/100:.0f}) - {payment.id}")
        
        # Scenario 5: Successful payments (for context)
        for i in range(7, 10):
            payment = create_payment(
                db=db,
                merchant=merchant,
                customer=customers[i],
                amount=random_amount(50000, 200000),  # ₹500-₹2,000
                razorpay_id=f"pay_demo_00{i}",
                status=PaymentStatus.CAPTURED,
                method="upi",
                failure_code=None,
                failure_description=None,
                retry_count=0,
                hours_ago=random_hours(24, 72)
            )
            print(f"Scenario 5: Successful payment #{i-6} (₹{payment.amount_minor/100:.0f}) - {payment.id}")
        
        # Additional failed payments for aggregate statistics
        for i in range(10, 15):
            payment = create_payment(
                db=db,
                merchant=merchant,
                customer=customers[i % len(customers)],
                amount=random_amount(5000, 100000),  # ₹50-₹1,000
                razorpay_id=f"pay_demo_0{i}",
                status=PaymentStatus.FAILED,
                method=random_method(),
                failure_code=random_failure_code(),
                failure_description=random_failure_description(),
                retry_count=random_retry_count(),
                hours_ago=random_hours(1, 168)
            )
            create_recovery_case(db, payment)
            print(f"Additional failed payment #{i-9} (₹{payment.amount_minor/100:.0f}) - {payment.id}")
        
        print("\nDemo data creation complete!")
        print(f"Total payments created: {db.query(Payment).count()}")
        print(f"Failed payments: {db.query(Payment).filter(Payment.status == PaymentStatus.FAILED).count()}")
        print(f"Recovery cases: {db.query(RecoveryCase).count()}")
        
    except Exception as e:
        print(f"Error creating demo data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def create_payment(
    db: Session,
    merchant: Merchant,
    customer: Customer,
    amount: int,
    razorpay_id: str,
    status: PaymentStatus,
    method: str,
    failure_code: str,
    failure_description: str,
    retry_count: int,
    hours_ago: int
) -> Payment:
    """Create a payment with attempts."""
    created_at = datetime.utcnow() - timedelta(hours=hours_ago)
    
    payment = Payment(
        razorpay_payment_id=razorpay_id,
        razorpay_order_id=f"order_demo_{razorpay_id}",
        merchant_id=merchant.id,
        customer_id=customer.id,
        amount_minor=amount,
        currency="INR",
        status=status,
        method=method,
        failure_code=failure_code,
        failure_description=failure_description,
        created_at=created_at,
        updated_at=created_at
    )
    
    db.add(payment)
    db.commit()
    db.refresh(payment)
    
    # Create payment attempts
    if retry_count > 0:
        for i in range(retry_count):
            attempt = PaymentAttempt(
                payment_id=payment.id,
                attempt_number=i + 1,
                status=status,
                failure_code=failure_code,
                failure_description=failure_description,
                method=method,
                started_at=created_at + timedelta(minutes=i * 10),
                completed_at=created_at + timedelta(minutes=i * 10 + 2)
            )
            db.add(attempt)
    else:
        # Single attempt for successful payments
        attempt = PaymentAttempt(
            payment_id=payment.id,
            attempt_number=1,
            status=status,
            method=method,
            started_at=created_at,
            completed_at=created_at + timedelta(minutes=1)
        )
        db.add(attempt)
    
    db.commit()
    return payment


def create_recovery_case(db: Session, payment: Payment) -> RecoveryCase:
    """Create a recovery case for a failed payment."""
    recovery_case = RecoveryCase(
        payment_id=payment.id,
        status=RecoveryCaseStatus.OPEN,
        amount_at_risk_minor=payment.amount_minor
    )
    db.add(recovery_case)
    db.commit()
    return recovery_case


def random_amount(min_paise: int, max_paise: int) -> int:
    """Generate random amount in paise."""
    import random
    return random.randint(min_paise, max_paise)


def random_method() -> str:
    """Generate random payment method."""
    import random
    return random.choice(["upi", "card", "netbanking", "wallet"])


def random_failure_code() -> str:
    """Generate random failure code."""
    import random
    return random.choice([
        "BAD_REQUEST_ERROR",
        "GATEWAY_ERROR",
        "NETWORK_ERROR",
        "AUTHENTICATION_ERROR",
        "TIMEOUT_ERROR",
        "LIMIT_ERROR"
    ])


def random_failure_description() -> str:
    """Generate random failure description."""
    import random
    return random.choice([
        "Insufficient funds in account",
        "Bank processing error",
        "Network connectivity issue",
        "Authentication failed",
        "Request timeout",
        "Transaction limit exceeded"
    ])


def random_retry_count() -> int:
    """Generate random retry count."""
    import random
    return random.randint(1, 3)


def random_hours(min_hours: int, max_hours: int) -> int:
    """Generate random hours ago."""
    import random
    return random.randint(min_hours, max_hours)


if __name__ == "__main__":
    create_demo_data()
