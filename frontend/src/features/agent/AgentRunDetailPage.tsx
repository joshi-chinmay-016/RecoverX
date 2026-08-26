import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { getAgentRun, getAgentTrace } from '@/api/agent';
import { AgentFlowDiagram } from '@/components/agent/AgentFlowDiagram';
import { PolicySafetyCheck } from '@/components/agent/PolicySafetyCheck';
import { ProposedActionCard } from '@/components/agent/ProposedActionCard';
import { DecisionTraceTimeline } from '@/components/agent/DecisionTraceTimeline';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { ErrorState } from '@/components/ui/ErrorState';
import { MetricCardSkeleton } from '@/components/ui/LoadingSkeleton';
import { formatEnum, formatDate } from '@/lib/formatters';
import { ArrowLeft, Layers, Lock } from 'lucide-react';

export const AgentRunDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const {
    data: run,
    isLoading: isRunLoading,
    isError: isRunError,
    error: runError,
    refetch,
  } = useQuery({
    queryKey: ['agent-run', id],
    queryFn: () => getAgentRun(id!),
    enabled: Boolean(id),
  });

  const { data: traceData } = useQuery({
    queryKey: ['agent-trace', id],
    queryFn: () => getAgentTrace(id!),
    enabled: Boolean(id),
  });

  if (isRunLoading) {
    return (
      <div className="space-y-6">
        <MetricCardSkeleton />
        <MetricCardSkeleton />
      </div>
    );
  }

  if (isRunError || !run) {
    return (
      <div className="space-y-4">
        <button
          onClick={() => navigate('/agent')}
          className="text-xs text-gray-400 hover:text-white flex items-center gap-1 cursor-pointer"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Agent Studio
        </button>
        <ErrorState
          title="Agent Run Not Found"
          message={runError instanceof Error ? runError.message : 'Unable to find agent run in backend'}
          onRetry={refetch}
        />
      </div>
    );
  }

  const plan = run.proposed_plan;

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Back Button & Header */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => navigate('/agent')}
          className="text-xs font-semibold text-gray-400 hover:text-white flex items-center gap-1.5 transition-colors cursor-pointer"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Agent Studio
        </button>

        <div className="flex items-center gap-2">
          <StatusBadge status={run.status} />
        </div>
      </div>

      {/* Hero Run Card */}
      <div className="p-6 rounded-2xl bg-surface-card border border-border flex flex-col md:flex-row items-start md:items-center justify-between gap-6 relative overflow-hidden before:absolute before:top-0 before:left-0 before:right-0 before:h-1 before:bg-gradient-to-r before:from-indigo-500 before:via-pink-500 before:to-emerald-500">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="text-[10px] font-mono uppercase font-bold text-indigo-400 bg-indigo-500/15 px-2 py-0.5 rounded border border-indigo-500/30">
              Agent Run Inspection
            </span>
            <span className="font-mono text-xs text-gray-400">ID: {run.run_id}</span>
          </div>
          <h2 className="font-heading font-extrabold text-2xl sm:text-3xl text-white tracking-tight">
            Strategy: {formatEnum(plan?.selected_strategy || 'MANUAL_REVIEW')}
          </h2>
          <p className="text-xs sm:text-sm text-gray-300 mt-1 max-w-2xl">
            {plan?.summary || run.reasoning_summary}
          </p>
        </div>

        <div className="flex items-center gap-8 border-t md:border-t-0 md:border-l border-border pt-4 md:pt-0 md:pl-8 text-xs text-gray-400">
          <div>
            <div>Agent: <strong className="text-white font-mono">{run.agent_version}</strong></div>
            <div>Policy: <strong className="text-white font-mono">{run.policy_version}</strong></div>
          </div>
          <div>
            <div>Started: <strong className="text-white">{formatDate(run.started_at)}</strong></div>
            <div>Completed: <strong className="text-emerald-400">{formatDate(run.completed_at)}</strong></div>
          </div>
        </div>
      </div>

      {/* Plan Flow & Safety Check */}
      {plan && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-surface-card border border-border rounded-2xl p-6 space-y-4">
            <h4 className="font-heading font-bold text-base text-white flex items-center gap-2">
              <Layers className="w-4 h-4 text-indigo-400" />
              Synthesized Recovery Plan
            </h4>
            <AgentFlowDiagram
              proposedActions={plan.proposed_actions || []}
              fallbackStrategy={plan.fallback_strategy}
            />
          </div>

          <div className="space-y-6">
            <PolicySafetyCheck
              policyStatus={plan.policy_status}
              policyReason={plan.policy_reason}
              policyVersion={plan.policy_version}
            />

            {/* Observability Decision Trace */}
            <div className="bg-surface-card border border-border rounded-2xl p-6">
              <DecisionTraceTimeline
                traces={traceData?.decision_trace || run.decision_trace || []}
                toolCalls={traceData?.tool_calls_summary || run.tool_calls_summary || []}
              />
            </div>
          </div>
        </div>
      )}

      {/* Proposed Actions */}
      {plan?.proposed_actions && plan.proposed_actions.length > 0 && (
        <div className="space-y-4">
          <h4 className="font-heading font-bold text-base text-white">
            Action Item Breakdown
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {plan.proposed_actions.map((action, idx) => (
              <ProposedActionCard key={idx} action={action} index={idx} />
            ))}
          </div>
        </div>
      )}

      {/* Execution Boundary Disclaimer */}
      <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-center text-xs font-bold text-amber-300 flex items-center justify-center gap-2">
        <Lock className="w-4 h-4" /> PLAN ARCHIVED — ACTION EXECUTION HELD UNDER SAFETY POLICY
      </div>
    </div>
  );
};
