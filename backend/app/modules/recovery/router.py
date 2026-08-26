from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.db.session import get_db
from app.modules.recovery.service import RecoveryService
from app.modules.recovery.schemas import RecoveryCaseResponse, RecoveryCaseListResponse
from app.db.base import RecoveryCaseStatus
from app.auth.dependencies import get_current_tenant, TenantContext
from app.core.logging import logger

recovery_router = APIRouter()


@recovery_router.get("/cases", response_model=RecoveryCaseListResponse)
async def list_recovery_cases(
    status: Optional[RecoveryCaseStatus] = Query(None, description="Filter by recovery case status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    tenant: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """List recovery cases with filters and pagination scoped to authenticated merchant tenant."""
    recovery_service = RecoveryService(db)
    
    cases, total = recovery_service.list_recovery_cases(
        status=status,
        merchant_id=tenant.merchant.id,
        page=page,
        page_size=page_size
    )
    
    return RecoveryCaseListResponse(
        cases=cases,
        total=total,
        page=page,
        page_size=page_size
    )


@recovery_router.get("/cases/{case_id}", response_model=RecoveryCaseResponse)
async def get_recovery_case(
    case_id: str,
    tenant: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Get a specific recovery case by ID scoped to authenticated merchant tenant."""
    recovery_service = RecoveryService(db)
    
    case = recovery_service.get_recovery_case(case_id, merchant_id=tenant.merchant.id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recovery case not found in tenant financial records"
        )
    
    return case