"""Pydantic schemas for Phase 6 Identity, Multi-Tenancy & RBAC."""

from typing import List, Optional
import uuid
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

from app.db.base import UserRole


class LoginRequest(BaseModel):
    """Credentials for authentication."""
    email: EmailStr
    password: str = Field(..., min_length=6)


class UserResponse(BaseModel):
    """User profile response (never exposes password hashes)."""
    id: uuid.UUID
    email: str
    full_name: str
    is_active: bool
    last_login_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class MerchantSummary(BaseModel):
    """Minimal merchant representation in membership context."""
    id: uuid.UUID
    name: str
    external_id: str
    currency: str

    class Config:
        from_attributes = True


class MerchantMembershipResponse(BaseModel):
    """Membership record with role and merchant details."""
    id: uuid.UUID
    merchant_id: uuid.UUID
    merchant_name: str
    merchant_external_id: str
    currency: str
    role: UserRole
    is_active: bool


class TokenResponse(BaseModel):
    """Successful login response."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    active_merchant: MerchantMembershipResponse
    available_merchants: List[MerchantMembershipResponse]


class SwitchMerchantRequest(BaseModel):
    """Request to switch active merchant tenant context."""
    merchant_id: uuid.UUID


class TenantContextResponse(BaseModel):
    """Current authenticated user and tenant context."""
    user: UserResponse
    active_membership: MerchantMembershipResponse
    available_merchants: List[MerchantMembershipResponse]


class CreateUserRequest(BaseModel):
    """Request to create a new user and assign initial membership."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str
    merchant_id: uuid.UUID
    role: UserRole = UserRole.ANALYST
