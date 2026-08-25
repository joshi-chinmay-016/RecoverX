"""Database models for Agent Runs - Phase 3."""

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Float, Text, Enum as SQLEnum, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db.base import Base, TimestampMixin
from app.db.base import AgentRunStatus
from uuid import uuid4
import enum


class AgentRun(Base, TimestampMixin):
    """Persistent storage for agent runs."""
    
    __tablename__ = "agent_runs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    run_id = Column(String, unique=True, nullable=False, index=True)
    opportunity_id = Column(String, nullable=False, index=True)
    payment_id = Column(String, nullable=False, index=True)
    merchant_id = Column(String, nullable=False, index=True)
    
    # Execution state
    current_step = Column(Integer, default=0)
    status = Column(SQLEnum(AgentRunStatus), nullable=False, index=True)
    
    # Context (stored as JSON for audit)
    context = Column(JSONB, nullable=True)
    
    # Tool calls summary
    tool_calls_summary = Column(JSONB, nullable=True)
    
    # Reasoning
    reasoning_summary = Column(Text, nullable=True)
    decision_trace = Column(JSONB, nullable=True)
    
    # Output
    proposed_plan = Column(JSONB, nullable=True)
    
    # Validation
    validation_result = Column(JSONB, nullable=True)
    
    # Error handling
    errors = Column(JSONB, nullable=True)
    
    # Timing
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    
    # Metadata
    agent_version = Column(String, nullable=False)
    prompt_version = Column(String, nullable=False)
    policy_version = Column(String, nullable=False)
    
    # Relationships
    tool_calls = relationship("AgentToolCall", back_populates="agent_run", cascade="all, delete-orphan")


class AgentToolCall(Base, TimestampMixin):
    """Record of tool calls made by the agent."""
    
    __tablename__ = "agent_tool_calls"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    run_id = Column(String, nullable=False, index=True)
    agent_run_id = Column(UUID(as_uuid=True), ForeignKey("agent_runs.id"), nullable=False)
    
    tool_name = Column(String, nullable=False)
    input_summary = Column(Text, nullable=True)
    output_summary = Column(Text, nullable=True)
    step_number = Column(Integer, nullable=False)
    execution_time_ms = Column(Integer, nullable=True)
    
    # Relationships
    agent_run = relationship("AgentRun", back_populates="tool_calls")
