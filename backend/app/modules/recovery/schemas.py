from pydantic import BaseModel, Field
from typing import Optional, List, Any, Union
from uuid import UUID
from datetime import datetime
from app.db.base import RecoveryCaseStatus


class RecoveryCaseResponse(BaseModel):
    """Schema for recovery case response."""
    id: Union[UUID, str]
    payment_id: Union[UUID, str]
    status: RecoveryCaseStatus
    amount_at_risk_minor: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RecoveryCaseListResponse(BaseModel):
    """Schema for paginated recovery case list."""
    cases: List[RecoveryCaseResponse]
    total: int
    page: int
    page_size: int