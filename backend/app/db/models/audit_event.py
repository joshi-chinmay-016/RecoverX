from sqlalchemy import Column, String, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db.base import Base, TimestampMixin, AuditEventType, ActorType
import uuid


class AuditEvent(Base, TimestampMixin):
    __tablename__ = "audit_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type = Column(String, nullable=False, index=True)
    entity_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    event_type = Column(SQLEnum(AuditEventType), nullable=False)
    actor_type = Column(SQLEnum(ActorType), nullable=False, default=ActorType.SYSTEM)
    audit_metadata = Column(JSONB, nullable=True)
