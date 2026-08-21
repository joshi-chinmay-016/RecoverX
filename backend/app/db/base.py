from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID, JSONB
import enum

Base = declarative_base()


class PaymentStatus(str, enum.Enum):
    CREATED = "CREATED"
    AUTHORIZED = "AUTHORIZED"
    CAPTURED = "CAPTURED"
    FAILED = "FAILED"


class ProcessingStatus(str, enum.Enum):
    RECEIVED = "RECEIVED"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"
    IGNORED = "IGNORED"


class RecoveryCaseStatus(str, enum.Enum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class AuditEventType(str, enum.Enum):
    WEBHOOK_RECEIVED = "WEBHOOK_RECEIVED"
    PAYMENT_CREATED = "PAYMENT_CREATED"
    PAYMENT_STATUS_CHANGED = "PAYMENT_STATUS_CHANGED"
    RECOVERY_CASE_CREATED = "RECOVERY_CASE_CREATED"
    AGENT_DECISION = "AGENT_DECISION"
    POLICY_DECISION = "POLICY_DECISION"
    ACTION_EXECUTED = "ACTION_EXECUTED"
    RECOVERY_VERIFIED = "RECOVERY_VERIFIED"


class ActorType(str, enum.Enum):
    SYSTEM = "SYSTEM"
    WEBHOOK = "WEBHOOK"
    AGENT = "AGENT"
    USER = "USER"


class TimestampMixin:
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
