from pydantic import BaseModel, Field
from typing import Optional, List, Any, Union
from uuid import UUID
from datetime import datetime
from app.db.base import PaymentStatus


class PaymentAttemptResponse(BaseModel):
    """Schema for payment attempt response."""
    id: Union[UUID, str]
    payment_id: Union[UUID, str]
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
    id: Union[UUID, str]
    payment_id: Union[UUID, str]
    status: str
    amount_at_risk_minor: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaymentResponse(BaseModel):
    """Schema for payment response."""
    id: Union[UUID, str]
    razorpay_payment_id: str
    razorpay_order_id: Optional[str] = None
    merchant_id: Union[UUID, str]
    customer_id: Optional[Union[UUID, str]] = None
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