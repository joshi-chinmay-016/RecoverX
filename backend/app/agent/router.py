"""API Router for Phase 3 Agent with Tenant Isolation."""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from typing import Optional
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.agent.orchestrator import AgentOrchestrator
from app.agent.schemas import (
    AgentRunRequest,
    AgentRunResponse,
    AgentState,
    AgentRunStatus,
    RecoveryPlan,
    PolicyStatus,
)
from app.db.models.agent_run import AgentRun as AgentRunModel
from app.db.models.revenue_intelligence import RevenueIntelligenceResult
from app.db.models.payment import Payment
from app.auth.dependencies import get_current_tenant, TenantContext
from app.core.logging import get_logger
import json
from datetime import datetime

logger = get_logger(__name__)

router = APIRouter()
agent_router = router


@router.post("/analyze/{opportunity_id}", response_model=AgentRunResponse)
async def analyze_opportunity(
    opportunity_id: str,
    request: Optional[AgentRunRequest] = None,
    background_tasks: BackgroundTasks = None,
    tenant: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db),
):
    req = request or AgentRunRequest()
    """Run the AI recovery agent on an opportunity scoped to authenticated tenant."""
    import uuid
    try:
        opp_uuid = uuid.UUID(str(opportunity_id))
    except (ValueError, TypeError):
        raise HTTPException(status_code=404, detail="Opportunity not found in tenant financial records")
    
    # Check if intelligence result exists and belongs to tenant
    intelligence = db.query(RevenueIntelligenceResult).join(
        Payment, RevenueIntelligenceResult.payment_id == Payment.id
    ).filter(
        RevenueIntelligenceResult.id == opp_uuid,
        Payment.merchant_id == tenant.merchant.id,
    ).first()
    
    if not intelligence:
        raise HTTPException(status_code=404, detail="Opportunity not found in tenant financial records")
    
    # Check for existing run
    existing_run = db.query(AgentRunModel).filter(
        AgentRunModel.opportunity_id == str(opportunity_id),
        AgentRunModel.merchant_id == str(tenant.merchant.id),
        AgentRunModel.status.in_([AgentRunStatus.INVESTIGATING, AgentRunStatus.PLANNING, AgentRunStatus.VALIDATING]),
    ).first()
    
    if existing_run and not req.force_reanalyze:
        return AgentRunResponse(
            run_id=existing_run.run_id,
            status=existing_run.status,
            error="Agent run already in progress",
        )
    
    # Create orchestrator
    orchestrator = AgentOrchestrator(db)
    
    # Run agent
    try:
        state = await orchestrator.analyze_opportunity(opportunity_id)
        
        # Persist agent run
        agent_run = AgentRunModel(
            run_id=state.run_id,
            opportunity_id=str(state.opportunity_id),
            payment_id=str(state.payment_id),
            merchant_id=str(tenant.merchant.id),
            current_step=state.current_step,
            status=state.status,
            context=state.context.model_dump(mode="json") if state.context else None,
            tool_calls_summary=state.tool_calls,
            reasoning_summary=state.reasoning_summary,
            decision_trace=[t.model_dump(mode="json") for t in state.decision_trace],
            proposed_plan=state.proposed_plan.model_dump(mode="json") if state.proposed_plan else None,
            validation_result=state.validation_result,
            errors=state.errors,
            started_at=state.started_at,
            completed_at=state.completed_at,
            agent_version=state.agent_version,
            prompt_version=state.prompt_version,
            policy_version=state.policy_version,
        )
        
        db.add(agent_run)
        db.flush()

        # Persist individual tool calls
        from app.db.models.agent_run import AgentToolCall as AgentToolCallModel
        for tc in state.tool_calls:
            tool_call_record = AgentToolCallModel(
                run_id=state.run_id,
                agent_run_id=agent_run.id,
                tool_name=tc.get("tool_name", "unknown"),
                input_summary=tc.get("input_summary"),
                output_summary=tc.get("output_summary"),
                step_number=tc.get("step_number", 1),
                execution_time_ms=tc.get("execution_time_ms", 0),
            )
            db.add(tool_call_record)

        db.commit()
        db.refresh(agent_run)
        
        return AgentRunResponse(
            run_id=state.run_id,
            status=state.status,
            selected_strategy=state.proposed_plan.selected_strategy.value if state.proposed_plan else None,
            confidence=state.proposed_plan.confidence if state.proposed_plan else None,
            plan=state.proposed_plan,
            decision_summary=state.reasoning_summary,
            policy_status=state.proposed_plan.policy_status if state.proposed_plan else None,
            error=state.errors[0] if state.errors else None,
        )
        
    except Exception as e:
        logger.error(f"Agent analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/runs", response_model=dict)
