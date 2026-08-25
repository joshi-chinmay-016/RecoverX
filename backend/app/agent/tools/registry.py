"""Tool Registry for Phase 3 AI Recovery Agent.

Manages safe, read-only tools that the agent is allowed to execute during reasoning.
Enforces read-only boundaries and records execution metrics for audit trails.
"""

import time
import json
from typing import Dict, Any, Callable, Optional
from sqlalchemy.orm import Session

from app.agent.tools.payment_context import get_payment_context
from app.agent.tools.recovery_history import get_recovery_history
from app.agent.tools.intelligence import get_revenue_intelligence
from app.agent.tools.merchant_context import get_merchant_context
from app.agent.tools.policy import get_recovery_policy
from app.agent.tools.allowed_actions import get_allowed_actions
from app.core.logging import get_logger

logger = get_logger(__name__)


class ToolRegistry:
    """Registry of safe, read-only tools available to the Recovery Agent."""

    def __init__(self, db: Session):
        self.db = db
        self._tools: Dict[str, Callable] = {
            "get_payment_context": self._run_get_payment_context,
            "get_recovery_history": self._run_get_recovery_history,
            "get_revenue_intelligence": self._run_get_revenue_intelligence,
            "get_merchant_context": self._run_get_merchant_context,
            "get_recovery_policy": self._run_get_recovery_policy,
            "get_allowed_actions": self._run_get_allowed_actions,
        }

    def list_tools(self) -> Dict[str, str]:
        """Return list of available read-only tool names and descriptions."""
        return {
            "get_payment_context": "Retrieve normalized payment and attempt context (payment_id required)",
            "get_recovery_history": "Retrieve recovery case history and prior attempts (payment_id required)",
            "get_revenue_intelligence": "Retrieve Phase 2 revenue intelligence and risk scoring (opportunity_id or payment_id required)",
            "get_merchant_context": "Retrieve merchant aggregate statistics and recovery rates (merchant_id required)",
            "get_recovery_policy": "Retrieve current deterministic policy rules and limits",
            "get_allowed_actions": "Retrieve list of all allowed recovery actions and schemas",
        }

    def is_tool_allowed(self, tool_name: str) -> bool:
        """Check if tool is in the read-only whitelist."""
        return tool_name in self._tools

    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a read-only tool with timing and audit logging."""
        if not self.is_tool_allowed(tool_name):
            error_msg = f"Tool '{tool_name}' is not allowed or does not exist."
            logger.warning(f"unauthorized_tool_request tool_name={tool_name}")
            return {
                "success": False,
                "tool_name": tool_name,
                "error": error_msg,
                "output": None,
                "execution_time_ms": 0,
            }

        start_time = time.perf_counter()
        logger.info(f"agent_tool_called tool_name={tool_name} params={parameters}")

        try:
            handler = self._tools[tool_name]
            result = handler(parameters or {})
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            
            logger.info(f"agent_tool_completed tool_name={tool_name} duration_ms={elapsed_ms}")
            return {
                "success": True,
                "tool_name": tool_name,
                "output": result,
                "input_summary": json.dumps(parameters or {}),
                "output_summary": json.dumps(result)[:1000] if result else "",
                "execution_time_ms": elapsed_ms,
            }

        except Exception as e:
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            logger.error(f"agent_tool_failed tool_name={tool_name} error={str(e)}")
            return {
                "success": False,
                "tool_name": tool_name,
                "error": str(e),
                "input_summary": json.dumps(parameters or {}),
                "output_summary": str(e),
                "execution_time_ms": elapsed_ms,
            }

    # Tool Handlers
    def _run_get_payment_context(self, params: Dict[str, Any]) -> Dict[str, Any]:
        payment_id = params.get("payment_id")
        if not payment_id:
            raise ValueError("Missing required parameter: payment_id")
        return get_payment_context(self.db, str(payment_id))

    def _run_get_recovery_history(self, params: Dict[str, Any]) -> Dict[str, Any]:
        payment_id = params.get("payment_id")
        if not payment_id:
            raise ValueError("Missing required parameter: payment_id")
        return get_recovery_history(self.db, str(payment_id))

    def _run_get_revenue_intelligence(self, params: Dict[str, Any]) -> Dict[str, Any]:
        identifier = params.get("opportunity_id") or params.get("payment_id")
        if not identifier:
            raise ValueError("Missing parameter: opportunity_id or payment_id")
        return get_revenue_intelligence(self.db, str(identifier))

    def _run_get_merchant_context(self, params: Dict[str, Any]) -> Dict[str, Any]:
        merchant_id = params.get("merchant_id")
        if not merchant_id:
            raise ValueError("Missing required parameter: merchant_id")
        return get_merchant_context(self.db, str(merchant_id))

    def _run_get_recovery_policy(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return get_recovery_policy(params)

    def _run_get_allowed_actions(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return get_allowed_actions(params)
