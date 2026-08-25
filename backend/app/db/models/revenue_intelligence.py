"""Revenue Intelligence database model."""

from sqlalchemy import Column, Integer, ForeignKey, String, Float, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db.base import Base, TimestampMixin
from app.intelligence.schemas import FailureCategory, PriorityLevel
import uuid


class RevenueIntelligenceResult(Base, TimestampMixin):
    """Persistent intelligence result for payments/recovery cases."""
    __tablename__ = "revenue_intelligence_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payment_id = Column(UUID(as_uuid=True), ForeignKey("payments.id"), nullable=False, unique=True)
    recovery_case_id = Column(UUID(as_uuid=True), ForeignKey("recovery_cases.id"), nullable=True)
    
    # Classification
    failure_category = Column(SQLEnum(FailureCategory), nullable=False)
    failure_reason = Column(String, nullable=False)
    
    # Revenue metrics
    revenue_at_risk = Column(Integer, nullable=False)
    recovery_probability = Column(Float, nullable=False)
    estimated_recoverable_revenue = Column(Integer, nullable=False)
    
    # Scoring
    opportunity_score = Column(Float, nullable=False)
    priority = Column(SQLEnum(PriorityLevel), nullable=False)
    
    # Recommendation
    recommended_intervention = Column(String, nullable=False)
    intervention_reason = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    
    # Explainability
    explanation = Column(String, nullable=False)
    factors = Column(JSONB, nullable=False, default=list)
    
    # Model versioning
    model_version = Column(String, nullable=False, default="rules-v1")

    # Relationships
    payment = relationship("Payment")
    recovery_case = relationship("RecoveryCase")
