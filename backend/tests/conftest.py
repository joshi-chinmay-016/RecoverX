"""Pytest configuration and environment fixtures for RecoverX test suite."""

import sys
import os
import uuid
from datetime import datetime
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Ensure backend root is always in Python module path
BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from app.main import app
from app.db.session import SessionLocal, get_db
from app.db.models.user import User
from app.db.models.merchant import Merchant
from app.db.models.merchant_membership import MerchantMembership
from app.db.base import UserRole
from app.auth.dependencies import get_current_tenant, TenantContext
from app.auth.security import get_password_hash


@pytest.fixture
def db():
    """Database session fixture."""
    db_session = SessionLocal()
    try:
        yield db_session
    finally:
        db_session.rollback()
        db_session.close()


@pytest.fixture
def sample_tenant(db: Session):
    """Fixture providing a test merchant, user, and membership."""
    unique_suffix = uuid.uuid4().hex[:8]
    merchant = Merchant(
        name=f"Test Merchant {unique_suffix}",
        external_id=f"merchant_{unique_suffix}",
        currency="INR",
    )
    db.add(merchant)
    db.flush()

    user = User(
        email=f"testuser_{unique_suffix}@recoverx.io",
        password_hash=get_password_hash("TestPassword123!"),
        full_name="Test Suite User",
        is_active=True,
    )
    db.add(user)
    db.flush()

    membership = MerchantMembership(
        user_id=user.id,
        merchant_id=merchant.id,
        role=UserRole.ADMIN,
        is_active=True,
    )
    db.add(membership)
    db.commit()
    db.refresh(merchant)
    db.refresh(user)
    db.refresh(membership)

    return TenantContext(user=user, merchant=merchant, membership=membership)


@pytest.fixture
def client(db: Session, sample_tenant: TenantContext):
    """FastAPI TestClient with database and tenant context dependency overrides."""
    def override_get_db():
        yield db

    def override_get_tenant():
        return sample_tenant

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_tenant] = override_get_tenant

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
