"""Bootstrap demo users with RBAC roles for Phase 6 Identity & Multi-Tenancy."""

import os
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.base import UserRole
from app.db.models.user import User
from app.db.models.merchant import Merchant
from app.db.models.merchant_membership import MerchantMembership
from app.auth.security import get_password_hash


def bootstrap_demo_users(db: Session):
    """Seed standard demo users and merchant memberships."""
    print("Bootstrapping RecoverX Phase 6 Demo Users & Multi-Tenant Memberships...")

    # 1. Ensure Primary Demo Merchant exists
    primary_merchant = db.query(Merchant).filter(Merchant.external_id == "demo_merchant_agent").first()
    if not primary_merchant:
        primary_merchant = Merchant(
            name="Demo Merchant Agent",
            external_id="demo_merchant_agent",
            currency="INR",
        )
        db.add(primary_merchant)
        db.commit()
        db.refresh(primary_merchant)
    print(f"[OK] Primary Merchant: {primary_merchant.name} ({primary_merchant.id})")

    # 2. Ensure Secondary Demo Merchant exists for tenant switching
    secondary_merchant = db.query(Merchant).filter(Merchant.external_id == "acme_global").first()
    if not secondary_merchant:
        secondary_merchant = Merchant(
            name="Acme Global Payments",
            external_id="acme_global",
            currency="INR",
        )
        db.add(secondary_merchant)
        db.commit()
        db.refresh(secondary_merchant)
    print(f"[OK] Secondary Merchant: {secondary_merchant.name} ({secondary_merchant.id})")

    # 3. Standard Demo User Profiles
    demo_accounts = [
        {
            "email": os.getenv("ADMIN_EMAIL", "admin@recoverx.io"),
            "password": os.getenv("ADMIN_PASSWORD", "Admin@RecoverX2026!"),
            "full_name": "Elena Vance (Platform Admin)",
            "memberships": [
                (primary_merchant.id, UserRole.ADMIN),
                (secondary_merchant.id, UserRole.ADMIN),
            ],
        },
        {
            "email": os.getenv("OPERATOR_EMAIL", "operator@recoverx.io"),
            "password": os.getenv("OPERATOR_PASSWORD", "Operator@RecoverX2026!"),
            "full_name": "Marcus Kane (Recovery Operator)",
            "memberships": [
                (primary_merchant.id, UserRole.OPERATOR),
            ],
        },
        {
            "email": os.getenv("ANALYST_EMAIL", "analyst@recoverx.io"),
            "password": os.getenv("ANALYST_PASSWORD", "Analyst@RecoverX2026!"),
            "full_name": "Sarah Chen (Risk Analyst)",
            "memberships": [
                (primary_merchant.id, UserRole.ANALYST),
            ],
        },
    ]

    for acc in demo_accounts:
        email = acc["email"].lower().strip()
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(
                email=email,
                password_hash=get_password_hash(acc["password"]),
                full_name=acc["full_name"],
                is_active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"  Created user: {user.email} (ID: {user.id})")
        else:
            # Update password hash to match current config
            user.password_hash = get_password_hash(acc["password"])
            user.full_name = acc["full_name"]
            user.is_active = True
            db.commit()
            print(f"  Updated user: {user.email}")

        # Ensure memberships
        for merch_id, role in acc["memberships"]:
            membership = (
                db.query(MerchantMembership)
                .filter(
                    MerchantMembership.user_id == user.id,
                    MerchantMembership.merchant_id == merch_id,
                )
                .first()
            )
            if not membership:
                membership = MerchantMembership(
                    user_id=user.id,
                    merchant_id=merch_id,
                    role=role,
                    is_active=True,
                )
                db.add(membership)
                db.commit()
                print(f"    Assigned role {role.value} on merchant {merch_id}")
            else:
                membership.role = role
                membership.is_active = True
                db.commit()

    print("[OK] Phase 6 Demo Users and RBAC Memberships successfully configured.")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        bootstrap_demo_users(db)
    finally:
        db.close()
