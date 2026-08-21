from typing import Optional, List
from sqlalchemy.orm import Session
from app.db.models.recovery_case import RecoveryCase
from app.db.base import RecoveryCaseStatus
from app.core.logging import logger


class RecoveryRepository:
    """Repository for recovery case operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_payment_id(self, payment_id: str) -> Optional[RecoveryCase]:
        """Get recovery case by payment ID."""
        return self.db.query(RecoveryCase).filter(
            RecoveryCase.payment_id == payment_id
        ).first()
    
    def get_by_id(self, case_id: str) -> Optional[RecoveryCase]:
        """Get recovery case by ID."""
        return self.db.query(RecoveryCase).filter(
            RecoveryCase.id == case_id
        ).first()
    
    def create_recovery_case(
        self,
        payment_id: str,
        amount_at_risk_minor: int
    ) -> RecoveryCase:
        """Create a new recovery case."""
        recovery_case = RecoveryCase(
            payment_id=payment_id,
            status=RecoveryCaseStatus.OPEN,
            amount_at_risk_minor=amount_at_risk_minor
        )
        
        self.db.add(recovery_case)
        self.db.commit()
        self.db.refresh(recovery_case)
        
        logger.info(f"recovery_case_created payment_id={payment_id}")
        return recovery_case
    
    def update_status(self, recovery_case: RecoveryCase, new_status: RecoveryCaseStatus) -> None:
        """Update recovery case status."""
        recovery_case.status = new_status
        self.db.commit()
        logger.info(
            f"recovery_case_status_updated "
            f"case_id={recovery_case.id} "
            f"new_status={new_status}"
        )
    
    def list_recovery_cases(
        self,
        status: Optional[RecoveryCaseStatus] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[list[RecoveryCase], int]:
        """List recovery cases with filters and pagination."""
        query = self.db.query(RecoveryCase)
        
        if status:
            query = query.filter(RecoveryCase.status == status)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        cases = query.order_by(RecoveryCase.created_at.desc()).offset(offset).limit(page_size).all()
        
        return cases, total