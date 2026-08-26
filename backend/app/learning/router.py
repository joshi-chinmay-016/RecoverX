"""FastAPI REST Router for Phase 5 Adaptive Recovery Intelligence with Tenant Isolation."""

from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.base import UserRole
from app.intelligence.schemas import FailureCategory
from app.agent.schemas import ActionType
from app.learning.schemas import (
    LearningOverviewResponse,
    StrategyRankItem,
    AdaptiveProbabilityResult,
    CalibrationReport,
    RecomputeResponse,
)
from app.learning.service import LearningService
from app.auth.dependencies import get_current_tenant, require_role, TenantContext
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/learning", tags=["Adaptive Learning"])


@router.get("/overview", response_model=LearningOverviewResponse)
def get_learning_overview(
    tenant: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db),
):
    """Retrieve adaptive learning statistics, overall yield lift, and category breakdown scoped to tenant."""
    service = LearningService(db)
    return service.get_overview(merchant_id=tenant.merchant.id)


@router.get("/strategies", response_model=List[StrategyRankItem])
def get_strategy_rankings(
    failure_category: FailureCategory = Query(FailureCategory.TEMPORARY_FAILURE, description="Failure category to rank"),
    retry_count: int = Query(0, ge=0, le=10, description="Current payment retry count"),
    amount_minor: int = Query(0, ge=0, description="Payment amount in paise"),
    tenant: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db),
):
    """Rank candidate recovery strategies for a specific failure context scoped to tenant."""
    service = LearningService(db)
    return service.strategy_selector.evaluate_strategies(
        failure_category=failure_category,
        merchant_id=tenant.merchant.id,
        retry_count=retry_count,
        payment_amount_minor=amount_minor,
    )


@router.get("/evidence", response_model=AdaptiveProbabilityResult)
def get_adaptive_evidence(
    failure_category: FailureCategory = Query(..., description="Target failure category"),
    action_type: Optional[ActionType] = Query(None, description="Optional recovery action"),
    baseline_probability: float = Query(0.55, ge=0.0, le=1.0, description="Phase 2 deterministic baseline"),
    tenant: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db),
):
    """Query calibrated adaptive probability and statistical evidence scope for authenticated tenant."""
    service = LearningService(db)
    return service.calibrator.calibrate(
        baseline_probability=baseline_probability,
        failure_category=failure_category,
        action_type=action_type,
        merchant_id=tenant.merchant.id,
    )


@router.get("/calibration", response_model=CalibrationReport)
def get_calibration_report(
    tenant: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db),
):
    """Retrieve predictive calibration report and Brier accuracy score scoped to tenant."""
    service = LearningService(db)
    return service.get_calibration_report(merchant_id=tenant.merchant.id)


@router.post("/recompute", response_model=RecomputeResponse)
def recompute_learning_model(
    tenant: TenantContext = Depends(require_role([UserRole.ADMIN, UserRole.OPERATOR])),
    db: Session = Depends(get_db),
):
    """Explicitly recompute adaptive probability weights, strategy ranking metrics, and model snapshot."""
    service = LearningService(db)
    snapshot = service.recompute_snapshot(merchant_id=tenant.merchant.id)
    
    return RecomputeResponse(
        success=True,
        model_version=snapshot.model_version,
        total_samples_processed=snapshot.total_samples,
        categories_calibrated=len(FailureCategory),
        strategies_evaluated=len(ActionType),
        brier_score=snapshot.brier_score,
        drift_status=snapshot.drift_status,
        recomputed_at=snapshot.generated_at,
        message="Adaptive recovery intelligence model snapshot successfully recomputed and persisted for tenant.",
    )
