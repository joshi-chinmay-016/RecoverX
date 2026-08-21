"""
Seed data script for development/testing.

Generates:
- 1 merchant
- 20 customers
- 50 payments (mixed statuses)
- Multiple payment attempts
- Failed payments with recovery cases
- Successful payments
"""

import sys
import os
import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import create_engine

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.db.session import SessionLocal
from app.db.models.merchant import Merchant
from app.db.models.customer import Customer
from app.db.models.payment import Payment
from app.db.models.payment_attempt import PaymentAttempt
from app.db.models.recovery_case import RecoveryCase
from app.db.base import PaymentStatus, RecoveryCaseStatus


def seed_merchant(db: Session) -> Merchant:
    """Create a development merchant."""
    merchant = Merchant(
        id=uuid.uuid4(),
        name="Development Merchant",
        external_id="dev_merchant_001",
        currency="INR"
    )
    db.add(merchant)
    db.commit()
    db.refresh(merchant)
    print(f"✓ Created merchant: {merchant.name}")
    return merchant


def seed_customers(db: Session, count: int = 20) -> list[Customer]:
    """Create development customers."""
    customers = []
    for i in range(count):
        customer = Customer(
            id=uuid.uuid4(),
            external_customer_id=f"cust_{i:04d}",
            email=f"customer{i}@example.com",
            phone=f"987654321{i%10}"
        )
        customers.append(customer)
        db.add(customer)
    
    db.commit()
    print(f"✓ Created {count} customers")
    return customers


def seed_payments(
    db: Session,
    merchant: Merchant,
    customers: list[Customer],
    count: int = 50
) -> list[Payment]:
    """Create development payments with mixed statuses."""
    payments = []
    statuses = [
        PaymentStatus.CREATED,
        PaymentStatus.AUTHORIZED,
        PaymentStatus.CAPTURED,
        PaymentStatus.FAILED
    ]
    
    for i in range(count):
        customer = customers[i % len(customers)]
        status = statuses[i % len(statuses)]
        
        payment = Payment(
            id=uuid.uuid4(),
            razorpay_payment_id=f"pay_{i:04d}",
            razorpay_order_id=f"order_{i:04d}" if i % 2 == 0 else None,
            merchant_id=merchant.id,
            customer_id=customer.id,
            amount_minor=1000 + (i * 100),  # Varying amounts
            currency="INR",
            status=status,
            method="upi" if i % 3 == 0 else "card" if i % 3 == 1 else "netbanking",
            failure_code="BAD_REQUEST_ERROR" if status == PaymentStatus.FAILED else None,
            failure_description="Payment failed" if status == PaymentStatus.FAILED else None
        )
        payments.append(payment)
        db.add(payment)
    
    db.commit()
    print(f"✓ Created {count} payments")
    return payments


def seed_payment_attempts(db: Session, payments: list[Payment]) -> list[PaymentAttempt]:
    """Create payment attempts for failed payments."""
    attempts = []
    
    for payment in payments:
        if payment.status in [PaymentStatus.FAILED, PaymentStatus.CAPTURED]:
            # Create 1-3 attempts per payment
            num_attempts = 1 if payment.status == PaymentStatus.CAPTURED else 2
            
            for attempt_num in range(1, num_attempts + 1):
                attempt = PaymentAttempt(
                    id=uuid.uuid4(),
                    payment_id=payment.id,
                    attempt_number=attempt_num,
                    status=payment.status,
                    failure_code=payment.failure_code,
                    failure_description=payment.failure_description,
                    method=payment.method,
                    started_at=datetime.utcnow() - timedelta(minutes=attempt_num),
                    completed_at=datetime.utcnow() - timedelta(minutes=attempt_num - 1)
                )
                attempts.append(attempt)
                db.add(attempt)
    
    db.commit()
    print(f"✓ Created {len(attempts)} payment attempts")
    return attempts


def seed_recovery_cases(db: Session, payments: list[Payment]) -> list[RecoveryCase]:
    """Create recovery cases for failed payments."""
    recovery_cases = []
    
    for payment in payments:
        if payment.status == PaymentStatus.FAILED:
            # Create recovery case for failed payments
            recovery_case = RecoveryCase(
                id=uuid.uuid4(),
                payment_id=payment.id,
                status=RecoveryCaseStatus.OPEN,
                amount_at_risk_minor=payment.amount_minor
            )
            recovery_cases.append(recovery_case)
            db.add(recovery_case)
    
    db.commit()
    print(f"✓ Created {len(recovery_cases)} recovery cases")
    return recovery_cases


def main():
    """Main seed function."""
    print("🌱 Starting seed data generation...")
    
    db = SessionLocal()
    try:
        # Clear existing data (optional - comment out if you want to preserve data)
        print("Clearing existing data...")
        db.query(RecoveryCase).delete()
        db.query(PaymentAttempt).delete()
        db.query(Payment).delete()
        db.query(Customer).delete()
        db.query(Merchant).delete()
        db.commit()
        
        # Seed data
        merchant = seed_merchant(db)
        customers = seed_customers(db, count=20)
        payments = seed_payments(db, merchant, customers, count=50)
        seed_payment_attempts(db, payments)
        seed_recovery_cases(db, payments)
        
        print("\n✅ Seed data generation completed successfully!")
        print(f"   - 1 merchant")
        print(f"   - {len(customers)} customers")
        print(f"   - {len(payments)} payments")
        print(f"   - Recovery cases for failed payments")
        
    except Exception as e:
        print(f"❌ Error during seed data generation: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()