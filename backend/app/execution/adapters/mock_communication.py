"""Deterministic Mock Communication Adapter for Phase 4."""

import asyncio
import time
import uuid
from typing import Dict, Any

from app.db.models.payment import Payment
from app.db.models.recovery_action import RecoveryAction
from app.execution.schemas import ProviderResult
from app.core.logging import get_logger

logger = get_logger(__name__)


class MockCommunicationAdapter:
    """Simulates templated customer communications (payment reminders, alternate method requests)."""

    def __init__(self, simulated_latency_ms: int = 150):
        self.simulated_latency_ms = simulated_latency_ms
        self._sent_messages: Dict[str, ProviderResult] = {}

    async def send_message(
        self,
        payment: Payment,
        action: RecoveryAction,
        template_name: str,
        parameters: Dict[str, Any],
        idempotency_key: str,
    ) -> ProviderResult:
        """Send a templated, authorized customer notification."""
        start_time = time.perf_counter()

        if idempotency_key in self._sent_messages:
            return self._sent_messages[idempotency_key]

        if self.simulated_latency_ms > 0:
            await asyncio.sleep(self.simulated_latency_ms / 1000.0)

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        msg_ref = f"msg_{uuid.uuid4().hex[:10]}"

        result = ProviderResult(
            success=True,
            provider_reference=msg_ref,
            provider_status="delivered",
            latency_ms=elapsed_ms,
            raw_payload={
                "message_id": msg_ref,
                "template": template_name,
                "recipient": parameters.get("recipient_email") or "customer@example.com",
                "payment_amount": payment.amount_minor,
                "status": "delivered",
            },
        )
        self._sent_messages[idempotency_key] = result
        logger.info(f"mock_communication_delivered ref={msg_ref} template={template_name}")
        return result
