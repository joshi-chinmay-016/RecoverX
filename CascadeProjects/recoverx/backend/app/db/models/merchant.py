from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base, TimestampMixin
import uuid


class Merchant(Base, TimestampMixin):
    __tablename__ = "merchants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    external_id = Column(String, unique=True, nullable=False, index=True)
    currency = Column(String, nullable=False)
