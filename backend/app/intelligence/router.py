"""API router for Revenue Intelligence with Tenant Isolation."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional
from app.db.session import get_db
from app.intelligence.intelligence_service import IntelligenceService
from app.intelligence.schemas import (
    IntelligenceResult,
    IntelligenceOverview,
    OpportunityListResponse,
    AnalysisRequest,
    PriorityLevel,
    FailureCategory,
)
from app.db.models.payment import Payment
from app.auth.dependencies import get_current_tenant, TenantContext
from app.core.logging import logger

intelligence_router = APIRouter()


@intelligence_router.get("/overview", response_model=IntelligenceOverview)
async def get_intelligence_overview(
    tenant: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Get merchant-level aggregate intelligence overview scoped to tenant."""
    service = IntelligenceService(db)
    return service.get_overview(merchant_id=tenant.merchant.id)


@intelligence_router.get("/opportunities", response_model=OpportunityListResponse)
async def list_opportunities(
    priority: Optional[PriorityLevel] = Query(None, description="Filter by priority level"),
    failure_category: Optional[FailureCategory] = Query(None, description="Filter by failure category"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    tenant: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db),
):
    """List recovery opportunities with filters scoped to authenticated merchant tenant."""
    service = IntelligenceService(db)
    return service.list_opportunities(
        priority=priority,
        failure_category=failure_category,
        merchant_id=tenant.merchant.id,
        page=page,
        page_size=page_size,
    )


@intelligence_router.get("/opportunities/{result_id}", response_model=IntelligenceResult)
async def get_opportunity(
    result_id: str,
    tenant: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Get detailed intelligence result for a specific opportunity scoped to tenant."""
    service = IntelligenceService(db)
    result = service.get_intelligence_result(result_id, merchant_id=tenant.merchant.id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Intelligence result not found in tenant financial records")
    
    return result


@intelligence_router.post("/analyze/{payment_id}", response_model=IntelligenceResult)
async def analyze_payment(
    payment_id: str,
    force_reanalyze: bool = Query(False, description="Force re-analysis even if result exists"),
    tenant: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db),
):
    """
    Run intelligence analysis for a specific payment.
    
    This endpoint only generates intelligence/recommendations.
    It does NOT execute any payment actions.
    """
    # Get payment scoped to tenant
    payment = db.query(Payment).filter(
        Payment.id == payment_id,
        Payment.merchant_id == tenant.merchant.id,
    ).first()
    
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found in tenant financial records")
    
    # Run analysis
    service = IntelligenceService(db)
    result = service.analyze_payment(payment, force_reanalyze=force_reanalyze)
    
    logger.info(f"payment_analysis_completed payment_id={payment_id} merchant_id={tenant.merchant.id}")
    
    return result


@intelligence_router.post("/analyze", response_model=dict)
async def batch_analyze(
    request: AnalysisRequest,
    tenant: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db),
):
    """
    Run batch intelligence analysis scoped to authenticated merchant tenant.
    
    This endpoint only generates intelligence/recommendations.
    It does NOT execute any payment actions.
    """
    service = IntelligenceService(db)
    
    analyzed_count = 0
    errors = []
    
    # Analyze by payment IDs
    if request.payment_ids:
        for payment_id in request.payment_ids:
            try:
                payment = db.query(Payment).filter(
                    Payment.id == payment_id,
                    Payment.merchant_id == tenant.merchant.id,
                ).first()
                if payment:
                    service.analyze_payment(payment, force_reanalyze=request.force_reanalyze)
                    analyzed_count += 1
                else:
                    errors.append(f"Payment not found: {payment_id}")
            except Exception as e:
                errors.append(f"Error analyzing payment {payment_id}: {str(e)}")
                logger.error(f"batch_analysis_error payment_id={payment_id} error={str(e)}")
    
    # Analyze by recovery case IDs
    if request.recovery_case_ids:
        from app.db.models.recovery_case import RecoveryCase
        for case_id in request.recovery_case_ids:
            try:
                recovery_case = db.query(RecoveryCase).join(
                    Payment, RecoveryCase.payment_id == Payment.id
                ).filter(
                    RecoveryCase.id == case_id,
                    Payment.merchant_id == tenant.merchant.id,
                ).first()
                if recovery_case:
                    payment = db.query(Payment).filter(Payment.id == recovery_case.payment_id).first()
                    if payment:
                        service.analyze_payment(payment, force_reanalyze=request.force_reanalyze)
                        analyzed_count += 1
                    else:
                        errors.append(f"Payment not found for recovery case: {case_id}")
                else:
                    errors.append(f"Recovery case not found: {case_id}")
            except Exception as e:
                errors.append(f"Error analyzing recovery case {case_id}: {str(e)}")
                logger.error(f"batch_analysis_error case_id={case_id} error={str(e)}")
    
    logger.info(f"batch_analysis_completed count={analyzed_count} errors={len(errors)} merchant_id={tenant.merchant.id}")
    
    return {
        "analyzed_count": analyzed_count,
        "errors": errors,
    }
