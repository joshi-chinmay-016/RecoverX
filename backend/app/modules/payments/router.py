from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.db.session import get_db
from app.modules.payments.service import PaymentService
from app.modules.payments.schemas import PaymentResponse, PaymentListResponse
from app.db.base import PaymentStatus
from app.core.logging import logger

payment_router = APIRouter()


@payment_router.get("", response_model=PaymentListResponse)
async def list_payments(
    status: Optional[PaymentStatus] = Query(None, description="Filter by payment status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db)
):
    """List payments with filters and pagination."""
    payment_service = PaymentService(db)
    
    payments, total = payment_service.list_payments(
        status=status,
        page=page,
        page_size=page_size
    )
    
    return PaymentListResponse(
        payments=payments,
        total=total,
        page=page,
        page_size=page_size
    )


@payment_router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific payment by ID with attempts and recovery case."""
    payment_service = PaymentService(db)
    
    payment = payment_service.get_payment(payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    return payment