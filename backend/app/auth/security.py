"""Cryptographic and JWT security utilities for Phase 6."""

import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Password hashing context using standard bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT configuration
JWT_SECRET = settings.jwt_secret
JWT_ALGORITHM = settings.jwt_algorithm
ACCESS_TOKEN_EXPIRE_HOURS = settings.access_token_expire_hours


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate bcrypt password hash."""
    return pwd_context.hash(password)


def create_access_token(
    user_id: str,
    email: str,
    default_merchant_id: Optional[str] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create signed JWT access token containing only non-sensitive claims."""
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS))

    payload: Dict[str, Any] = {
        "sub": str(user_id),
        "email": email,
        "merchant_id": str(default_merchant_id) if default_merchant_id else None,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "jti": str(uuid.uuid4()),
        "type": "access",
    }

    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode and validate JWT access token.
    
    Raises:
        jwt.PyJWTError on invalid/expired token.
    """
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
