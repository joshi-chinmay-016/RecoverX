"""RecoverX Phase 7: Deterministic Master Demo Reset & Seeder Script.

Usage:
    python scripts/reset_demo.py

Features:
- Completely idempotent and self-contained
- Establishes Primary Demo Merchant ("Demo Merchant Agent") & Secondary Merchant ("Acme Global Payments")
- Bootstraps Phase 6 Users (Admin, Operator, Analyst) with secure bcrypt hashes & RBAC memberships
- Establishes Phase 7 Named Demo Scenarios:
    * Scenario A: Successful Recovery (₹2,450, BANK_FAILURE, retry=0, Critical priority, auto-resolves on action execution)
    * Scenario B: Policy Block (₹8,900, TEMPORARY_FAILURE, retries=3, PolicyEngine blocks execution due to safety limit)
    * Scenario C: Provider Timeout (₹4,200, GATEWAY_TIMEOUT, Action in UNKNOWN state with reconciliation flow)
    * Scenario D: Cross-Tenant Isolation (Acme Global Payments private transaction)
- Populates rich Revenue Intelligence queue, Agent Run histories, Audit Trails, and Learning Outcome records.
"""

import sys
import os
import uuid
from datetime import datetime, timedelta

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.base import (
    PaymentStatus,
    RecoveryCaseStatus,
    ActionStatus,
    ExecutionAttemptStatus,
    AuditEventType,
    ActorType,
    UserRole,
)
from app.db.models.merchant import Merchant
from app.db.models.customer import Customer
from app.db.models.payment import Payment
from app.db.models.payment_attempt import PaymentAttempt
from app.db.models.recovery_case import RecoveryCase
from app.db.models.revenue_intelligence import RevenueIntelligenceResult
from app.db.models.recovery_action import RecoveryAction
from app.db.models.execution_attempt import ExecutionAttempt
from app.db.models.agent_run import AgentRun
from app.db.models.learning_outcome import LearningOutcomeRecord
from app.db.models.learning_model_snapshot import LearningModelSnapshot
from app.db.models.webhook_event import WebhookEvent
from app.db.models.audit_event import AuditEvent
from app.db.models.user import User
from app.db.models.merchant_membership import MerchantMembership
from app.auth.security import get_password_hash
from app.intelligence.schemas import FailureCategory, PriorityLevel
from app.agent.schemas import ActionType


