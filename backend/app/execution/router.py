"""FastAPI Router for Phase 4 Controlled Action Execution Endpoints (Protected with RBAC & Multi-Tenancy)."""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.base import UserRole
from app.auth.dependencies import get_current_tenant, require_role, TenantContext
from app.execution.service import ExecutionService
from app.execution.schemas import (
    CreateActionRequest,
    AuthorizeActionRequest,
    ExecuteActionRequest,
    RecoveryActionResponse,
    ExecutionResultResponse,
    PaginatedRecoveryActionResponse,
    PolicyDecision,
)
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/actions", tags=["Recovery Execution"])


@router.post("/create-from-plan/{opportunity_id}", response_model=List[RecoveryActionResponse])
def create_actions_from_plan(
    opportunity_id: str,
    tenant: TenantContext = Depends(require_role([UserRole.ADMIN, UserRole.OPERATOR])),
    db: Session = Depends(get_db),
):
    """Synthesize structured recovery actions from an approved Phase 3 Agent Recovery Plan scoped to tenant."""
    from app.db.models.revenue_intelligence import RevenueIntelligenceResult
    from app.db.models.payment import Payment
    import uuid

    try:
        opp_uuid = uuid.UUID(str(opportunity_id))
    except (ValueError, TypeError):
        raise HTTPException(status_code=404, detail="Opportunity not found in tenant financial records.")

    intel = db.query(RevenueIntelligenceResult).join(
        Payment, RevenueIntelligenceResult.payment_id == Payment.id
    ).filter(
        RevenueIntelligenceResult.id == opp_uuid,
        Payment.merchant_id == tenant.merchant.id,
    ).first()

    if not intel:
        raise HTTPException(status_code=404, detail="Opportunity not found in tenant financial records.")

    service = ExecutionService(db)
    try:
        actions = service.create_actions_from_plan(opportunity_id)
        return actions
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"create_actions_from_plan_failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=RecoveryActionResponse, status_code=status.HTTP_201_CREATED)
def create_action(
    request: CreateActionRequest,
    tenant: TenantContext = Depends(require_role([UserRole.ADMIN, UserRole.OPERATOR])),
    db: Session = Depends(get_db),
):
    """Create a new proposed recovery action scoped to tenant."""
    from app.db.models.revenue_intelligence import RevenueIntelligenceResult
    from app.db.models.payment import Payment
    import uuid

    try:
        opp_uuid = uuid.UUID(str(request.opportunity_id))
    except (ValueError, TypeError):
        raise HTTPException(status_code=404, detail="Opportunity not found in tenant financial records.")

    intel = db.query(RevenueIntelligenceResult).join(
        Payment, RevenueIntelligenceResult.payment_id == Payment.id
    ).filter(
        RevenueIntelligenceResult.id == opp_uuid,
        Payment.merchant_id == tenant.merchant.id,
    ).first()

    if not intel:
        raise HTTPException(status_code=404, detail="Opportunity not found in tenant financial records.")

    service = ExecutionService(db)
    try:
        action = service.create_action(
            opportunity_id=str(request.opportunity_id),
            action_type=request.action_type,
            parameters=request.parameters,
            recovery_plan_id=request.recovery_plan_id,
            agent_run_id=request.agent_run_id,
            merchant_id=str(tenant.merchant.id),
        )
        return action
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"create_action_failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{action_id}/authorize", response_model=Dict[str, Any])
def authorize_action(
    action_id: str,
    request: AuthorizeActionRequest = AuthorizeActionRequest(),
    tenant: TenantContext = Depends(require_role([UserRole.ADMIN, UserRole.OPERATOR])),
    db: Session = Depends(get_db),
):
    """Evaluate deterministic PolicyEngine guardrails and update action authorization status."""
    service = ExecutionService(db)
    action_record = service.get_action(action_id)
    if action_record and action_record.merchant_id != tenant.merchant.id:
        raise HTTPException(status_code=404, detail="Recovery action not found in tenant financial records.")

    try:
        action, decision = service.authorize_action(
            action_id=action_id,
            force_reevaluate=request.force_reevaluate,
        )
        return {
            "action": RecoveryActionResponse.model_validate(action).model_dump(mode="json"),
            "decision": decision.model_dump(mode="json"),
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"authorize_action_failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{action_id}/execute", response_model=ExecutionResultResponse)
async def execute_action(
    action_id: str,
    request: Optional[ExecuteActionRequest] = None,
    tenant: TenantContext = Depends(require_role([UserRole.ADMIN, UserRole.OPERATOR])),
    db: Session = Depends(get_db),
):
    """Securely execute an authorized recovery action through the adapter layer."""
    service = ExecutionService(db)
    
    # IDOR / Tenant verification
    action_record = service.get_action(action_id)
    if action_record and action_record.merchant_id != tenant.merchant.id:
        raise HTTPException(status_code=404, detail="Recovery action not found in tenant financial records.")

    req = request or ExecuteActionRequest()
    try:
        result = await service.execute_action(
            action_id=action_id,
            custom_idempotency_key=req.idempotency_key,
            simulation_override=req.simulation_override,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"execute_action_failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{action_id}/retry", response_model=ExecutionResultResponse)