async def list_agent_runs(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    opportunity_id: Optional[str] = Query(None, description="Filter by opportunity ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    tenant: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db),
):
    """List agent runs scoped to authenticated merchant tenant."""
    query = db.query(AgentRunModel).filter(AgentRunModel.merchant_id == str(tenant.merchant.id))
    
    if opportunity_id:
        query = query.filter(AgentRunModel.opportunity_id == str(opportunity_id))
    if status:
        query = query.filter(AgentRunModel.status == status)
        
    total = query.count()
    offset = (page - 1) * page_size
    runs = query.order_by(AgentRunModel.created_at.desc()).offset(offset).limit(page_size).all()
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "runs": [
            {
                "run_id": r.run_id,
                "opportunity_id": r.opportunity_id,
                "payment_id": r.payment_id,
                "merchant_id": r.merchant_id,
                "status": r.status.value if hasattr(r.status, "value") else str(r.status),
                "current_step": r.current_step,
                "selected_strategy": (r.proposed_plan or {}).get("selected_strategy") if r.proposed_plan else None,
                "confidence": (r.proposed_plan or {}).get("confidence") if r.proposed_plan else None,
                "policy_status": (r.proposed_plan or {}).get("policy_status") if r.proposed_plan else None,
                "agent_version": r.agent_version,
                "prompt_version": r.prompt_version,
                "policy_version": r.policy_version,
                "started_at": r.started_at.isoformat() if r.started_at else None,
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in runs
        ]
    }


@router.get("/runs/{run_id}", response_model=dict)
async def get_agent_run(
    run_id: str,
    tenant: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db),
):
    """Get an agent run by ID scoped to tenant."""
    agent_run = db.query(AgentRunModel).filter(
        AgentRunModel.run_id == run_id,
        AgentRunModel.merchant_id == str(tenant.merchant.id),
    ).first()
    
    if not agent_run:
        raise HTTPException(status_code=404, detail="Agent run not found in tenant records")
    
    return {
        "run_id": agent_run.run_id,
        "opportunity_id": agent_run.opportunity_id,
        "payment_id": agent_run.payment_id,
        "merchant_id": agent_run.merchant_id,
        "status": agent_run.status.value,
        "current_step": agent_run.current_step,
        "context": agent_run.context,
        "tool_calls_summary": agent_run.tool_calls_summary,
        "reasoning_summary": agent_run.reasoning_summary,
        "decision_trace": agent_run.decision_trace,
        "proposed_plan": agent_run.proposed_plan,
        "validation_result": agent_run.validation_result,
        "errors": agent_run.errors,
        "started_at": agent_run.started_at.isoformat() if agent_run.started_at else None,
        "completed_at": agent_run.completed_at.isoformat() if agent_run.completed_at else None,
        "agent_version": agent_run.agent_version,
        "prompt_version": agent_run.prompt_version,
        "policy_version": agent_run.policy_version,
    }


@router.get("/runs/{run_id}/trace", response_model=dict)
async def get_agent_trace(
    run_id: str,
    tenant: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db),
):
    """Get decision trace and tool activity for an agent run scoped to tenant."""
    agent_run = db.query(AgentRunModel).filter(
        AgentRunModel.run_id == run_id,
        AgentRunModel.merchant_id == str(tenant.merchant.id),
    ).first()
    
    if not agent_run:
        raise HTTPException(status_code=404, detail="Agent run not found in tenant records")
    
    return {
        "run_id": agent_run.run_id,
        "decision_trace": agent_run.decision_trace,
        "tool_calls_summary": agent_run.tool_calls_summary,
        "reasoning_summary": agent_run.reasoning_summary,
    }


@router.post("/preview/{opportunity_id}", response_model=AgentRunResponse)
async def preview_opportunity(
    opportunity_id: str,
    tenant: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db),
):
    """Generate a plan without execution (dry run / preview) scoped to tenant."""
    import uuid
    try:
        opp_uuid = uuid.UUID(str(opportunity_id))
    except (ValueError, TypeError):
        raise HTTPException(status_code=404, detail="Opportunity not found in tenant financial records")

    intelligence = db.query(RevenueIntelligenceResult).join(
        Payment, RevenueIntelligenceResult.payment_id == Payment.id
    ).filter(
        RevenueIntelligenceResult.id == opp_uuid,
        Payment.merchant_id == tenant.merchant.id,
    ).first()
    
    if not intelligence:
        raise HTTPException(status_code=404, detail="Opportunity not found in tenant financial records")
    
    # Create orchestrator
    orchestrator = AgentOrchestrator(db)
    
    # Run agent (same as analyze, but labeled as preview)
    try:
        state = await orchestrator.analyze_opportunity(opportunity_id)
        
        return AgentRunResponse(
            run_id=state.run_id,
            status=state.status,
            selected_strategy=state.proposed_plan.selected_strategy.value if state.proposed_plan else None,
            confidence=state.proposed_plan.confidence if state.proposed_plan else None,
            plan=state.proposed_plan,
            decision_summary=state.reasoning_summary,
            policy_status=state.proposed_plan.policy_status if state.proposed_plan else None,
            error=state.errors[0] if state.errors else None,
        )
        
    except Exception as e:
        logger.error(f"Agent preview failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/policy", response_model=dict)
async def get_policy(
    tenant: TenantContext = Depends(get_current_tenant),
):
    """Get current policy configuration."""
    from app.agent.policy.engine import PolicyEngine
    
    policy_engine = PolicyEngine()
    return policy_engine.get_policy_summary()
