"""Execution Adapter Protocols and Base Interfaces for Phase 4."""

from typing import Protocol, Dict, Any, Optional
from app.db.models.payment import Payment
from app.db.models.recovery_action import RecoveryAction
from app.execution.schemas import ProviderResult


class PaymentExecutionAdapter(Protocol):
    """Adapter interface for executing payment retries and payment-related actions."""

    async def execute_retry(
        self,
        payment: Payment,
        action: RecoveryAction,
        attempt_number: int,
        idempotency_key: str,
        simulation_override: Optional[str] = None,
    ) -> ProviderResult:
        """Execute a payment retry against the payment gateway or mock adapter."""
        ...

    async def check_transaction_status(
        self,
        provider_reference: str,
    ) -> ProviderResult:
        """Check status of a transaction for reconciliation."""
        ...


class CommunicationAdapter(Protocol):
    """Adapter interface for customer notifications and payment reminder links."""

    async def send_message(
        self,
        payment: Payment,
        action: RecoveryAction,
        template_name: str,
        parameters: Dict[str, Any],
        idempotency_key: str,
    ) -> ProviderResult:
        """Send a structured, approved customer notification."""
        ...
