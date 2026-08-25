"""Database model for persisted Learning Model Snapshots (Phase 5)."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.db.base import Base, TimestampMixin


class LearningModelSnapshot(Base, TimestampMixin):
    """Persisted snapshot of adaptive recovery intelligence and calibration metrics."""
    __tablename__ = "learning_model_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id = Column(UUID(as_uuid=True), ForeignKey("merchants.id"), nullable=True, index=True)
    
    model_version = Column(String, nullable=False, default="adaptive-v1")
    evidence_window_days = Column(Integer, nullable=False, default=90)
    
    total_samples = Column(Integer, nullable=False, default=0)
    confirmed_recoveries = Column(Integer, nullable=False, default=0)
    overall_recovery_rate = Column(Float, nullable=False, default=0.0)
    
    # Statistical predictive calibration metric (lower is better, e.g. Brier score)
    brier_score = Column(Float, nullable=True)
    
    # Granular aggregates by failure category and strategy
    category_metrics = Column(JSONB, nullable=False, default=dict)
    strategy_metrics = Column(JSONB, nullable=False, default=dict)
    
    # Drift status: NORMAL, DRIFT_DETECTED, DEGRADED
    drift_status = Column(String, nullable=False, default="NORMAL")
    drift_details = Column(JSONB, nullable=True)
    
    generated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    merchant = relationship("Merchant")
