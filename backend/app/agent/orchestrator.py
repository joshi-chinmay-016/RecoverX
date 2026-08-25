"""Agent Orchestrator for Phase 3 Agent.

Controls the agent loop with bounded steps, read-only tool access, structured output validation,
and deterministic PolicyEngine validation.
"""

import time
import json
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.agent.schemas import (
    AgentState,
    AgentRunStatus,
    RecoveryPlan,
    AgentContext,
    DecisionTrace,
    PolicyStatus,
    ToolCall,
)
from app.agent.context_builder import AgentContextBuilder
from app.agent.llm import get_llm_provider, LLMProvider, LLMMessage
from app.agent.prompts import get_system_prompt, build_recovery_prompt
from app.agent.validation.plan_validator import PlanValidator
from app.agent.policy.engine import PolicyEngine
from app.agent.tools.registry import ToolRegistry
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class AgentOrchestrator:
    """Orchestrates the agent reasoning loop with bounded steps and deterministic validation."""

    def __init__(self, db: Session):
        self.db = db
        self.context_builder = AgentContextBuilder(db)
        self.plan_validator = PlanValidator()
        self.policy_engine = PolicyEngine()
        self.tool_registry = ToolRegistry(db)
        self.max_steps = settings.max_agent_steps
        self.llm_provider = get_llm_provider(settings)

    async def analyze_opportunity(
        self,
        opportunity_id: str,
        payment_id: Optional[str] = None,
    ) -> AgentState:
        """Run the agent on a recovery opportunity."""
        start_time = time.perf_counter()

        # Initialize agent state
        state = AgentState(
            opportunity_id=opportunity_id,
            payment_id=payment_id or "",
            merchant_id="",
            status=AgentRunStatus.INVESTIGATING,
            agent_version=settings.agent_version,
            prompt_version=settings.prompt_version,
            policy_version=settings.policy_version,
        )

        logger.info(
            f"agent_run_started run_id={state.run_id} opportunity_id={opportunity_id} "
            f"agent_version={state.agent_version} policy_version={state.policy_version}"
        )

        try:
            # Step 1: Investigation & Context Gathering via read-only tools
            state.current_step = 1
            logger.info(f"agent_tool_called tool_name=build_context opportunity_id={opportunity_id}")
            tool_start = time.perf_counter()

            state.context = self.context_builder.build_context(opportunity_id)
            state.payment_id = state.context.payment_id
            state.merchant_id = state.context.merchant_id

            tool_duration = int((time.perf_counter() - tool_start) * 1000)
            logger.info(f"agent_tool_completed tool_name=build_context duration_ms={tool_duration}")

            # Record tool call in state
            state.tool_calls.append({
                "tool_name": "build_context",
                "input_summary": json.dumps({"opportunity_id": opportunity_id}),
                "output_summary": json.dumps({
                    "payment_id": state.payment_id,
                    "amount": state.context.payment_amount,
                    "failure_category": state.context.failure_category,
                    "recovery_likelihood": state.context.recovery_likelihood,
                    "priority": state.context.priority,
                }),
                "step_number": 1,
                "execution_time_ms": tool_duration,
            })

            # Add decision trace for investigation
            state.decision_trace.append(
                DecisionTrace(
                    observation=(
                        f"Retrieved context for payment ₹{state.context.payment_amount / 100:.2f}. "
                        f"Failure category: {state.context.failure_category}. "
                        f"Phase 2 recovery likelihood: {state.context.recovery_likelihood * 100:.0f}%, "
                        f"Priority: {state.context.priority}."
                    ),
                    evidence="Context builder successfully consolidated payment, failure, history, and merchant data.",
                    decision="Proceed to adaptive recovery strategy selection.",
                    reason="Sufficient structured domain context available for bounded reasoning.",
                    confidence=1.0,
                )
            )

            state.status = AgentRunStatus.PLANNING

            # Step 2: Run Bounded Agent Loop
            state = await self._run_agent_loop(state)

            total_elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            logger.info(
                f"agent_run_completed run_id={state.run_id} status={state.status.value} "
                f"duration_ms={total_elapsed_ms}"
            )
            return state

        except Exception as e:
            total_elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            logger.error(f"agent_run_failed run_id={state.run_id} error={str(e)} duration_ms={total_elapsed_ms}")
            state.status = AgentRunStatus.FAILED
            state.errors.append(str(e))
            state.completed_at = datetime.utcnow()
            state.proposed_plan = self._create_fallback_plan(state, reason=f"Agent exception: {str(e)}")
            return state

    async def _run_agent_loop(self, state: AgentState) -> AgentState:
        """Run the bounded reasoning loop."""
        state.current_step += 1

        # Check step limit
        if state.current_step > self.max_steps:
            logger.warning(f"max_steps_reached run_id={state.run_id} max_steps={self.max_steps}")
            state.proposed_plan = self._create_fallback_plan(state, reason="Exhausted maximum reasoning steps")
            state.status = AgentRunStatus.COMPLETED
            state.completed_at = datetime.utcnow()
            return state

        prompt = build_recovery_prompt(state.context)

        messages = [
            LLMMessage(role="system", content=get_system_prompt()),
            LLMMessage(role="user", content=prompt),
        ]

        response_schema = {
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "diagnosis": {"type": "string"},
                "selected_strategy": {"type": "string"},
                "reasoning": {"type": "string"},
                "confidence": {"type": "number"},
                "proposed_actions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "action_type": {"type": "string"},
                            "purpose": {"type": "string"},
                            "parameters": {"type": "object"},
                            "rationale": {"type": "string"},
                            "expected_outcome": {"type": "string"},
                            "risk_level": {"type": "string"},
                            "requires_approval": {"type": "boolean"},
                        },
                        "required": ["action_type", "purpose", "rationale", "expected_outcome"],
                    },
                },
                "alternatives_considered": {"type": "array"},
                "required_inputs": {"type": "array"},
                "risks": {"type": "array"},
                "constraints": {"type": "array"},
                "fallback_strategy": {"type": "string"},
                "requires_approval": {"type": "boolean"},
            },
            "required": [
                "summary",
                "diagnosis",
                "selected_strategy",
                "reasoning",
                "confidence",
                "proposed_actions",
                "fallback_strategy",
                "requires_approval",
            ],
        }

        # Call LLM Provider
        llm_start = time.perf_counter()
        try:
            plan_data = await self.llm_provider.generate_structured(
                messages=messages,
                response_schema=response_schema,
                temperature=0.7,
                max_tokens=2000,
            )
            llm_duration = int((time.perf_counter() - llm_start) * 1000)
            logger.info(f"agent_plan_generated run_id={state.run_id} duration_ms={llm_duration}")

        except Exception as e:
            logger.error(f"LLM generation failed for run_id={state.run_id}: {e}")
            state.proposed_plan = self._create_fallback_plan(state, reason=f"LLM generation failed: {str(e)}")
            state.status = AgentRunStatus.COMPLETED
            state.completed_at = datetime.utcnow()
            return state

        # Enrich plan with identifiers
        plan_data["opportunity_id"] = state.opportunity_id
        plan_data["payment_id"] = state.payment_id
        plan_data["merchant_id"] = state.merchant_id

        # Step 3: Structured Schema Validation
        state.status = AgentRunStatus.VALIDATING
        is_valid, error, plan = self.plan_validator.validate_plan(plan_data)

        if not is_valid or plan is None:
            logger.error(f"Plan validation failed: {error}")
            state.errors.append(f"Plan validation error: {error}")
            state.proposed_plan = self._create_fallback_plan(state, reason=f"Plan schema invalid: {error}")
            state.status = AgentRunStatus.COMPLETED
            state.completed_at = datetime.utcnow()
            return state

        logger.info(
            f"agent_strategy_selected run_id={state.run_id} strategy={plan.selected_strategy.value} "
            f"confidence={plan.confidence:.2f}"
        )

        # Step 4: Deterministic Policy Engine Validation
        context_dict = state.context.model_dump()
        policy_status, policy_reason = self.policy_engine.validate_plan(plan, context_dict)

        plan.policy_status = policy_status
        plan.policy_reason = policy_reason

        logger.info(
            f"agent_policy_validated run_id={state.run_id} status={policy_status.value} "
            f"reason={policy_reason or 'None'}"
        )

        if policy_status == PolicyStatus.BLOCKED:
            logger.warning(f"agent_action_blocked run_id={state.run_id} reason={policy_reason}")
            # Replace actions with safe fallback under blocked policy
            plan.selected_strategy = plan.selected_strategy
            state.status = AgentRunStatus.BLOCKED
        else:
            state.status = AgentRunStatus.COMPLETED

        state.proposed_plan = plan
        state.reasoning_summary = plan.reasoning
        state.validation_result = {
            "plan_valid": True,
            "policy_status": policy_status.value,
            "policy_reason": policy_reason,
        }

        # Add decision trace
        state.decision_trace.append(
            DecisionTrace(
                observation=f"Evaluated opportunity strategy {plan.selected_strategy.value}.",
                evidence=f"Confidence: {plan.confidence:.2f}, Policy Validation: {policy_status.value}.",
                decision=plan.selected_strategy.value,
                reason=plan.reasoning,
                confidence=plan.confidence,
            )
        )

        state.completed_at = datetime.utcnow()
        return state

    def _create_fallback_plan(self, state: AgentState, reason: str = "Safe fallback") -> RecoveryPlan:
        """Create a safe deterministic fallback plan when agent reasoning fails or is blocked."""
        from app.agent.schemas import AgentAction, ActionType, RiskLevel

        return RecoveryPlan(
            opportunity_id=state.opportunity_id,
            payment_id=state.payment_id,
            merchant_id=state.merchant_id,
            summary="Escalation to Manual Review (Safe Fallback)",
            diagnosis=f"Automated recovery planner triggered safe fallback: {reason}",
            selected_strategy=ActionType.MANUAL_REVIEW,
            reasoning=f"Automatic escalation to manual review to protect merchant operations and customer trust. Rationale: {reason}",
            confidence=0.0,
            proposed_actions=[
                AgentAction(
                    action_type=ActionType.MANUAL_REVIEW,
                    purpose="Escalate to operations team for human review",
                    parameters={"reason": reason},
                    rationale="Guarantees safe handling when automated planning encounters constraints or exceptions",
                    expected_outcome="Manual review and guided decision by merchant operations",
                    risk_level=RiskLevel.LOW,
                    requires_approval=True,
                )
            ],
            alternatives_considered=[
                {"strategy": "RETRY_PAYMENT", "reason": "Automated retry suppressed by safety fallback"}
            ],
            required_inputs=["merchant_operator_review"],
            risks=["Requires manual staff time"],
            constraints=["Must be reviewed prior to action execution"],
            fallback_strategy="MANUAL_REVIEW",
            requires_approval=True,
            policy_status=PolicyStatus.REQUIRES_APPROVAL,
            policy_reason=f"Safe fallback plan: {reason}",
        )
