"""Automated Unit and Integration Tests for Phase 6 Identity, Multi-Tenancy & RBAC."""

import pytest
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, AsyncMock
from fastapi import HTTPException, status

from app.db.base import UserRole, ActionStatus, PaymentStatus, RecoveryCaseStatus, PolicyStatus
from app.db.models.user import User
from app.db.models.merchant import Merchant
from app.db.models.merchant_membership import MerchantMembership
from app.db.models.recovery_action import RecoveryAction
from app.auth.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    decode_access_token,
    JWT_SECRET,
)
from app.auth.dependencies import (
    get_current_user,
    get_current_tenant,
    require_role,
    TenantContext,
)
from app.agent.tools.registry import ToolRegistry


# ==============================================================================
# 1. Cryptographic Password & JWT Security Tests
# ==============================================================================

def test_password_hashing_and_verification():
    """Verify bcrypt hash generation, verification, and rejection of invalid passwords."""
    plain = "SuperSecretPassword2026!"
    hashed = get_password_hash(plain)

    assert hashed != plain
    assert hashed.startswith("$2b$") or hashed.startswith("$2a$")
    assert verify_password(plain, hashed) is True
    assert verify_password("WrongPassword123", hashed) is False


def test_jwt_creation_and_validation():
    """Verify JWT access token generation and claims extraction."""
    user_id = str(uuid.uuid4())
    email = "test.admin@recoverx.io"
    merchant_id = str(uuid.uuid4())

    token = create_access_token(user_id=user_id, email=email, default_merchant_id=merchant_id)
    payload = decode_access_token(token)

    assert payload["sub"] == user_id
    assert payload["email"] == email
    assert payload["merchant_id"] == merchant_id
    assert "exp" in payload
    assert "jti" in payload
    assert payload["type"] == "access"


def test_jwt_expired_token_rejected():
    """Verify expired token raises validation error."""
    user_id = str(uuid.uuid4())
    expired_delta = timedelta(seconds=-10)

    token = create_access_token(user_id=user_id, email="exp@recoverx.io", expires_delta=expired_delta)
    
    with pytest.raises(Exception):
        decode_access_token(token)


# ==============================================================================
# 2. Authentication & Tenant Resolution Dependencies
# ==============================================================================

@pytest.mark.asyncio
async def test_get_current_user_blocks_inactive_account():
    """Inactive or deactivated user account must be strictly rejected with 401."""
    user_id = uuid.uuid4()
    inactive_user = User(
        id=user_id,
        email="disabled@recoverx.io",
        password_hash="hash",
        full_name="Disabled User",
        is_active=False,  # Inactive!
    )

    token = create_access_token(user_id=str(user_id), email=inactive_user.email)
    
    mock_auth = MagicMock()
    mock_auth.credentials = token

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = inactive_user

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(auth=mock_auth, db=mock_db)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "deactivated" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_get_current_tenant_resolves_membership():
    """Active member of a merchant tenant resolves successfully to TenantContext."""
    user_id = uuid.uuid4()
    merchant_id = uuid.uuid4()

    user = User(id=user_id, email="active@recoverx.io", password_hash="h", full_name="Active User", is_active=True)
    merchant = Merchant(id=merchant_id, name="Test Merchant", external_id="test_merch", currency="INR")
    membership = MerchantMembership(
        id=uuid.uuid4(),
        user_id=user_id,
        merchant_id=merchant_id,
        role=UserRole.ADMIN,
        is_active=True,
    )

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.all.return_value = [membership]
    mock_db.query.return_value.filter.return_value.first.return_value = merchant

    tenant = await get_current_tenant(user=user, x_merchant_id=str(merchant_id), db=mock_db)

    assert tenant.user.id == user_id
    assert tenant.merchant.id == merchant_id
    assert tenant.role == UserRole.ADMIN


@pytest.mark.asyncio
async def test_get_current_tenant_blocks_unauthorized_cross_tenant_access():
    """Attempting to access Merchant B while only belonging to Merchant A must raise 403."""
    user_id = uuid.uuid4()
    merchant_a = uuid.uuid4()
    merchant_b = uuid.uuid4()

    user = User(id=user_id, email="member_a@recoverx.io", password_hash="h", full_name="User A", is_active=True)
    membership_a = MerchantMembership(
        id=uuid.uuid4(),
        user_id=user_id,
        merchant_id=merchant_a,
        role=UserRole.ADMIN,
        is_active=True,
    )

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.all.return_value = [membership_a]

    # User attempts to request Merchant B via X-Merchant-ID header
    with pytest.raises(HTTPException) as exc_info:
        await get_current_tenant(user=user, x_merchant_id=str(merchant_b), db=mock_db)

    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert "not an authorized member" in exc_info.value.detail.lower()


# ==============================================================================
# 3. RBAC Enforcement Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_rbac_analyst_blocked_from_execution():
    """ANALYST role is strictly forbidden from executing recovery actions."""
    analyst_membership = MerchantMembership(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        merchant_id=uuid.uuid4(),
        role=UserRole.ANALYST,
        is_active=True,
    )
    tenant = TenantContext(
        user=User(id=analyst_membership.user_id, email="analyst@recoverx.io", password_hash="h", full_name="Analyst", is_active=True),
        membership=analyst_membership,
        merchant=Merchant(id=analyst_membership.merchant_id, name="Test", external_id="test", currency="INR"),
    )

    role_checker = require_role([UserRole.ADMIN, UserRole.OPERATOR])

    with pytest.raises(HTTPException) as exc_info:
        await role_checker(tenant=tenant)

    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert "insufficient role permissions" in exc_info.value.detail.lower() or "requires one of" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_rbac_operator_and_admin_allowed_execution():
    """OPERATOR and ADMIN roles are permitted to access recovery execution endpoints."""
    operator_membership = MerchantMembership(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        merchant_id=uuid.uuid4(),
        role=UserRole.OPERATOR,
        is_active=True,
    )
    tenant = TenantContext(
        user=User(id=operator_membership.user_id, email="op@recoverx.io", password_hash="h", full_name="Operator", is_active=True),
        membership=operator_membership,
        merchant=Merchant(id=operator_membership.merchant_id, name="Test", external_id="test", currency="INR"),
    )

    role_checker = require_role([UserRole.ADMIN, UserRole.OPERATOR])
    result = await role_checker(tenant=tenant)

    assert result.role == UserRole.OPERATOR


# ==============================================================================
# 4. Agent Identity & Permission Boundary Tests
# ==============================================================================

def test_agent_tools_have_zero_mutation_authority():
    """Ensure the AI Recovery Agent registry contains ONLY read-only inspection tools."""
    mock_db = MagicMock()
    registry = ToolRegistry(mock_db)

    tools = registry.list_tools()
    
    # Check that forbidden mutation tools do NOT exist
    forbidden = ["execute_action", "modify_payment", "refund", "delete", "create_user", "change_policy"]
    for f in forbidden:
        assert f not in tools
        assert registry.is_tool_allowed(f) is False

    # Check allowed inspection tools exist
    assert "get_payment_context" in tools
    assert "get_recovery_history" in tools
    assert "get_revenue_intelligence" in tools
    assert "get_merchant_context" in tools
    assert "get_recovery_policy" in tools
    assert "get_allowed_actions" in tools
    assert "get_recovery_strategy_evidence" in tools
