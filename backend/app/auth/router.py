"""FastAPI REST Router for Authentication, Identity & Multi-Tenancy."""

from datetime import datetime
from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.base import AuditEventType, ActorType
from app.db.models.user import User
from app.db.models.merchant_membership import MerchantMembership
from app.db.models.merchant import Merchant
from app.db.models.audit_event import AuditEvent
from app.auth.security import verify_password, create_access_token
from app.auth.schemas import (
    LoginRequest,
    TokenResponse,
    UserResponse,
    MerchantMembershipResponse,
    TenantContextResponse,
    SwitchMerchantRequest,
)
from app.auth.dependencies import (
    get_current_user,
    get_current_tenant,
    TenantContext,
)
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication & Identity"])


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
):
    """Authenticate user with email/password and issue JWT access token."""
    user = db.query(User).filter(User.email == payload.email.lower().strip()).first()
    
    # 1. Validate credentials
    if not user or not verify_password(payload.password, user.password_hash):
        logger.warning(f"login_failed email={payload.email}")
        
        # Log failure audit event
        audit = AuditEvent(
            entity_type="USER",
            entity_id=user.id if user else uuid.uuid4(),
            event_type=AuditEventType.USER_LOGIN_FAILURE,
            actor_type=ActorType.USER,
            audit_metadata={"email": payload.email, "reason": "Invalid credentials"},
        )
        db.add(audit)
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 2. Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive. Please contact your organization administrator.",
        )

    # 3. Retrieve user's merchant memberships
    memberships = (
        db.query(MerchantMembership)
        .filter(MerchantMembership.user_id == user.id, MerchantMembership.is_active == True)
        .all()
    )

    if not memberships:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not associated with any active merchant tenant.",
        )

    # Pick first active merchant as default
    active_m = memberships[0]
    merchant = db.query(Merchant).filter(Merchant.id == active_m.merchant_id).first()

    # Update last login timestamp
    user.last_login_at = datetime.utcnow()
    
    # Log success audit event
    audit = AuditEvent(
        entity_type="USER",
        entity_id=user.id,
        event_type=AuditEventType.USER_LOGIN_SUCCESS,
        actor_type=ActorType.USER,
        audit_metadata={"email": user.email, "merchant_id": str(active_m.merchant_id), "role": active_m.role.value},
    )
    db.add(audit)
    db.commit()
    db.refresh(user)

    # Generate JWT
    token = create_access_token(
        user_id=str(user.id),
        email=user.email,
        default_merchant_id=str(active_m.merchant_id),
    )

    # Format membership responses
    available_memberships: List[MerchantMembershipResponse] = []
    for m in memberships:
        m_merch = db.query(Merchant).filter(Merchant.id == m.merchant_id).first()
        available_memberships.append(MerchantMembershipResponse(
            id=m.id,
            merchant_id=m.merchant_id,
            merchant_name=m_merch.name if m_merch else "Unknown Merchant",
            merchant_external_id=m_merch.external_id if m_merch else "",
            currency=m_merch.currency if m_merch else "INR",
            role=m.role,
            is_active=m.is_active,
        ))

    active_resp = next(m for m in available_memberships if m.merchant_id == active_m.merchant_id)

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
        active_merchant=active_resp,
        available_merchants=available_memberships,
    )


@router.get("/me", response_model=TenantContextResponse)
def get_current_user_profile(
    tenant: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db),
):
    """Retrieve current authenticated user profile, active tenant, and memberships."""
    memberships = (
        db.query(MerchantMembership)
        .filter(MerchantMembership.user_id == tenant.user.id, MerchantMembership.is_active == True)
        .all()
    )

    available_memberships: List[MerchantMembershipResponse] = []
    for m in memberships:
        m_merch = db.query(Merchant).filter(Merchant.id == m.merchant_id).first()
        available_memberships.append(MerchantMembershipResponse(
            id=m.id,
            merchant_id=m.merchant_id,
            merchant_name=m_merch.name if m_merch else "Unknown Merchant",
            merchant_external_id=m_merch.external_id if m_merch else "",
            currency=m_merch.currency if m_merch else "INR",
            role=m.role,
            is_active=m.is_active,
        ))

    active_resp = next((m for m in available_memberships if m.merchant_id == tenant.merchant.id), available_memberships[0])

    return TenantContextResponse(
        user=UserResponse.model_validate(tenant.user),
        active_membership=active_resp,
        available_merchants=available_memberships,
    )


@router.post("/switch-merchant", response_model=TenantContextResponse)
def switch_merchant_tenant(
    payload: SwitchMerchantRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Switch user's active merchant tenant context after verifying membership."""
    membership = (
        db.query(MerchantMembership)
        .filter(
            MerchantMembership.user_id == user.id,
            MerchantMembership.merchant_id == payload.merchant_id,
            MerchantMembership.is_active == True,
        )
        .first()
    )

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You do not have an active membership for the requested merchant.",
        )

    merchant = db.query(Merchant).filter(Merchant.id == payload.merchant_id).first()
    if not merchant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Merchant not found.")

    memberships = (
        db.query(MerchantMembership)
        .filter(MerchantMembership.user_id == user.id, MerchantMembership.is_active == True)
        .all()
    )

    available_memberships = []
    for m in memberships:
        m_merch = db.query(Merchant).filter(Merchant.id == m.merchant_id).first()
        available_memberships.append(MerchantMembershipResponse(
            id=m.id,
            merchant_id=m.merchant_id,
            merchant_name=m_merch.name if m_merch else "Unknown Merchant",
            merchant_external_id=m_merch.external_id if m_merch else "",
            currency=m_merch.currency if m_merch else "INR",
            role=m.role,
            is_active=m.is_active,
        ))

    active_resp = next(m for m in available_memberships if m.merchant_id == payload.merchant_id)

    return TenantContextResponse(
        user=UserResponse.model_validate(user),
        active_membership=active_resp,
        available_merchants=available_memberships,
    )
