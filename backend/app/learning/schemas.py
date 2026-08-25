"""Pydantic schemas for Phase 5 Adaptive Recovery Intelligence & Learning."""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from app.intelligence.schemas import FailureCategory
from app.agent.schemas import ActionType


class EvidenceScope(str, Enum):
    """Scope of evidence used in adaptive calculation."""
    MERCHANT_CATEGORY_ACTION = "MERCHANT_CATEGORY_ACTION"
    MERCHANT_CATEGORY = "MERCHANT_CATEGORY"
    GLOBAL_CATEGORY_ACTION = "GLOBAL_CATEGORY_ACTION"
    GLOBAL_CATEGORY = "GLOBAL_CATEGORY"
    BASELINE_FALLBACK = "BASELINE_FALLBACK"


class SupportLevel(str, Enum):
    """Statistical sample support level."""
    HIGH = "HIGH"          # >= 50 samples
    MODERATE = "MODERATE"  # >= 20 samples
    LOW = "LOW"            # >= 10 samples
    SPARSE = "SPARSE"      # < 10 samples (falls back or heavily smoothed)


class DriftStatus(str, Enum):
    """Drift or performance degradation status."""
    NORMAL = "NORMAL"
    DEGRADATION_DETECTED = "DEGRADATION_DETECTED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class StrategyScoreFactor(BaseModel):
    """Individual contributing factor to strategy score."""
    name: str
    impact: float
    description: str


class StrategyRankItem(BaseModel):
    """Ranked recovery intervention recommendation."""
    action_type: ActionType
    strategy_score: float = Field(..., ge=0.0, le=100.0)
    empirical_recovery_rate: float = Field(..., ge=0.0, le=1.0)
    sample_size: int = Field(..., ge=0)
    support_level: SupportLevel
    evidence_scope: EvidenceScope
    is_policy_eligible: bool = True
    confidence: float = Field(..., ge=0.0, le=1.0)
    factors: List[StrategyScoreFactor] = Field(default_factory=list)
    reasons: List[str] = Field(default_factory=list)


class AdaptiveProbabilityResult(BaseModel):
    """Calibrated probability result with statistical evidence."""
    adaptive_probability: float = Field(..., ge=0.0, le=1.0)
    baseline_probability: float = Field(..., ge=0.0, le=1.0)
    empirical_rate: float = Field(..., ge=0.0, le=1.0)
    sample_size: int = Field(..., ge=0)
    successes: int = Field(..., ge=0)
    support_level: SupportLevel
    evidence_scope: EvidenceScope
    fallback_level: str
    model_version: str = "adaptive-v1"
    is_cold_start: bool = False
    explanation: str


class CategoryLearningMetrics(BaseModel):
    """Statistical performance metrics for a specific failure category."""
    failure_category: FailureCategory
    total_attempts: int
    confirmed_successes: int
    confirmed_failures: int
    observed_recovery_rate: float
    baseline_probability: float
    adaptive_probability: float
    top_recommended_strategy: ActionType
    support_level: SupportLevel


class StrategyPerformanceSummary(BaseModel):
    """Historical performance metrics for a specific recovery strategy."""
    action_type: ActionType
    total_attempts: int
    successful_recoveries: int
    observed_success_rate: float
    average_latency_ms: int
    best_matching_category: Optional[FailureCategory] = None


class CalibrationReport(BaseModel):
    """Predictive probability calibration report."""
    brier_score: float = Field(..., description="Mean squared error of probabilities (0.0=perfect, 0.25=random)")
    evaluated_samples: int
    calibration_status: str
    bucketed_accuracy: List[Dict[str, Any]] = Field(default_factory=list)


class LearningOverviewResponse(BaseModel):
    """System-wide or merchant-scoped learning overview."""
    model_version: str
    model_name: str = "Adaptive Statistical Recovery Model"
    evidence_window_days: int
    total_samples: int
    confirmed_recoveries: int
    overall_recovery_rate: float
    baseline_benchmark_rate: float
    adaptive_yield_lift_pct: float
    unknown_outcomes_count: int
    drift_status: DriftStatus
    brier_score: Optional[float] = None
    last_updated: datetime
    category_breakdown: List[CategoryLearningMetrics]
    strategy_rankings: List[StrategyPerformanceSummary]


class RecomputeResponse(BaseModel):
    """Response after executing explicit learning recomputation."""
    success: bool
    model_version: str
    total_samples_processed: int
    categories_calibrated: int
    strategies_evaluated: int
    brier_score: Optional[float] = None
    drift_status: str
    recomputed_at: datetime
    message: str
