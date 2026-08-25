"""Seed script for Phase 3 Agent Demo Scenarios.

Creates deterministic demo scenarios for testing the AI Recovery Agent:
1. Transient Bank Failure - High value, recoverable
2. Insufficient Funds - Low value, alternate payment method
3. Repeated Failure - Multiple retries, manual review
4. Low-Value Opportunity - Low priority
5. Policy Block - Retry limit exceeded
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models.merchant import Merchant
from app.db.models.customer import Customer
from app.db.models.payment import Payment
from app.db.models.payment_attempt import PaymentAttempt
from app.db.models.recovery_case import RecoveryCase
from app.db.models.revenue_intelligence import RevenueIntelligenceResult
from app.db.base import PaymentStatus, RecoveryCaseStatus
from app.intelligence.schemas import PriorityLevel, FailureCategory
import uuid


def create_merchant(db: Session, name: str, external_id: str) -> Merchant:
    """Create a merchant for demo."""
    merchant = db.query(Merchant).filter(Merchant.external_id == external_id).first()
    if merchant:
        return merchant
    
    merchant = Merchant(
        name=name,
        external_id=external_id,
        currency="INR",
    )
    db.add(merchant)
    db.commit()
    db.refresh(merchant)
    return merchant


def create_customer(db: Session, email: str) -> Customer:
    """Create a customer for demo."""
    customer = db.query(Customer).filter(Customer.email == email).first()
    if customer:
        return customer
    
    customer = Customer(
        external_customer_id=f"cust_{uuid.uuid4().hex[:8]}",
        email=email,
        phone="+919876543210",
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


def create_payment(
    db: Session,
    merchant_id: str,
    customer_id: str,
    amount_minor: int,
    failure_code: str,
    failure_description: str,
    retry_count: int = 0,
) -> Payment:
    """Create a failed payment for demo."""
    payment = Payment(
        merchant_id=merchant_id,
        customer_id=customer_id,
        razorpay_payment_id=f"pay_demo_{uuid.uuid4().hex[:12]}",
        amount_minor=amount_minor,
        currency="INR",
        method="upi",
        status=PaymentStatus.FAILED,
        failure_code=failure_code,
        failure_description=failure_description,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    
    # Create payment attempts
    for i in range(retry_count + 1):
        attempt = PaymentAttempt(
            payment_id=payment.id,
            attempt_number=i + 1,
            status=PaymentStatus.FAILED,
            method="upi",
            failure_code=failure_code,
            failure_description=failure_description,
            started_at=datetime.now(timezone.utc) - timedelta(hours=retry_count - i),
            completed_at=datetime.now(timezone.utc) - timedelta(hours=retry_count - i) + timedelta(minutes=5),
        )
        db.add(attempt)
    
    db.commit()
    return payment


def create_recovery_case(db: Session, payment: Payment) -> RecoveryCase:
    """Create a recovery case for demo."""
    recovery_case = db.query(RecoveryCase).filter(
        RecoveryCase.payment_id == payment.id
    ).first()
    
    if recovery_case:
        return recovery_case
    
    recovery_case = RecoveryCase(
        payment_id=payment.id,
        amount_at_risk_minor=payment.amount_minor,
        status=RecoveryCaseStatus.OPEN,
    )
    db.add(recovery_case)
    db.commit()
    db.refresh(recovery_case)
    return recovery_case


def create_intelligence_result(
    db: Session,
    payment_id: uuid.UUID,
    recovery_case_id: uuid.UUID,
    failure_category: FailureCategory,
    recovery_probability: float,
    opportunity_score: float,
    priority: PriorityLevel,
    recommended_intervention: str,
) -> RevenueIntelligenceResult:
    """Create intelligence result for demo."""
    intelligence = db.query(RevenueIntelligenceResult).filter(
        RevenueIntelligenceResult.payment_id == payment_id
    ).first()
    
    if intelligence:
        return intelligence
    
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    revenue_at_risk = payment.amount_minor if payment else 0
    estimated_recoverable = int(revenue_at_risk * recovery_probability)
    
    intelligence = RevenueIntelligenceResult(
        payment_id=payment_id,
        recovery_case_id=recovery_case_id,
        failure_category=failure_category,
        failure_reason="Demo failure",
        revenue_at_risk=revenue_at_risk,
        recovery_probability=recovery_probability,
        estimated_recoverable_revenue=estimated_recoverable,
        opportunity_score=opportunity_score,
        priority=priority,
        recommended_intervention=recommended_intervention,
        intervention_reason="Automated recovery opportunity identified",
        confidence=0.85,
        explanation="Multi-factor revenue scoring based on merchant telemetry and gateway failure codes",
        factors=[
            {"factor_name": "FAILURE_SEVERITY", "impact": 20, "description": "Temporary gateway outage"},
            {"factor_name": "AMOUNT_WEIGHT", "impact": 15, "description": "High value payment"},
        ],
        model_version="rules-v1",
    )
    
    db.add(intelligence)
    db.commit()
    db.refresh(intelligence)
    return intelligence


def seed_scenario_1_transient_bank_failure(db: Session, merchant: Merchant, customer: Customer):
    """Scenario 1: Transient Bank Failure - High value, recoverable."""
    print("Creating Scenario 1: Transient Bank Failure...")
    
    payment = create_payment(
        db,
        merchant_id=merchant.id,
        customer_id=customer.id,
        amount_minor=2500000,  # ₹25,000
        failure_code="BANK_ERROR",
        failure_description="Bank processing error - temporary failure",
        retry_count=0,
    )
    
    recovery_case = create_recovery_case(db, payment)
    
    intelligence = create_intelligence_result(
        db,
        payment_id=payment.id,
        recovery_case_id=recovery_case.id,
        failure_category=FailureCategory.BANK_FAILURE,
        recovery_probability=0.78,
        opportunity_score=82.0,
        priority=PriorityLevel.HIGH,
        recommended_intervention="RETRY_PAYMENT",
    )
    
    print(f"  Created payment: {payment.id}")
    print(f"  Created intelligence: {intelligence.id}")
    return intelligence


def seed_scenario_2_insufficient_funds(db: Session, merchant: Merchant, customer: Customer):
    """Scenario 2: Insufficient Funds - Low value, alternate payment method."""
    print("Creating Scenario 2: Insufficient Funds...")
    
    payment = create_payment(
        db,
        merchant_id=merchant.id,
        customer_id=customer.id,
        amount_minor=80000,  # ₹800
        failure_code="BAD_REQUEST_ERROR",
        failure_description="Insufficient funds in account",
        retry_count=0,
    )
    
    recovery_case = create_recovery_case(db, payment)
    
    intelligence = create_intelligence_result(
        db,
        payment_id=payment.id,
        recovery_case_id=recovery_case.id,
        failure_category=FailureCategory.INSUFFICIENT_FUNDS,
        recovery_probability=0.35,
        opportunity_score=45.0,
        priority=PriorityLevel.MEDIUM,
        recommended_intervention="REQUEST_ALTERNATE_PAYMENT_METHOD",
    )
    
    print(f"  Created payment: {payment.id}")
    print(f"  Created intelligence: {intelligence.id}")
    return intelligence


def seed_scenario_3_repeated_failure(db: Session, merchant: Merchant, customer: Customer):
    """Scenario 3: Repeated Failure - Multiple retries, manual review."""
    print("Creating Scenario 3: Repeated Failure...")
    
    payment = create_payment(
        db,
        merchant_id=merchant.id,
        customer_id=customer.id,
        amount_minor=2000000,  # ₹20,000
        failure_code="NETWORK_ERROR",
        failure_description="Network connectivity issue",
        retry_count=3,
    )
    
    recovery_case = create_recovery_case(db, payment)
    
    intelligence = create_intelligence_result(
        db,
        payment_id=payment.id,
        recovery_case_id=recovery_case.id,
        failure_category=FailureCategory.NETWORK_FAILURE,
        recovery_probability=0.25,
        opportunity_score=38.0,
        priority=PriorityLevel.MEDIUM,
        recommended_intervention="MANUAL_REVIEW",
    )
    
    print(f"  Created payment: {payment.id}")
    print(f"  Created intelligence: {intelligence.id}")
    return intelligence


def seed_scenario_4_low_value(db: Session, merchant: Merchant, customer: Customer):
    """Scenario 4: Low-Value Opportunity - Low priority."""
    print("Creating Scenario 4: Low-Value Opportunity...")
    
    payment = create_payment(
        db,
        merchant_id=merchant.id,
        customer_id=customer.id,
        amount_minor=30000,  # ₹300
        failure_code="TEMPORARY_ERROR",
        failure_description="Temporary processing error",
        retry_count=0,
    )
    
    recovery_case = create_recovery_case(db, payment)
    
    intelligence = create_intelligence_result(
        db,
        payment_id=payment.id,
        recovery_case_id=recovery_case.id,
        failure_category=FailureCategory.TEMPORARY_FAILURE,
        recovery_probability=0.55,
        opportunity_score=35.0,
        priority=PriorityLevel.LOW,
        recommended_intervention="WAIT_AND_RETRY",
    )
    
    print(f"  Created payment: {payment.id}")
    print(f"  Created intelligence: {intelligence.id}")
    return intelligence


def seed_scenario_5_policy_block(db: Session, merchant: Merchant, customer: Customer):
    """Scenario 5: Policy Block - Retry limit exceeded."""
    print("Creating Scenario 5: Policy Block...")
    
    payment = create_payment(
        db,
        merchant_id=merchant.id,
        customer_id=customer.id,
        amount_minor=1500000,  # ₹15,000
        failure_code="BANK_ERROR",
        failure_description="Bank processing error",
        retry_count=4,
    )
    
    recovery_case = create_recovery_case(db, payment)
    
    intelligence = create_intelligence_result(
        db,
        payment_id=payment.id,
        recovery_case_id=recovery_case.id,
        failure_category=FailureCategory.BANK_FAILURE,
        recovery_probability=0.65,
        opportunity_score=75.0,
        priority=PriorityLevel.HIGH,
        recommended_intervention="RETRY_PAYMENT",
    )
    
    print(f"  Created payment: {payment.id}")
    print(f"  Created intelligence: {intelligence.id}")
    return intelligence


def main():
    """Seed demo scenarios for Phase 3 Agent."""
    db = SessionLocal()
    
    try:
        print("Seeding Phase 3 Agent Demo Scenarios...")
        
        merchant = create_merchant(db, "Demo Merchant Agent", "demo_merchant_agent")
        customer = create_customer(db, "demo@recoverx.ai")
        
        scenario1 = seed_scenario_1_transient_bank_failure(db, merchant, customer)
        scenario2 = seed_scenario_2_insufficient_funds(db, merchant, customer)
        scenario3 = seed_scenario_3_repeated_failure(db, merchant, customer)
        scenario4 = seed_scenario_4_low_value(db, merchant, customer)
        scenario5 = seed_scenario_5_policy_block(db, merchant, customer)
        
        print("\n✅ Demo scenarios seeded successfully!")
        print(f"  Scenario 1 (Transient Bank Failure): {scenario1.id}")
        print(f"  Scenario 2 (Insufficient Funds): {scenario2.id}")
        print(f"  Scenario 3 (Repeated Failure): {scenario3.id}")
        print(f"  Scenario 4 (Low-Value): {scenario4.id}")
        print(f"  Scenario 5 (Policy Block): {scenario5.id}")
        
    except Exception as e:
        print(f"❌ Error seeding demo scenarios: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
