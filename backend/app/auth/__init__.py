"""Authentication, Identity, RBAC & Multi-Tenancy Package (Phase 6)."""

from app.auth.security import verify_password, get_password_hash, create_access_token, decode_access_token
from app.auth.dependencies import get_current_user, get_current_tenant, require_role, TenantContext
from app.auth.router import router as auth_router

__all__ = [
    "verify_password",
    "get_password_hash",
    "create_access_token",
    "decode_access_token",
    "get_current_user",
    "get_current_tenant",
    "require_role",
    "TenantContext",
    "auth_router",
]
