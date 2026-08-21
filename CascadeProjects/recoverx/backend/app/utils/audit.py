from sqlalchemy.orm import Session
from app.db.models.audit_event import AuditEvent
from app.db.base import AuditEventType, ActorType
from app.core.logging import logger
from typing import Optional, Dict, Any
import uuid


class AuditService:
    """Service for creating audit events."""
    
    @staticmethod
    def create_audit_event(
        db: Session,
        entity_type: str,
        entity_id: str,
        event_type: AuditEventType,
        actor_type: ActorType = ActorType.SYSTEM,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditEvent:
        """Create an audit event."""
        audit_event = AuditEvent(
            entity_type=entity_type,
            entity_id=uuid.UUID(entity_id) if isinstance(entity_id, str) else entity_id,
            event_type=event_type,
            actor_type=actor_type,
            audit_metadata=metadata or {}
        )
        
        db.add(audit_event)
        db.commit()
        db.refresh(audit_event)
        
        logger.info(
            f"audit_event_created "
            f"entity_type={entity_type} "
            f"entity_id={entity_id} "
            f"event_type={event_type}"
        )
        
        return audit_event