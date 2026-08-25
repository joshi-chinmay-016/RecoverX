"""Pydantic schemas for Revenue Intelligence."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from uuid import UUID
from datetime import datetime
from enum import Enum


class FailureCategory(str, Enum):
    """Normalized failure categories."""
    PAYMENT_METHOD_FAILURE = "PAYMENT_METHOD_FAILURE"
    INSUFFICIENT_FUNDS = "INSUFFICIENT_FUNDS"
    BANK_FAILURE = "BANK_FAILURE"
    NETWORK_FAILURE = "NETWORK_FAILURE"
    AUTHENTICATION_FAILURE = "AUTHENTICATION_FAILURE"
    LIMIT_EXCEEDED = "LIMIT_EXCEEDED"
    TEMPORARY_FAILURE = "TEMPORARY_FAILURE"
    UNKNOWN = "UNKNOWN"


class PriorityLevel(str, Enum):
    """Priority levels for recovery opportunities."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class FeatureSet(BaseModel):
    """Extracted features for a payment."""
    # Payment-level features
    payment_amount: int
    currency: str
    payment_method: Optional[str] = None
    payment_status: str
    failure_code: Optional[str] = None
    failure_message: Optional[str] = None
    retry_count: int = 0
    created_at: datetime
    last_attempt_at: Optional[datetime] = None
    time_since_failure_hours: Optional[float] = None
    
    # Merchant-level features
    merchant_historical_success_rate: float = 0.0
    merchant_historical_failure_rate: float = 0.0
    merchant_historical_recovery_rate: float = 0.0
    merchant_avg_transaction_value: int = 0
    
    # Merchant-relative transaction value features (Phase 2 correction)
    transaction_value_percentile: float = 0.0  # 0.0 to 1.0, where 1.0 is highest value
    normalized_value_score: float = 0.0  # 0.0 to 1.0, relative to merchant average
    
    # Recovery features
    previous_recovery_attempts: int = 0
    previous_successful_recovery: bool = False
    previous_failed_recovery: bool = False
    recovery_case_age_hours: Optional[float] = None


class FailureClassification(BaseModel):
    """Result of failure classification."""
    category: FailureCategory
    normalized_reason: str
    confidence: float = Field(ge=0.0, le=1.0)
    explanation: str


class RevenueAtRisk(BaseModel):
    """Revenue at risk calculation."""
    gross_failed_revenue: int
    potentially_recoverable_revenue: int
    estimated_recoverable_revenue: int
    recovered_revenue: int = 0
    unrecoverable_revenue: int = 0


class RecoveryProbability(BaseModel):
    """Deterministic rules-based recovery likelihood estimate with contributing factors."""
    probability: float = Field(ge=0.0, le=1.0, description="Estimated recovery likelihood (0.0 to 1.0)")
    factors: List[Dict[str, Any]] = []


class OpportunityScore(BaseModel):
    """Opportunity scoring result with contributing factors."""
    score: float = Field(ge=0.0, le=100.0)
    priority: PriorityLevel
    explanation: str
    score_factors: List[Dict[str, Any]] = Field(default_factory=list, description="Major contributing factors to the score")


class InterventionRecommendation(BaseModel):
    """Recommended intervention."""
    recommended_action: str
    reason: str
    confidence: float = Field(ge=0.0, le=1.0)


class IntelligenceResult(BaseModel):
    """Complete intelligence result for a payment/recovery case."""
    id: Union[UUID, str]
    payment_id: Union[UUID, str]
    recovery_case_id: Optional[Union[UUID, str]] = None
    
    # Classification
    failure_category: FailureCategory
    failure_reason: str
    
    # Revenue metrics
    revenue_at_risk: int
    recovery_probability: float
    estimated_recoverable_revenue: int
    
    # Scoring
    opportunity_score: float
    priority: PriorityLevel
    
    # Recommendation
    recommended_intervention: str
    intervention_reason: str
    confidence: float
    
    # Explainability
    explanation: str
    factors: List[Dict[str, Any]] = []
    
    # Metadata
    model_version: str = "rules-v1"
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class IntelligenceOverview(BaseModel):
    """Merchant-level aggregate intelligence."""
    total_revenue: int
    failed_revenue: int
    revenue_at_risk: int
    estimated_recoverable_revenue: int
    recovered_revenue: int
    recovery_opportunity_count: int
    high_priority_opportunities: int
    
    # Failure distribution
    failure_distribution: Dict[str, int] = {}
    top_failure_reasons: List[Dict[str, Any]] = []
    
    # Priority distribution
    priority_distribution: Dict[str, int] = {}


class OpportunityListResponse(BaseModel):
    """Paginated list of recovery opportunities."""
    opportunities: List[IntelligenceResult]
    total: int
    page: int
    page_size: int


class AnalysisRequest(BaseModel):
    """Request for batch analysis."""
    payment_ids: Optional[List[str]] = None
    recovery_case_ids: Optional[List[str]] = None
    force_reanalyze: bool = False
