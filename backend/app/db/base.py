from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID, JSONB
import enum

Base = declarative_base()


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    OPERATOR = "OPERATOR"
    ANALYST = "ANALYST"


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
    ACTION_PROPOSED = "ACTION_PROPOSED"
    ACTION_AUTHORIZED = "ACTION_AUTHORIZED"
    ACTION_BLOCKED = "ACTION_BLOCKED"
    ACTION_EXECUTED = "ACTION_EXECUTED"
    ACTION_RECONCILED = "ACTION_RECONCILED"
    ACTION_CANCELLED = "ACTION_CANCELLED"
    RECOVERY_VERIFIED = "RECOVERY_VERIFIED"
    # Phase 6 Security and Identity Audit Events
    USER_LOGIN_SUCCESS = "USER_LOGIN_SUCCESS"
    USER_LOGIN_FAILURE = "USER_LOGIN_FAILURE"
    TOKEN_REJECTED = "TOKEN_REJECTED"
    ROLE_CHANGED = "ROLE_CHANGED"
    MEMBERSHIP_CREATED = "MEMBERSHIP_CREATED"
    MEMBERSHIP_DISABLED = "MEMBERSHIP_DISABLED"
    POLICY_CHANGED = "POLICY_CHANGED"


class ActorType(str, enum.Enum):
    SYSTEM = "SYSTEM"
    WEBHOOK = "WEBHOOK"
    AGENT = "AGENT"
    USER = "USER"


class AgentRunStatus(str, enum.Enum):
    CREATED = "CREATED"
    INVESTIGATING = "INVESTIGATING"
    PLANNING = "PLANNING"
    VALIDATING = "VALIDATING"
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"


class PolicyStatus(str, enum.Enum):
    ALLOWED = "ALLOWED"
    BLOCKED = "BLOCKED"
    REQUIRES_APPROVAL = "REQUIRES_APPROVAL"


class ActionStatus(str, enum.Enum):
    PROPOSED = "PROPOSED"
    POLICY_CHECK = "POLICY_CHECK"
    AUTHORIZED = "AUTHORIZED"
    QUEUED = "QUEUED"
    EXECUTING = "EXECUTING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    RETRYABLE = "RETRYABLE"
    BLOCKED = "BLOCKED"
    REQUIRES_APPROVAL = "REQUIRES_APPROVAL"
    CANCELLED = "CANCELLED"
    UNKNOWN = "UNKNOWN"


class ExecutionAttemptStatus(str, enum.Enum):
    PENDING = "PENDING"
    EXECUTING = "EXECUTING"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    TIMEOUT = "TIMEOUT"
    UNKNOWN = "UNKNOWN"


class TimestampMixin:
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
