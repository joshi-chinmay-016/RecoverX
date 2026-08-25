"""Mock LLM Provider for Phase 3 Testing and Demonstrations."""

from typing import Dict, Any, List, Optional
from app.agent.llm.base import LLMProvider, LLMMessage, LLMResponse
from app.core.logging import get_logger

logger = get_logger(__name__)


class MockLLMProvider(LLMProvider):
    """Deterministic Mock LLM provider for testing and offline environments."""

    def __init__(self, api_key: str = "mock-key", model: str = "mock-model", timeout_seconds: int = 5):
        super().__init__(api_key=api_key, model=model, timeout_seconds=timeout_seconds)

    async def generate(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Generate a mock textual response."""
        return LLMResponse(
            content="Analysis complete. Recommended strategy: WAIT_AND_RETRY based on transient failure characteristics.",
            finish_reason="stop",
            usage={"prompt_tokens": 120, "completion_tokens": 40, "total_tokens": 160},
        )

    async def generate_structured(
        self,
        messages: List[LLMMessage],
        response_schema: Dict[str, Any],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Generate a realistic, context-aware structured JSON recovery plan."""
        # Find user message content to inspect context
        user_content = ""
        for msg in messages:
            if msg.role == "user":
                user_content += msg.content + "\n"

        content_lower = user_content.lower()

        # Context-aware heuristics for realistic mock behavior matching prompt requirements:
        if "insufficient_funds" in content_lower or "insufficient funds" in content_lower:
            selected_strategy = "REQUEST_ALTERNATE_PAYMENT_METHOD"
            summary = "Customer had insufficient funds; requesting alternative payment method (card, netbanking, or alternate UPI ID)."
            diagnosis = "Transaction failed due to insufficient funds in primary account. Immediate retry will likely fail."
            reasoning = "Because the failure is balance-related, retrying the same method immediately is ineffective. Prompting for an alternative payment method provides the highest recovery likelihood."
            proposed_actions = [
                {
                    "action_type": "REQUEST_ALTERNATE_PAYMENT_METHOD",
                    "purpose": "Offer alternative payment methods to the customer",
                    "parameters": {"suggested_methods": ["card", "netbanking", "upi_alternate"]},
                    "rationale": "Directs customer to a funded payment instrument",
                    "expected_outcome": "Customer completes payment with alternative method",
                    "risk_level": "LOW",
                    "requires_approval": False,
                }
            ]
            alternatives_considered = [
                {"strategy": "RETRY_PAYMENT", "reason": "Immediate retry ineffective due to balance constraints"},
                {"strategy": "MANUAL_REVIEW", "reason": "Automated alternative payment request is low risk and faster"}
            ]
            confidence = 0.85

        elif "retry count: 3" in content_lower or "retry count: 4" in content_lower or "3 previous" in content_lower:
            selected_strategy = "MANUAL_REVIEW"
            summary = "Multiple retry attempts already exhausted. Escalating to human operations for manual review."
            diagnosis = "Payment has repeatedly failed across multiple attempts. Continued automated retries risk merchant policy violation."
            reasoning = "Retry limit reached. Escalating to manual review ensures policy compliance and protects customer experience."
            proposed_actions = [
                {
                    "action_type": "MANUAL_REVIEW",
                    "purpose": "Escalate to merchant support team for review",
                    "parameters": {"reason": "Exhausted maximum retry threshold"},
                    "rationale": "Human review required after repeated automated failures",
                    "expected_outcome": "Support agent contacts customer or resolves billing issue",
                    "risk_level": "LOW",
                    "requires_approval": True,
                }
            ]
            alternatives_considered = [
                {"strategy": "RETRY_PAYMENT", "reason": "Blocked by policy limit on maximum retry attempts"},
                {"strategy": "WAIT_AND_RETRY", "reason": "Repeated failures indicate persistent problem"}
            ]
            confidence = 0.90

        elif "authentication_failure" in content_lower or "otp" in content_lower or "3ds" in content_lower:
            selected_strategy = "REQUEST_REAUTHENTICATION"
            summary = "Customer failed 3D-Secure or OTP challenge. Requesting re-authentication session."
            diagnosis = "Payment failed during customer authentication step (OTP timeout or 3DS challenge)."
            reasoning = "Authentication failures are customer-actionable. Triggering a fresh re-authentication link allows quick completion."
            proposed_actions = [
                {
                    "action_type": "REQUEST_REAUTHENTICATION",
                    "purpose": "Send secure re-authentication link to customer",
                    "parameters": {"auth_method": "3ds_otp"},
                    "rationale": "Enables customer to complete 2FA verification",
                    "expected_outcome": "Successful payment authorization following OTP verification",
                    "risk_level": "MEDIUM",
                    "requires_approval": False,
                }
            ]
            alternatives_considered = [
                {"strategy": "RETRY_PAYMENT", "reason": "Backend retry cannot bypass customer 2FA requirement"}
            ]
            confidence = 0.88

        elif "low-value" in content_lower or "amount: ₹3" in content_lower or "amount: ₹5" in content_lower or "amount: ₹50" in content_lower:
            selected_strategy = "SEND_PAYMENT_REMINDER"
            summary = "Low-value transaction failure. Sending subtle non-intrusive reminder."
            diagnosis = "Low transaction value with moderate recovery probability."
            reasoning = "A gentle notification minimizes customer friction while recovering revenue."
            proposed_actions = [
                {
                    "action_type": "SEND_PAYMENT_REMINDER",
                    "purpose": "Send gentle reminder notification",
                    "parameters": {"reminder_type": "gentle"},
                    "rationale": "Cost-effective recovery for low-value transaction",
                    "expected_outcome": "Customer voluntarily re-attempts checkout",
                    "risk_level": "LOW",
                    "requires_approval": True,
                }
            ]
            alternatives_considered = [
                {"strategy": "ESCALATE", "reason": "Disproportionate operational cost for low-value transaction"}
            ]
            confidence = 0.75

        else:
            # Default / Transient failure
            selected_strategy = "WAIT_AND_RETRY"
            summary = "Temporary bank/gateway outage detected. Staggered retry recommended."
            diagnosis = "Transient processing error or temporary gateway timeout. Underlying account is valid."
            reasoning = "High recovery likelihood for temporary failures when retried after downstream bank systems recover."
            proposed_actions = [
                {
                    "action_type": "WAIT_AND_RETRY",
                    "purpose": "Wait for upstream bank recovery then retry payment",
                    "parameters": {"delay_minutes": 30},
                    "rationale": "Allows downstream banking systems to recover from temporary downtime",
                    "expected_outcome": "Payment captured on subsequent attempt",
                    "risk_level": "LOW",
                    "requires_approval": False,
                }
            ]
            alternatives_considered = [
                {"strategy": "RETRY_PAYMENT", "reason": "Immediate retry risks hitting same temporary bank outage"},
                {"strategy": "MANUAL_REVIEW", "reason": "Premature manual escalation for standard transient failure"}
            ]
            confidence = 0.85

        return {
            "summary": summary,
            "diagnosis": diagnosis,
            "selected_strategy": selected_strategy,
            "reasoning": reasoning,
            "confidence": confidence,
            "proposed_actions": proposed_actions,
            "alternatives_considered": alternatives_considered,
            "required_inputs": ["merchant_credentials", "payment_attempt_id"],
            "risks": ["Potential repeated failure if bank outage persists"],
            "constraints": ["Must adhere to max retry limits and merchant policy"],
            "fallback_strategy": "MANUAL_REVIEW",
            "requires_approval": any(a.get("requires_approval", False) for a in proposed_actions),
        }

    def validate_connection(self) -> bool:
        """Mock connection is always valid."""
        return True
