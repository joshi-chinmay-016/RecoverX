from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime
from app.db.base import PaymentStatus


class PaymentAttemptResponse(BaseModel):
    """Schema for payment attempt response."""
    id: str
    payment_id: str
    attempt_number: int
    status: str
    failure_code: Optional[str] = None
    failure_description: Optional[str] = None
    method: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class RecoveryCaseResponse(BaseModel):
    """Schema for recovery case response."""
    id: str
    payment_id: str
    status: str
    amount_at_risk_minor: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaymentResponse(BaseModel):
    """Schema for payment response."""
    id: str
    razorpay_payment_id: str
    razorpay_order_id: Optional[str] = None
    merchant_id: str
    customer_id: Optional[str] = None
    amount_minor: int
    currency: str
    status: PaymentStatus
    method: Optional[str] = None
    failure_code: Optional[str] = None
    failure_description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    attempts: List[PaymentAttemptResponse] = []
    recovery_case: Optional[RecoveryCaseResponse] = None

    class Config:
        from_attributes = True


class PaymentListResponse(BaseModel):
    """Schema for paginated payment list."""
    payments: List[PaymentResponse]
    total: int
    page: int
    page_size: int