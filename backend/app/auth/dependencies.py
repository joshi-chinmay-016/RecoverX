"""Authentication and Tenant Context FastAPI Dependencies for Phase 6."""

from typing import List, Optional
import uuid
import jwt
from fastapi import Depends, HTTPException, Header, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.base import UserRole
from app.db.models.user import User
from app.db.models.merchant_membership import MerchantMembership
from app.db.models.merchant import Merchant
from app.auth.security import decode_access_token
from app.core.logging import get_logger

logger = get_logger(__name__)

security_bearer = HTTPBearer(auto_error=False)


class TenantContext:
    """Encapsulates the fully verified tenant and RBAC execution context."""
    def __init__(
        self,
        user: User,
        membership: MerchantMembership,
        merchant: Merchant,
    ):
        self.user = user
        self.membership = membership
        self.merchant = merchant
        self.role: UserRole = membership.role


async def get_current_user(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: Session = Depends(get_db),
) -> User:
    """Validate JWT bearer token and return active User instance."""
    if not auth or not auth.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Missing Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_access_token(auth.credentials)
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token claims: missing subject")
        user_id = uuid.UUID(user_id_str)
    except (jwt.PyJWTError, ValueError) as e:
        logger.warning(f"token_validation_failed error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User account not found.")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User account is deactivated.")

    return user


async def get_current_tenant(
    user: User = Depends(get_current_user),
    x_merchant_id: Optional[str] = Header(None, alias="X-Merchant-ID"),
    db: Session = Depends(get_db),
) -> TenantContext:
    """Resolve and verify the active merchant tenant context from server-side memberships."""
    # Find user memberships
    memberships = (
        db.query(MerchantMembership)
        .filter(MerchantMembership.user_id == user.id, MerchantMembership.is_active == True)
        .all()
    )

    if not memberships:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User has no active merchant memberships.",
        )

    # Resolve targeted merchant
    active_membership = None
    if x_merchant_id:
        try:
            target_id = uuid.UUID(x_merchant_id)
            active_membership = next((m for m in memberships if m.merchant_id == target_id), None)
            if not active_membership:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: User is not an authorized member of the requested merchant tenant.",
                )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid X-Merchant-ID header format (UUID expected).",
            )
    else:
        # Default to first active membership
        active_membership = memberships[0]

    merchant = db.query(Merchant).filter(Merchant.id == active_membership.merchant_id).first()
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Merchant tenant not found in financial records.",
        )

    return TenantContext(
        user=user,
        membership=active_membership,
        merchant=merchant,
    )


async def get_current_tenant_optional(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    x_merchant_id: Optional[str] = Header(None, alias="X-Merchant-ID"),
    db: Session = Depends(get_db),
) -> Optional[TenantContext]:
    """Optional tenant resolver for backwards-compatible test fixtures and public views."""
    if not auth or not auth.credentials:
        return None
    try:
        user = await get_current_user(auth, db)
        return await get_current_tenant(user, x_merchant_id, db)
    except HTTPException:
        return None


def require_role(allowed_roles: List[UserRole]):
    """FastAPI dependency factory enforcing Role-Based Access Control."""
    async def role_checker(tenant: TenantContext = Depends(get_current_tenant)) -> TenantContext:
        if tenant.role not in allowed_roles:
            logger.warning(
                f"rbac_permission_denied user_id={tenant.user.id} role={tenant.role.value} required={allowed_roles} merchant_id={tenant.merchant.id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: Operation requires one of {[r.value for r in allowed_roles]} role permissions. Current role: {tenant.role.value}.",
            )
        return tenant

    return role_checker