def reset_and_seed_demo_environment():
    """Master deterministic reset and seeding function."""
    db: Session = SessionLocal()
    print("=" * 70)
    print(">>> RecoverX Phase 7: Initializing Deterministic Sandbox Environment")
    print("=" * 70)

    try:
        # 1. Clean existing demo data safely
        print("\n[1/6] Cleaning existing demo records...")
        db.query(LearningModelSnapshot).delete()
        db.query(LearningOutcomeRecord).delete()
        db.query(ExecutionAttempt).delete()
        db.query(RecoveryAction).delete()
        db.query(AgentRun).delete()
        db.query(RevenueIntelligenceResult).delete()
        db.query(RecoveryCase).delete()
        db.query(PaymentAttempt).delete()
        db.query(Payment).delete()
        db.query(WebhookEvent).delete()
        db.query(Customer).delete()
        db.query(AuditEvent).delete()
        db.query(MerchantMembership).delete()
        db.query(User).delete()
        db.query(Merchant).delete()
        db.commit()
        print("  [+] Database cleared of previous demo state.")

        # 2. Bootstrap Merchants
        print("\n[2/6] Seeding Multi-Tenant Merchants...")
        primary_merchant = Merchant(
            id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            name="Demo Merchant Agent",
            external_id="demo_merchant",
            currency="INR",
        )
        secondary_merchant = Merchant(
            id=uuid.UUID("87654321-4321-8765-4321-876543210987"),
            name="Acme Global Payments",
            external_id="acme_global",
            currency="INR",
        )
        db.add_all([primary_merchant, secondary_merchant])
        db.commit()
        print(f"  [+] Primary Merchant: {primary_merchant.name} ({primary_merchant.id})")
        print(f"  [+] Secondary Merchant: {secondary_merchant.name} ({secondary_merchant.id})")

        # 3. Bootstrap Users & RBAC Memberships
        print("\n[3/6] Bootstrapping Demo Users & RBAC Memberships...")
        admin_user = User(
            id=uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
            email="admin@recoverx.io",
            full_name="Sarah Connor (Admin)",
            password_hash=get_password_hash("Admin@RecoverX2026!"),
            is_active=True,
        )
        operator_user = User(
            id=uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
            email="operator@recoverx.io",
            full_name="Alex Vance (Recovery Operator)",
            password_hash=get_password_hash("Operator@RecoverX2026!"),
            is_active=True,
        )
        analyst_user = User(
            id=uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc"),
            email="analyst@recoverx.io",
            full_name="Gordon Freeman (Risk Analyst)",
            password_hash=get_password_hash("Analyst@RecoverX2026!"),
            is_active=True,
        )
        db.add_all([admin_user, operator_user, analyst_user])
        db.flush()

        # Memberships
        m1 = MerchantMembership(user_id=admin_user.id, merchant_id=primary_merchant.id, role=UserRole.ADMIN)
        m2 = MerchantMembership(user_id=admin_user.id, merchant_id=secondary_merchant.id, role=UserRole.ADMIN)
        m3 = MerchantMembership(user_id=operator_user.id, merchant_id=primary_merchant.id, role=UserRole.OPERATOR)
        m4 = MerchantMembership(user_id=analyst_user.id, merchant_id=primary_merchant.id, role=UserRole.ANALYST)
        db.add_all([m1, m2, m3, m4])
        db.commit()
        print("  [+] Admin:    admin@recoverx.io    (Password: Admin@RecoverX2026!) -> Full Access")
        print("  [+] Operator: operator@recoverx.io (Password: Operator@RecoverX2026!) -> Execution Ops")
        print("  [+] Analyst:  analyst@recoverx.io  (Password: Analyst@RecoverX2026!) -> Read Only")

        # 4. Bootstrap Customers
        print("\n[4/6] Seeding Customers...")
        customers = []
        for i in range(12):
            cust = Customer(
                id=uuid.uuid4(),
                external_customer_id=f"cust_rec_{i+1:03d}",
                email=f"customer_{i+1}@fintechdemo.in",
                phone=f"+9198765{i+1:05d}",
            )
            db.add(cust)
            customers.append(cust)
        db.commit()
        print(f"  [+] Seeded {len(customers)} verified customer entities.")

        # 5. Bootstrap Named Phase 7 Demo Scenarios
        print("\n[5/6] Generating Phase 7 Deterministic Demo Scenarios...")

        # -------------------------------------------------------------
        # Scenario A: Successful Recovery (INR 2,450, BANK_FAILURE, retry=0)
        # -------------------------------------------------------------
        pay_a = Payment(
            id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
            razorpay_payment_id="pay_demo_scenario_a_001",
            merchant_id=primary_merchant.id,
            customer_id=customers[0].id,
            amount_minor=245000,  # INR 2,450.00
            currency="INR",
            status=PaymentStatus.FAILED,
            method="upi",
            failure_code="BANK_ERROR",
            failure_description="Bank gateway timeout on NPCI rail",
            created_at=datetime.utcnow() - timedelta(minutes=25),
        )
        db.add(pay_a)
        db.flush()

        att_a = PaymentAttempt(
            payment_id=pay_a.id,
            attempt_number=1,
            status=PaymentStatus.FAILED,
            method="upi",
            failure_code="BANK_ERROR",
            failure_description="Bank gateway timeout on NPCI rail",
            started_at=datetime.utcnow() - timedelta(minutes=25),
            completed_at=datetime.utcnow() - timedelta(minutes=24),
        )
        case_a = RecoveryCase(
            id=uuid.UUID("a1111111-1111-1111-1111-111111111111"),
            payment_id=pay_a.id,
            status=RecoveryCaseStatus.OPEN,
            amount_at_risk_minor=245000,
            created_at=datetime.utcnow() - timedelta(minutes=24),
        )
        intel_a = RevenueIntelligenceResult(
            id=uuid.UUID("b1111111-1111-1111-1111-111111111111"),
            payment_id=pay_a.id,
            recovery_case_id=case_a.id,
            failure_category=FailureCategory.BANK_FAILURE,
            failure_reason="Transient core banking switch congestion",
            revenue_at_risk=245000,
            recovery_probability=0.78,
            estimated_recoverable_revenue=191100,
            opportunity_score=85.0,
            priority=PriorityLevel.CRITICAL,
            recommended_intervention="RETRY_PAYMENT",
            intervention_reason="Historically recoverable bank congestion failure with 0 previous retries",
            confidence=0.88,
            explanation="INR 2,450 transaction failed due to transient bank congestion. High historical recovery likelihood (78%) via immediate controlled retry.",
            factors=[
                {"factor": "CATEGORY_YIELD", "impact": "POSITIVE", "weight": 0.35, "description": "Bank failures exhibit 78% recovery rate"},
                {"factor": "RETRY_COUNT", "impact": "POSITIVE", "weight": 0.25, "description": "Zero previous retries attempted"},
                {"factor": "AMOUNT_VALUE", "impact": "POSITIVE", "weight": 0.20, "description": "High normalized revenue value (INR 2,450)"},
                {"factor": "TIME_DECAY", "impact": "POSITIVE", "weight": 0.20, "description": "Recent failure under 30 minutes old"},
            ],
            model_version="rules-v1",
            created_at=datetime.utcnow() - timedelta(minutes=23),
        )
        db.add_all([att_a, case_a, intel_a])
        print("  [+] [Scenario A] Successful Recovery Target: pay_demo_scenario_a_001 (INR 2,450, Critical, Score 85)")

        # -------------------------------------------------------------
        # Scenario B: Policy Safety Block (INR 8,900, Retries Exceeded = 3)
        # -------------------------------------------------------------
        pay_b = Payment(
            id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
            razorpay_payment_id="pay_demo_scenario_b_002",
            merchant_id=primary_merchant.id,
            customer_id=customers[1].id,
            amount_minor=890000,  # INR 8,900.00
            currency="INR",
            status=PaymentStatus.FAILED,
            method="card",
            failure_code="INSUFFICIENT_FUNDS",
            failure_description="Cardholder account balance insufficient",
            created_at=datetime.utcnow() - timedelta(hours=6),
        )
        db.add(pay_b)
        db.flush()

        # 3 previous failed attempts
        att_b1 = PaymentAttempt(payment_id=pay_b.id, attempt_number=1, status=PaymentStatus.FAILED, method="card", failure_code="INSUFFICIENT_FUNDS", started_at=datetime.utcnow() - timedelta(hours=6))
        att_b2 = PaymentAttempt(payment_id=pay_b.id, attempt_number=2, status=PaymentStatus.FAILED, method="card", failure_code="INSUFFICIENT_FUNDS", started_at=datetime.utcnow() - timedelta(hours=4))
        att_b3 = PaymentAttempt(payment_id=pay_b.id, attempt_number=3, status=PaymentStatus.FAILED, method="card", failure_code="INSUFFICIENT_FUNDS", started_at=datetime.utcnow() - timedelta(hours=2))

        case_b = RecoveryCase(
            id=uuid.UUID("a2222222-2222-2222-2222-222222222222"),
            payment_id=pay_b.id,
            status=RecoveryCaseStatus.OPEN,
            amount_at_risk_minor=890000,
            created_at=datetime.utcnow() - timedelta(hours=6),
        )
        intel_b = RevenueIntelligenceResult(
            id=uuid.UUID("b2222222-2222-2222-2222-222222222222"),
            payment_id=pay_b.id,
            recovery_case_id=case_b.id,
            failure_category=FailureCategory.TEMPORARY_FAILURE,
            failure_reason="Customer insufficient balance across repeated checks",
            revenue_at_risk=890000,
            recovery_probability=0.31,
            estimated_recoverable_revenue=275900,
            opportunity_score=52.0,
            priority=PriorityLevel.MEDIUM,
            recommended_intervention="CUSTOMER_NOTIFICATION",
            intervention_reason="Max retries reached; customer notification or balance reminder required",
            confidence=0.72,
            explanation="Payment has already undergone 3 failed attempts. Direct retries are disallowed by PolicyEngine.",
            factors=[
                {"factor": "RETRY_PENALTY", "impact": "NEGATIVE", "weight": -0.40, "description": "3 attempts already failed"},
                {"factor": "AMOUNT_VALUE", "impact": "POSITIVE", "weight": 0.30, "description": "High ticket size (INR 8,900)"},
            ],
            model_version="rules-v1",
            created_at=datetime.utcnow() - timedelta(hours=2),
        )
        db.add_all([att_b1, att_b2, att_b3, case_b, intel_b])
        print("  [+] [Scenario B] Policy Block Demo: pay_demo_scenario_b_002 (INR 8,900, 3 Retries, Policy BLOCK)")

        # -------------------------------------------------------------
        # Scenario C: Provider Timeout & UNKNOWN State Reconciliation
        # -------------------------------------------------------------
        pay_c = Payment(
            id=uuid.UUID("33333333-3333-3333-3333-333333333333"),
            razorpay_payment_id="pay_demo_scenario_c_003",
            merchant_id=primary_merchant.id,
            customer_id=customers[2].id,
            amount_minor=420000,  # INR 4,200.00
            currency="INR",
            status=PaymentStatus.FAILED,
            method="netbanking",
            failure_code="GATEWAY_TIMEOUT",
            failure_description="Acquiring host did not respond in 5000ms",
            created_at=datetime.utcnow() - timedelta(hours=1),
        )
        db.add(pay_c)
        db.flush()

        att_c = PaymentAttempt(payment_id=pay_c.id, attempt_number=1, status=PaymentStatus.FAILED, method="netbanking", failure_code="GATEWAY_TIMEOUT", started_at=datetime.utcnow() - timedelta(hours=1))
        case_c = RecoveryCase(
            id=uuid.UUID("a3333333-3333-3333-3333-333333333333"),
            payment_id=pay_c.id,
            status=RecoveryCaseStatus.OPEN,
            amount_at_risk_minor=420000,
            created_at=datetime.utcnow() - timedelta(hours=1),
        )
        intel_c = RevenueIntelligenceResult(
            id=uuid.UUID("b3333333-3333-3333-3333-333333333333"),
            payment_id=pay_c.id,
            recovery_case_id=case_c.id,
            failure_category=FailureCategory.NETWORK_FAILURE,
            failure_reason="Network socket timeout during gateway handshake",
            revenue_at_risk=420000,
            recovery_probability=0.65,
            estimated_recoverable_revenue=273000,
            opportunity_score=74.0,
            priority=PriorityLevel.HIGH,
            recommended_intervention="RETRY_PAYMENT",
            intervention_reason="Timeout during off-peak window; retry pending status confirmation",
            confidence=0.81,
            explanation="Gateway timed out without final debit confirmation. Requires reconciliation before new charge attempts.",
            factors=[
                {"factor": "CATEGORY_YIELD", "impact": "POSITIVE", "weight": 0.30, "description": "Network timeout recoverable once route clears"},
            ],
            model_version="rules-v1",
            created_at=datetime.utcnow() - timedelta(minutes=50),
        )
        db.add_all([att_c, case_c, intel_c])
        db.flush()

        # Create action in UNKNOWN state
        act_c = RecoveryAction(
            id=uuid.UUID("c3333333-3333-3333-3333-333333333333"),
            action_id="act_demo_timeout_c_003",
            opportunity_id=intel_c.id,
            payment_id=pay_c.id,
            merchant_id=primary_merchant.id,
            action_type=ActionType.RETRY_PAYMENT,
            status=ActionStatus.UNKNOWN,
            idempotency_key="idemp_demo_c_timeout_key_4200",
            execution_attempts_count=1,
            max_attempts=3,
            provider_reference="mock_rec_timeout_4200",
            last_error_code="GATEWAY_TIMEOUT",
            last_error_message="Provider timeout: Outcome unconfirmed. Blind retries disabled. Reconciliation required.",
            requested_at=datetime.utcnow() - timedelta(minutes=45),
            started_at=datetime.utcnow() - timedelta(minutes=45),
        )
        db.add(act_c)
        print("  [+] [Scenario C] Timeout / UNKNOWN Reconciliation: pay_demo_scenario_c_003 (INR 4,200, UNKNOWN Action)")

        # -------------------------------------------------------------
        # Scenario D: Cross-Tenant Isolation (Acme Global Payments)
        # -------------------------------------------------------------
        pay_d = Payment(
            id=uuid.UUID("44444444-4444-4444-4444-444444444444"),
            razorpay_payment_id="pay_acme_isolated_999",
            merchant_id=secondary_merchant.id,
            amount_minor=1500000,  # INR 15,000.00
            currency="INR",
            status=PaymentStatus.FAILED,
            method="card",
            failure_code="AUTHENTICATION_FAILED",
            failure_description="3D Secure OTP verification timeout",
            created_at=datetime.utcnow() - timedelta(hours=3),
        )
        db.add(pay_d)
        db.flush()

        case_d = RecoveryCase(
            id=uuid.UUID("a4444444-4444-4444-4444-444444444444"),
            payment_id=pay_d.id,
            status=RecoveryCaseStatus.OPEN,
            amount_at_risk_minor=1500000,
            created_at=datetime.utcnow() - timedelta(hours=3),
        )
        intel_d = RevenueIntelligenceResult(
            id=uuid.UUID("b4444444-4444-4444-4444-444444444444"),
            payment_id=pay_d.id,
            recovery_case_id=case_d.id,
            failure_category=FailureCategory.AUTHENTICATION_FAILURE,
            failure_reason="Customer 3DS auth timeout",
            revenue_at_risk=1500000,
            recovery_probability=0.45,
            estimated_recoverable_revenue=675000,
            opportunity_score=68.0,
            priority=PriorityLevel.HIGH,
            recommended_intervention="CUSTOMER_NOTIFICATION",
            intervention_reason="Prompt customer to retry with active OTP",
            confidence=0.79,
            explanation="Acme private payment entity.",
            factors=[],
            model_version="rules-v1",
            created_at=datetime.utcnow() - timedelta(hours=3),
        )
        db.add_all([case_d, intel_d])
        print("  [+] [Scenario D] Cross-Tenant Isolation: pay_acme_isolated_999 (Acme Global Payments)")

        # -------------------------------------------------------------
        # 6. Additional Realistic Payments & Queue Opportunities
        # -------------------------------------------------------------
        print("\n[6/6] Populating Queue Data, Learning History & Audit Events...")

        sample_cases = [
            ("pay_seed_004", 120000, "upi", "BANK_ERROR", FailureCategory.BANK_FAILURE, PriorityLevel.CRITICAL, 0.82, 88.0, ActionType.RETRY_PAYMENT),
            ("pay_seed_005", 350000, "card", "NETWORK_TIMEOUT", FailureCategory.NETWORK_FAILURE, PriorityLevel.HIGH, 0.71, 79.0, ActionType.RETRY_PAYMENT),
            ("pay_seed_006", 80000, "card", "BAD_REQUEST_ERROR", FailureCategory.PAYMENT_METHOD_FAILURE, PriorityLevel.LOW, 0.15, 22.0, ActionType.REQUEST_ALTERNATE_PAYMENT_METHOD),
            ("pay_seed_007", 540000, "upi", "BANK_ERROR", FailureCategory.BANK_FAILURE, PriorityLevel.CRITICAL, 0.84, 91.0, ActionType.RETRY_PAYMENT),
            ("pay_seed_008", 185000, "card", "INSUFFICIENT_FUNDS", FailureCategory.INSUFFICIENT_FUNDS, PriorityLevel.MEDIUM, 0.48, 56.0, ActionType.SEND_PAYMENT_REMINDER),
            ("pay_seed_009", 750000, "netbanking", "GATEWAY_TIMEOUT", FailureCategory.NETWORK_FAILURE, PriorityLevel.HIGH, 0.68, 77.0, ActionType.RETRY_PAYMENT),
            ("pay_seed_010", 95000, "upi", "AUTHENTICATION_FAILED", FailureCategory.AUTHENTICATION_FAILURE, PriorityLevel.MEDIUM, 0.52, 59.0, ActionType.SEND_PAYMENT_REMINDER),
            ("pay_seed_011", 210000, "card", "BANK_ERROR", FailureCategory.BANK_FAILURE, PriorityLevel.HIGH, 0.79, 82.0, ActionType.RETRY_PAYMENT),
            ("pay_seed_012", 430000, "upi", "BANK_ERROR", FailureCategory.BANK_FAILURE, PriorityLevel.HIGH, 0.76, 80.0, ActionType.RETRY_PAYMENT),
        ]

        for pid, amt, meth, fcode, fcat, prio, prob, score, act_type in sample_cases:
            p = Payment(
                id=uuid.uuid4(),
                razorpay_payment_id=pid,
                merchant_id=primary_merchant.id,
                customer_id=customers[3].id,
                amount_minor=amt,
                currency="INR",
                status=PaymentStatus.FAILED,
                method=meth,
                failure_code=fcode,
                failure_description="Transaction failure under standard monitoring",
                created_at=datetime.utcnow() - timedelta(hours=12),
            )
            db.add(p)
            db.flush()

            rc = RecoveryCase(
                id=uuid.uuid4(),
                payment_id=p.id,
                status=RecoveryCaseStatus.OPEN,
                amount_at_risk_minor=amt,
                created_at=datetime.utcnow() - timedelta(hours=12),
            )
            ri = RevenueIntelligenceResult(
                id=uuid.uuid4(),
                payment_id=p.id,
                recovery_case_id=rc.id,
                failure_category=fcat,
                failure_reason=fcode,
                revenue_at_risk=amt,
                recovery_probability=prob,
                estimated_recoverable_revenue=int(amt * prob),
                opportunity_score=score,
                priority=prio,
                recommended_intervention=act_type.value,
                intervention_reason=f"Recommended {act_type.value} based on {fcat.value} recovery characteristics",
                confidence=prob + 0.05,
                explanation=f"Transaction evaluated with opportunity score {score:.1f}.",
                factors=[],
                model_version="rules-v1",
                created_at=datetime.utcnow() - timedelta(hours=12),
            )
            db.add_all([rc, ri])

        # Populate Historical Learning Outcome Records (60+ items for realistic Bayesian chart)
        print("  [+] Seeding 65 historical learning outcome records for Bayesian calibration...")
        learning_configs = [
            (FailureCategory.BANK_FAILURE, ActionType.RETRY_PAYMENT, 28, 22, 6),       # 78.5% recovery rate
            (FailureCategory.NETWORK_FAILURE, ActionType.RETRY_PAYMENT, 18, 13, 5),   # 72.2% recovery rate
            (FailureCategory.INSUFFICIENT_FUNDS, ActionType.RETRY_PAYMENT, 12, 4, 8),   # 33.3% recovery rate
            (FailureCategory.AUTHENTICATION_FAILURE, ActionType.SEND_PAYMENT_REMINDER, 10, 5, 5), # 50.0% recovery rate
        ]

        for fcat, act_t, total_n, successes, failures in learning_configs:
            for j in range(total_n):
                is_succ = j < successes
                record = LearningOutcomeRecord(
                    id=uuid.uuid4(),
                    merchant_id=primary_merchant.id,
                    payment_id=pay_a.id,
                    failure_category=fcat,
                    action_type=act_t,
                    amount_minor=200000 + (j * 15000),
                    retry_count=1,
                    payment_method="upi" if fcat == FailureCategory.BANK_FAILURE else "card",
                    outcome_status=ActionStatus.SUCCEEDED if is_succ else ActionStatus.FAILED,
                    execution_latency_ms=180 + (j * 12),
                    occurred_at=datetime.utcnow() - timedelta(days=20 - (j % 18)),
                    context_metadata={"synthetic": True, "batch": "phase7_seed"},
                )
                db.add(record)

        # Populate Audit Events
        print("  [+] Recording audit events...")
        for event_type, ent_id in [
            (AuditEventType.USER_LOGIN_SUCCESS, admin_user.id),
            (AuditEventType.POLICY_CHANGED, primary_merchant.id),
            (AuditEventType.RECOVERY_VERIFIED, pay_a.id),
        ]:
            db.add(
                AuditEvent(
                    id=uuid.uuid4(),
                    entity_type="Merchant" if "POLICY" in event_type.value else "Payment",
                    entity_id=ent_id,
                    event_type=event_type,
                    actor_type=ActorType.SYSTEM,
                    audit_metadata={"seeded": True, "version": "Phase 7"},
                    created_at=datetime.utcnow() - timedelta(hours=1),
                )
            )

        db.commit()
        print("=" * 70)
        print(">>> SUCCESS: RecoverX Demo Environment Reset & Seeded!")
        print("=" * 70)
        print("\nDemo Accounts:")
        print("  * Admin:    admin@recoverx.io    / Admin@RecoverX2026!")
        print("  * Operator: operator@recoverx.io / Operator@RecoverX2026!")
        print("  * Analyst:  analyst@recoverx.io  / Analyst@RecoverX2026!")
        print("\nNamed Scenarios Ready in UI:")
        print("  * Scenario A: pay_demo_scenario_a_001 (INR 2,450, Bank Failure -> Allowed & Captured)")
        print("  * Scenario B: pay_demo_scenario_b_002 (INR 8,900, Retries=3 -> Blocked by PolicyEngine)")
        print("  * Scenario C: pay_demo_scenario_c_003 (INR 4,200, Timeout -> UNKNOWN with Reconciliation)")
        print("  * Scenario D: pay_acme_isolated_999 (Cross-Tenant Security Blocked)")

    except Exception as ex:
        db.rollback()
        print(f"\n[-] Error seeding demo environment: {str(ex)}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    reset_and_seed_demo_environment()
