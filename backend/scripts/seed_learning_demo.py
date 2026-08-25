"""Seed script for Phase 5 Adaptive Recovery Intelligence & Learning.

Populates deterministic historical recovery attempts and outcomes across merchants and failure categories
to demonstrate Beta-Binomial Bayesian probability smoothing, strategy ranking, and calibration metrics.
"""

import sys
import os
import uuid
import random
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.base import ActionStatus, PaymentStatus
from app.db.models.merchant import Merchant
from app.db.models.customer import Customer
from app.db.models.payment import Payment
from app.db.models.learning_outcome import LearningOutcomeRecord
from app.intelligence.schemas import FailureCategory
from app.agent.schemas import ActionType
from app.learning.service import LearningService


def seed_learning_dataset(db: Session):
    """Seed comprehensive synthetic recovery outcome records."""
    print("Seeding Phase 5 Adaptive Learning Historical Dataset...")

    # Ensure demo merchant exists
    merchant = db.query(Merchant).filter(Merchant.external_id == "demo_merchant_agent").first()
    if not merchant:
        merchant = Merchant(
            name="Demo Merchant Agent",
            external_id="demo_merchant_agent",
            currency="INR",
        )
        db.add(merchant)
        db.commit()
        db.refresh(merchant)

    # Clean existing learning records for idempotent re-seeding
    db.query(LearningOutcomeRecord).filter(LearningOutcomeRecord.merchant_id == merchant.id).delete()
    db.commit()

    random.seed(42)  # Deterministic seed

    # Benchmark configurations: (category, action_type, count, success_rate, amount_range)
    scenarios = [
        # 1. Bank failure: Retry performs very well (62%)
        (FailureCategory.BANK_FAILURE, ActionType.RETRY_PAYMENT, 280, 0.62, (100000, 2500000)),
        (FailureCategory.BANK_FAILURE, ActionType.WAIT_AND_RETRY, 148, 0.55, (50000, 1500000)),
        (FailureCategory.BANK_FAILURE, ActionType.SEND_PAYMENT_REMINDER, 45, 0.18, (20000, 500000)),
        
        # 2. Temporary glitch: Immediate wait & retry is highly effective (83%)
        (FailureCategory.TEMPORARY_FAILURE, ActionType.WAIT_AND_RETRY, 220, 0.85, (50000, 3000000)),
        (FailureCategory.TEMPORARY_FAILURE, ActionType.RETRY_PAYMENT, 130, 0.78, (50000, 2000000)),
        
        # 3. Insufficient funds: Customer alternate method prompt succeeds (58%), direct retry fails (14%)
        (FailureCategory.INSUFFICIENT_FUNDS, ActionType.REQUEST_ALTERNATE_PAYMENT_METHOD, 190, 0.60, (20000, 800000)),
        (FailureCategory.INSUFFICIENT_FUNDS, ActionType.SEND_PAYMENT_REMINDER, 90, 0.52, (10000, 400000)),
        (FailureCategory.INSUFFICIENT_FUNDS, ActionType.RETRY_PAYMENT, 70, 0.14, (30000, 500000)),
        
        # 4. Authentication failure: 3DS reauthentication prompt succeeds (70%)
        (FailureCategory.AUTHENTICATION_FAILURE, ActionType.REQUEST_REAUTHENTICATION, 160, 0.70, (50000, 1500000)),
        (FailureCategory.AUTHENTICATION_FAILURE, ActionType.RETRY_PAYMENT, 50, 0.22, (50000, 1000000)),
        
        # 5. Card expired: Direct retry fails (3%), card update prompt succeeds (56%)
        (FailureCategory.PAYMENT_METHOD_FAILURE, ActionType.REQUEST_ALTERNATE_PAYMENT_METHOD, 120, 0.58, (50000, 1200000)),
        (FailureCategory.PAYMENT_METHOD_FAILURE, ActionType.RETRY_PAYMENT, 70, 0.04, (50000, 1200000)),
        
        # 6. Limit exceeded: Manual review succeeds (45%)
        (FailureCategory.LIMIT_EXCEEDED, ActionType.MANUAL_REVIEW, 60, 0.45, (2500000, 10000000)),
        (FailureCategory.LIMIT_EXCEEDED, ActionType.RETRY_PAYMENT, 20, 0.05, (2500000, 5000000)),
    ]

    records_to_insert = []
    total_created = 0

    # Ensure a dummy payment exists for foreign key
    dummy_payment = db.query(Payment).filter(Payment.merchant_id == merchant.id).first()
    if not dummy_payment:
        dummy_payment = Payment(
            merchant_id=merchant.id,
            razorpay_payment_id=f"pay_seed_{uuid.uuid4().hex[:8]}",
            amount_minor=100000,
            currency="INR",
            method="upi",
            status=PaymentStatus.FAILED,
        )
        db.add(dummy_payment)
        db.commit()
        db.refresh(dummy_payment)

    for cat, action, count, success_rate, (min_amt, max_amt) in scenarios:
        for i in range(count):
            is_success = random.random() < success_rate
            days_ago = random.randint(1, 85)
            occurred_at = datetime.now(timezone.utc) - timedelta(days=days_ago, minutes=random.randint(0, 1440))
            
            outcome_status = ActionStatus.SUCCEEDED if is_success else ActionStatus.FAILED
            # Add small percentage of UNKNOWN and BLOCKED for realism
            if random.random() < 0.03:
                outcome_status = ActionStatus.UNKNOWN
            elif random.random() < 0.02:
                outcome_status = ActionStatus.BLOCKED

            record = LearningOutcomeRecord(
                merchant_id=merchant.id,
                payment_id=dummy_payment.id,
                failure_category=cat,
                action_type=action,
                amount_minor=random.randint(min_amt, max_amt),
                retry_count=random.choice([0, 1, 2]),
                payment_method=random.choice(["upi", "card", "netbanking"]),
                outcome_status=outcome_status,
                execution_latency_ms=random.randint(180, 450),
                occurred_at=occurred_at,
            )
            records_to_insert.append(record)
            total_created += 1

    db.bulk_save_objects(records_to_insert)
    db.commit()

    print(f"✓ Created {total_created} historical learning outcome records.")

    # Recompute and persist snapshot
    learning_service = LearningService(db)
    snapshot = learning_service.recompute_snapshot(merchant_id=merchant.id)
    print(f"✓ Recomputed learning snapshot: {snapshot.total_samples} samples, {round(snapshot.overall_recovery_rate * 100)}% overall yield, Brier score: {snapshot.brier_score}")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_learning_dataset(db)
    finally:
        db.close()
