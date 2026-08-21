from typing import Optional, List
from sqlalchemy.orm import Session
from app.db.models.recovery_case import RecoveryCase
from app.db.models.payment import Payment
from app.db.base import RecoveryCaseStatus, PaymentStatus
from app.modules.recovery.repository import RecoveryRepository
from app.core.logging import logger


class RecoveryService:
    """Service for recovery case business logic."""
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = RecoveryRepository(db)
    
    def create_recovery_case_for_payment(self, payment: Payment) -> RecoveryCase:
        """Create recovery case for failed payment if one doesn't exist."""
        # Check if recovery case already exists
        existing_case = self.repository.get_by_payment_id(payment.id)
        if existing_case:
            logger.info(f"recovery_case_already_exists payment_id={payment.id}")
            return existing_case
        
        # Create new recovery case
        recovery_case = self.repository.create_recovery_case(
            payment_id=payment.id,
            amount_at_risk_minor=payment.amount_minor
        )
        
        return recovery_case
    
    def resolve_recovery_case(self, payment: Payment) -> Optional[RecoveryCase]:
        """Resolve recovery case when payment is captured."""
        recovery_case = self.repository.get_by_payment_id(payment.id)
        if recovery_case and recovery_case.status == RecoveryCaseStatus.OPEN:
            self.repository.update_status(recovery_case, RecoveryCaseStatus.RESOLVED)
            logger.info(f"recovery_case_resolved payment_id={payment.id}")
            return recovery_case
        return None
    
    def get_recovery_case(self, case_id: str) -> Optional[RecoveryCase]:
        """Get recovery case by ID."""
        return self.repository.get_by_id(case_id)
    
    def list_recovery_cases(
        self,
        status: Optional[RecoveryCaseStatus] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[list[RecoveryCase], int]:
        """List recovery cases with filters."""
        return self.repository.list_recovery_cases(status, page, page_size)