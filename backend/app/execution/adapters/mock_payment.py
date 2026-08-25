"""Deterministic Mock Payment Execution Adapter for Phase 4."""

import asyncio
import time
import uuid
from typing import Optional, Dict, Any

from app.db.models.payment import Payment
from app.db.models.recovery_action import RecoveryAction
from app.execution.schemas import ProviderResult
from app.core.logging import get_logger

logger = get_logger(__name__)


class MockPaymentAdapter:
    """Deterministic simulation adapter for payment execution."""

    def __init__(self, simulated_latency_ms: int = 250):
        self.simulated_latency_ms = simulated_latency_ms
        # In-memory store of executed idempotency keys and mock transactions
        self._executed_transactions: Dict[str, ProviderResult] = {}

    async def execute_retry(
        self,
        payment: Payment,
        action: RecoveryAction,
        attempt_number: int,
        idempotency_key: str,
        simulation_override: Optional[str] = None,
    ) -> ProviderResult:
        """Execute a simulated payment retry with deterministic behavior."""
        start_time = time.perf_counter()

        # Check idempotency cache within adapter
        if idempotency_key in self._executed_transactions:
            cached_result = self._executed_transactions[idempotency_key]
            logger.info(f"mock_adapter_idempotency_hit key={idempotency_key} ref={cached_result.provider_reference}")
            return cached_result

        # Simulate network latency
        if self.simulated_latency_ms > 0:
            await asyncio.sleep(self.simulated_latency_ms / 1000.0)

        # Determine outcome mode
        mode = simulation_override or (action.parameters or {}).get("simulation_mode")

        if not mode:
            # Infer from failure code or attempt count
            failure_code = (payment.failure_code or "").upper()
            if "TIMEOUT" in failure_code or "NETWORK" in failure_code:
                mode = "SUCCESS" if attempt_number <= 2 else "TEMPORARY_FAILURE"
            elif "EXPIRED" in failure_code or "FRAUD" in failure_code:
                mode = "PERMANENT_FAILURE"
            else:
                mode = "SUCCESS"

        mode = mode.upper()
        elapsed_ms = int((time.perf_counter() - start_time) * 1000)

        if mode == "SUCCESS":
            provider_ref = f"mock_pay_{uuid.uuid4().hex[:12]}"
            result = ProviderResult(
                success=True,
                provider_reference=provider_ref,
                provider_status="captured",
                latency_ms=elapsed_ms,
                raw_payload={
                    "id": provider_ref,
                    "entity": "payment",
                    "amount": payment.amount_minor,
                    "currency": payment.currency,
                    "status": "captured",
                    "method": payment.method or "card",
                    "captured": True,
                    "attempt": attempt_number,
                },
            )
            self._executed_transactions[idempotency_key] = result
            self._executed_transactions[provider_ref] = result
            logger.info(f"mock_payment_succeeded ref={provider_ref} amount={payment.amount_minor} attempt={attempt_number}")
            return result

        elif mode == "TEMPORARY_FAILURE":
            result = ProviderResult(
                success=False,
                error_code="GATEWAY_TEMPORARY_ERROR",
                error_message="Downstream bank gateway unavailable. Retry recommended after backoff.",
                is_retryable=True,
                is_unknown=False,
                latency_ms=elapsed_ms,
                raw_payload={"error": {"code": "BAD_REQUEST_ERROR", "description": "Bank network glitch"}},
            )
            logger.warning(f"mock_payment_temporary_failure action_id={action.action_id} attempt={attempt_number}")
            return result

        elif mode == "PERMANENT_FAILURE":
            result = ProviderResult(
                success=False,
                error_code="PAYMENT_INSTRUMENT_DECLINED",
                error_message="Customer card has expired or reached permanent card limit.",
                is_retryable=False,
                is_unknown=False,
                latency_ms=elapsed_ms,
                raw_payload={"error": {"code": "BAD_REQUEST_ERROR", "description": "Instrument declined"}},
            )
            logger.warning(f"mock_payment_permanent_failure action_id={action.action_id} attempt={attempt_number}")
            return result

        elif mode == "TIMEOUT":
            # Simulate provider timeout without confirmed terminal state
            result = ProviderResult(
                success=False,
                error_code="PROVIDER_TIMEOUT",
                error_message="Gateway connection timed out after 30000ms. Result unconfirmed.",
                is_retryable=False,
                is_unknown=True,
                latency_ms=elapsed_ms,
                raw_payload={"error": {"code": "GATEWAY_TIMEOUT", "description": "Transaction status unverified"}},
            )
            logger.error(f"mock_payment_timeout action_id={action.action_id} attempt={attempt_number}")
            return result

        else:
            # Default fallback to SUCCESS
            provider_ref = f"mock_pay_{uuid.uuid4().hex[:12]}"
            result = ProviderResult(
                success=True,
                provider_reference=provider_ref,
                provider_status="captured",
                latency_ms=elapsed_ms,
            )
            self._executed_transactions[idempotency_key] = result
            return result

    async def check_transaction_status(self, provider_reference: str) -> ProviderResult:
        """Query mock provider for transaction status during reconciliation."""
        if provider_reference in self._executed_transactions:
            return self._executed_transactions[provider_reference]
        
        # If unknown, simulate confirmed capture
        return ProviderResult(
            success=True,
            provider_reference=provider_reference,
            provider_status="captured",
            latency_ms=50,
            raw_payload={"status": "captured", "reconciled": True},
        )