async def retry_action(
    action_id: str,
    request: Optional[ExecuteActionRequest] = None,
    tenant: TenantContext = Depends(require_role([UserRole.ADMIN, UserRole.OPERATOR])),
    db: Session = Depends(get_db),
):
    """Retry an action that is currently in RETRYABLE status."""
    service = ExecutionService(db)
    action_record = service.get_action(action_id)
    if action_record and action_record.merchant_id != tenant.merchant.id:
        raise HTTPException(status_code=404, detail="Recovery action not found in tenant financial records.")

    req = request or ExecuteActionRequest()
    try:
        result = await service.execute_action(
            action_id=action_id,
            custom_idempotency_key=req.idempotency_key,
            simulation_override=req.simulation_override,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"retry_action_failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{action_id}/reconcile", response_model=RecoveryActionResponse)
async def reconcile_action(
    action_id: str,
    tenant: TenantContext = Depends(require_role([UserRole.ADMIN, UserRole.OPERATOR])),
    db: Session = Depends(get_db),
):
    """Reconcile an action with UNKNOWN outcome by querying provider status."""
    service = ExecutionService(db)
    action_record = service.get_action(action_id)
    if action_record and action_record.merchant_id != tenant.merchant.id:
        raise HTTPException(status_code=404, detail="Recovery action not found in tenant financial records.")

    try:
        action = await service.reconcile_action(action_id)
        return action
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"reconcile_action_failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{action_id}/cancel", response_model=RecoveryActionResponse)
def cancel_action(
    action_id: str,
    reason: str = Query("Cancelled by operator"),
    tenant: TenantContext = Depends(require_role([UserRole.ADMIN, UserRole.OPERATOR])),
    db: Session = Depends(get_db),
):
    """Cancel a proposed, authorized, or pending recovery action."""
    service = ExecutionService(db)
    action_record = service.get_action(action_id)
    if action_record and action_record.merchant_id != tenant.merchant.id:
        raise HTTPException(status_code=404, detail="Recovery action not found in tenant financial records.")

    try:
        action = service.cancel_action(action_id, reason=reason)
        return action
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"cancel_action_failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{action_id}", response_model=RecoveryActionResponse)
def get_action(
    action_id: str,
    tenant: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db),
):
    """Get recovery action details and attempt history by ID."""
    service = ExecutionService(db)
    try:
        action = service.get_action(action_id)
        if not action or action.merchant_id != tenant.merchant.id:
            raise HTTPException(status_code=404, detail="Recovery action not found in tenant records.")
        return action
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("", response_model=PaginatedRecoveryActionResponse)
def list_actions(
    status: Optional[str] = Query(None, description="Filter by action status"),
    action_type: Optional[str] = Query(None, description="Filter by action type"),
    opportunity_id: Optional[str] = Query(None, description="Filter by opportunity ID"),
    payment_id: Optional[str] = Query(None, description="Filter by payment ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Page size"),
    limit: Optional[int] = Query(None, ge=1, le=100),
    tenant: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db),
):
    """List recovery actions scoped to the authenticated tenant."""
    service = ExecutionService(db)
    effective_page_size = limit or page_size
    actions, total = service.list_actions(
        merchant_id=str(tenant.merchant.id),
        status=status,
        action_type=action_type,
        opportunity_id=opportunity_id,
        payment_id=payment_id,
        page=page,
        page_size=effective_page_size,
    )
    return {
        "items": actions,
        "total": total,
        "page": page,
        "page_size": effective_page_size,
    }
