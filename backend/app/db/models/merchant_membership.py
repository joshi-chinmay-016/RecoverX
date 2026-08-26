"""Merchant Membership database model for Phase 6 Multi-Tenancy & RBAC."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base, TimestampMixin, UserRole


class MerchantMembership(Base, TimestampMixin):
    """User membership and role assignment within a specific merchant tenant."""
    __tablename__ = "merchant_memberships"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    merchant_id = Column(UUID(as_uuid=True), ForeignKey("merchants.id"), nullable=False, index=True)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.ANALYST, index=True)
    is_active = Column(Boolean, default=True, nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "merchant_id", name="uq_user_merchant_membership"),
    )

    user = relationship("User", back_populates="memberships")
    merchant = relationship("Merchant")
