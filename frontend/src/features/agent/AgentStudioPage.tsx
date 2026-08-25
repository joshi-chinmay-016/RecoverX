import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import { listOpportunities } from '@/api/opportunities';
import { analyzeOpportunity, previewOpportunity, listAgentRuns } from '@/api/agent';
import { AgentRunResponse } from '@/types/agent';
import { AgentFlowDiagram } from '@/components/agent/AgentFlowDiagram';
import { PolicySafetyCheck } from '@/components/agent/PolicySafetyCheck';
import { ProposedActionCard } from '@/components/agent/ProposedActionCard';
import { DecisionTraceTimeline } from '@/components/agent/DecisionTraceTimeline';
import { PriorityBadge } from '@/components/ui/PriorityBadge';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { ErrorState } from '@/components/ui/ErrorState';
import { EmptyState } from '@/components/ui/EmptyState';
import { formatCurrency, formatEnum, formatDate } from '@/lib/formatters';
import {
  Bot,
  Play,
  Eye,
  CheckCircle2,
  Lock,
  Layers,
  Sparkles,
  RefreshCw,
  Clock,
  History,
  ShieldCheck,
} from 'lucide-react';

export const AgentStudioPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const initialOppId = searchParams.get('opportunityId') || '';
  const [selectedOppId, setSelectedOppId] = useState<string>(initialOppId);

  const [activeStep, setActiveStep] = useState<number>(0);
  const [agentResult, setAgentResult] = useState<AgentRunResponse | null>(null);

  // Load all opportunities for the selector dropdown
  const { data: oppsData } = useQuery({
    queryKey: ['opportunities-all'],
    queryFn: () => listOpportunities({ page: 1, page_size: 50 }),
  });

  // Load recent agent runs history
  const {
    data: runsData,
    refetch: refetchRuns,
  } = useQuery({
    queryKey: ['agent-runs-history'],
    queryFn: () => listAgentRuns(1, 10),
  });

  useEffect(() => {
    if (initialOppId) {
      setSelectedOppId(initialOppId);
    } else if (oppsData?.opportunities && oppsData.opportunities.length > 0 && !selectedOppId) {
      setSelectedOppId(oppsData.opportunities[0].id);
    }
  }, [initialOppId, oppsData]);

  // Mutation for running full agent analysis
  const analyzeMutation = useMutation({
    mutationFn: (oppId: string) => analyzeOpportunity(oppId, true),
    onMutate: () => {
      setActiveStep(1);
      setAgentResult(null);
    },
    onSuccess: (data) => {
      setActiveStep(4);
      setAgentResult(data);
      refetchRuns();
    },
    onError: () => {
      setActiveStep(0);
    },
  });

  // Mutation for dry-run preview
  const previewMutation = useMutation({
    mutationFn: (oppId: string) => previewOpportunity(oppId),
    onMutate: () => {
      setActiveStep(1);
      setAgentResult(null);
    },
    onSuccess: (data) => {
      setActiveStep(4);
      setAgentResult(data);
    },
    onError: () => {
      setActiveStep(0);
    },
  });

  const isRunning = analyzeMutation.isPending || previewMutation.isPending;
  const currentOpportunity = oppsData?.opportunities.find((o) => o.id === selectedOppId);

  const handleSelectOpportunity = (id: string) => {
    setSelectedOppId(id);
    setSearchParams({ opportunityId: id });
    setAgentResult(null);
    setActiveStep(0);
  };

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] font-mono font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-pink-500/20 text-pink-300 border border-pink-500/30 flex items-center gap-1">
              <Sparkles className="w-3 h-3" /> Autonomous Reasoning
            </span>
            <span className="text-xs text-gray-400 font-mono">Agent Version: agent-v1</span>
          </div>
          <h2 className="font-heading font-extrabold text-2xl sm:text-3xl text-white tracking-tight">
            AI Recovery Agent Studio
          </h2>
          <p className="text-xs sm:text-sm text-gray-400 mt-1">
            Bounded AI reasoning over failed payments with strict deterministic PolicyEngine safety checks.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-mono px-3 py-1.5 rounded-xl bg-amber-500/10 text-amber-300 border border-amber-500/30 flex items-center gap-1.5">
            <Lock className="w-3.5 h-3.5" /> Action Execution Disabled
          </span>
        </div>
      </div>

      {/* Opportunity Target Selector Toolbar */}
      <div className="p-5 rounded-2xl bg-surface-card border border-border flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex-1 w-full md:w-auto">
          <label className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider block mb-1.5">
            Select Opportunity Target
          </label>
          <select
            value={selectedOppId}
            onChange={(e) => handleSelectOpportunity(e.target.value)}
            disabled={isRunning}
            className="w-full bg-surface-solid border border-border rounded-xl px-3.5 py-2.5 text-xs text-white focus:outline-none focus:border-indigo-500 cursor-pointer font-mono"
          >
            {oppsData?.opportunities.map((opp) => (
              <option key={opp.id} value={opp.id}>
                {opp.payment_id.substring(0, 14)}... — {formatCurrency(opp.revenue_at_risk)} [{opp.priority}] — {formatEnum(opp.failure_category)}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-3 shrink-0 self-end md:self-auto">
          <button
            onClick={() => selectedOppId && previewMutation.mutate(selectedOppId)}
            disabled={isRunning || !selectedOppId}
            className="px-4 py-2.5 bg-surface-solid hover:bg-white/10 text-gray-200 border border-border rounded-xl text-xs font-semibold flex items-center gap-2 transition-all cursor-pointer disabled:opacity-40"
          >
            <Eye className="w-4 h-4 text-indigo-400" />
            <span>Dry-Run Preview</span>
          </button>

          <button
            onClick={() => selectedOppId && analyzeMutation.mutate(selectedOppId)}
            disabled={isRunning || !selectedOppId}
            className="px-5 py-2.5 bg-gradient-to-r from-indigo-600 to-pink-600 hover:from-indigo-500 hover:to-pink-500 text-white rounded-xl text-xs font-bold flex items-center gap-2 shadow-lg shadow-indigo-500/25 transition-all cursor-pointer disabled:opacity-40"
          >
            <Play className={`w-4 h-4 ${isRunning ? 'animate-spin' : ''}`} />
            <span>Run Agent Investigation</span>
          </button>
        </div>
      </div>

      {/* Target Preview Pill */}
      {currentOpportunity && (
        <div className="p-4 rounded-xl bg-surface-solid/60 border border-border flex flex-wrap items-center justify-between gap-4 text-xs">
          <div className="flex items-center gap-3">
            <span className="text-gray-400">Target Payment:</span>
            <span className="font-mono text-indigo-300 font-bold">{currentOpportunity.payment_id}</span>
            <PriorityBadge priority={currentOpportunity.priority} />
          </div>
          <div className="flex items-center gap-6">
            <div>
              Revenue: <strong className="text-white">{formatCurrency(currentOpportunity.revenue_at_risk)}</strong>
            </div>
            <div>
              Failure: <span className="text-gray-300">{formatEnum(currentOpportunity.failure_category)}</span>
            </div>
            <div>
              Likelihood: <strong className="text-emerald-400">{Math.round(currentOpportunity.recovery_probability * 100)}%</strong>
            </div>
          </div>
        </div>
      )}

      {/* Live Agent Execution Progress Timeline */}
      {isRunning && (
        <div className="p-6 rounded-2xl bg-surface-card border border-indigo-500/40 space-y-4 animate-pulse">
          <h3 className="font-heading font-bold text-sm text-white flex items-center gap-2">
            <RefreshCw className="w-4 h-4 text-indigo-400 animate-spin" />
            Agent Autonomous Reasoning in Progress...
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 text-xs">
            <div className="p-3 rounded-xl bg-indigo-500/10 border border-indigo-500/30 text-indigo-200">
              <div className="font-bold font-mono">Step 1</div>
              <div>Context Gathering & Read-Only Tools</div>
            </div>
            <div className="p-3 rounded-xl bg-indigo-500/10 border border-indigo-500/30 text-indigo-200">
              <div className="font-bold font-mono">Step 2</div>
              <div>LLM Strategy Selection & Plan Synthesis</div>
            </div>
            <div className="p-3 rounded-xl bg-indigo-500/10 border border-indigo-500/30 text-indigo-200">
              <div className="font-bold font-mono">Step 3</div>
              <div>Deterministic PolicyEngine Validation</div>
            </div>
            <div className="p-3 rounded-xl bg-indigo-500/10 border border-indigo-500/30 text-indigo-200">
              <div className="font-bold font-mono">Step 4</div>
              <div>Decision Trace & Run Persistence</div>
            </div>
          </div>
        </div>
      )}

      {/* Errors if any */}
      {(analyzeMutation.isError || previewMutation.isError) && (
        <ErrorState
          title="Agent Execution Failed"
          message={
            (analyzeMutation.error as any)?.message ||
            (previewMutation.error as any)?.message ||
            'Error during agent reasoning'
          }
          onRetry={() => selectedOppId && analyzeMutation.mutate(selectedOppId)}
        />
      )}

      {/* Results View */}
      {agentResult?.plan && (
        <div className="space-y-6 animate-slide-up">
          {/* Strategy Hero Banner */}
          <div className="p-6 rounded-2xl bg-surface-card border border-border flex flex-col md:flex-row items-start md:items-center justify-between gap-6 relative overflow-hidden before:absolute before:top-0 before:left-0 before:right-0 before:h-1 before:bg-gradient-to-r before:from-indigo-500 before:to-pink-500">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <span className="text-[10px] font-mono uppercase font-bold text-pink-400 bg-pink-500/15 px-2 py-0.5 rounded border border-pink-500/30">
                  AI Strategy Decision
                </span>
                <StatusBadge status={agentResult.plan.policy_status} />
              </div>
              <h3 className="font-heading font-extrabold text-2xl sm:text-3xl text-white tracking-tight">
                {formatEnum(agentResult.plan.selected_strategy)}
              </h3>
              <p className="text-xs sm:text-sm text-gray-300 mt-1 max-w-2xl">
                {agentResult.plan.summary}
              </p>
            </div>

            <div className="flex items-center gap-6 border-t md:border-t-0 md:border-l border-border pt-4 md:pt-0 md:pl-6">
              <div className="text-center">
                <div className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-1">
                  Agent Confidence
                </div>
                <div className="font-heading font-bold text-2xl text-emerald-400">
                  {Math.round((agentResult.plan.confidence || 0.85) * 100)}%
                </div>
              </div>
            </div>
          </div>

          {/* Reasoning & Evidence ("Why?") */}
          <div className="bg-surface-card border border-border rounded-2xl p-6 space-y-3">
            <h4 className="font-heading font-bold text-sm text-white flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-indigo-400" />
              Agent Diagnostic Rationale & Evidence (Why?)
            </h4>
            <p className="text-xs sm:text-sm text-gray-200 leading-relaxed bg-surface-solid p-4 rounded-xl border border-border">
              {agentResult.plan.reasoning}
            </p>
          </div>

          {/* Flow Diagram & Policy Validation */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Flowchart */}
            <div className="bg-surface-card border border-border rounded-2xl p-6 space-y-4">
              <h4 className="font-heading font-bold text-sm text-white flex items-center gap-2">
                <Layers className="w-4 h-4 text-indigo-400" />
                Structured Recovery Plan Flow
              </h4>
              <AgentFlowDiagram
                proposedActions={agentResult.plan.proposed_actions || []}
                fallbackStrategy={agentResult.plan.fallback_strategy}
              />
            </div>

            {/* Policy Safety Check */}
            <div className="space-y-6">
              <PolicySafetyCheck
                policyStatus={agentResult.plan.policy_status}
                policyReason={agentResult.plan.policy_reason}
                policyVersion={agentResult.plan.policy_version}
              />

              {/* Alternatives Considered */}
              <div className="bg-surface-card border border-border rounded-2xl p-5 space-y-3">
                <h4 className="font-heading font-bold text-xs text-gray-300 uppercase tracking-wider">
                  Alternative Strategies Evaluated & Rejected
                </h4>
                <div className="space-y-2 text-xs">
                  {agentResult.plan.alternatives_considered && agentResult.plan.alternatives_considered.length > 0 ? (
                    agentResult.plan.alternatives_considered.map((alt, idx) => (
                      <div key={idx} className="p-2.5 rounded-xl bg-white/5 border border-border flex justify-between gap-2">
                        <span className="font-semibold text-amber-300">
                          {formatEnum(alt.strategy || alt.action_type || '')}:
                        </span>
                        <span className="text-gray-400 text-right">{alt.reason}</span>
                      </div>
                    ))
                  ) : (
                    <div className="text-gray-500 text-xs">None recorded.</div>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Proposed Actions Breakdown */}
          <div className="space-y-4">
            <h4 className="font-heading font-bold text-base text-white">
              Proposed Actions Specifications
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {(agentResult.plan.proposed_actions || []).map((action, idx) => (
                <ProposedActionCard key={idx} action={action} index={idx} />
              ))}
            </div>
          </div>

          {/* Safety Policy Disclaimer Banner */}
          <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-center text-xs font-bold text-amber-300 tracking-wide flex items-center justify-center gap-2">
            <Lock className="w-4 h-4" /> PLAN SYNTHESIZED AND VALIDATED — AUTOMATED EXECUTION HELD UNDER SAFETY POLICY
          </div>
        </div>
      )}

      {/* Historical Agent Runs List */}
      <section className="bg-surface-card border border-border rounded-2xl p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-heading font-bold text-base text-white flex items-center gap-2">
            <History className="w-4 h-4 text-indigo-400" />
            Agent Run History
          </h3>
          <span className="text-xs font-mono text-gray-400">
            Total Runs: {runsData?.total || 0}
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-border text-gray-400 uppercase text-[10px] tracking-wider font-semibold">
                <th className="pb-3 px-3">Run ID</th>
                <th className="pb-3 px-3">Target Payment</th>
                <th className="pb-3 px-3">Strategy</th>
                <th className="pb-3 px-3">Policy Status</th>
                <th className="pb-3 px-3">Status</th>
                <th className="pb-3 px-3">Timestamp</th>
                <th className="pb-3 px-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {!runsData?.runs || runsData.runs.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-6 text-center text-gray-500">
                    No previous agent runs recorded. Click "Run Agent Investigation" above.
                  </td>
                </tr>
              ) : (
                runsData.runs.map((run) => (
                  <tr key={run.run_id} className="hover:bg-white/5 transition-colors">
                    <td className="py-3.5 px-3 font-mono text-indigo-300 font-semibold">
                      {run.run_id.substring(0, 10)}...
                    </td>
                    <td className="py-3.5 px-3 font-mono text-gray-300">
                      {run.payment_id.substring(0, 10)}...
                    </td>
                    <td className="py-3.5 px-3 font-bold text-white">
                      {formatEnum(run.selected_strategy || 'MANUAL_REVIEW')}
                    </td>
                    <td className="py-3.5 px-3">
                      <StatusBadge status={run.policy_status || 'ALLOWED'} />
                    </td>
                    <td className="py-3.5 px-3">
                      <span className="font-mono text-emerald-400 text-[11px]">{run.status}</span>
                    </td>
                    <td className="py-3.5 px-3 text-gray-400">
                      {formatDate(run.created_at || run.started_at)}
                    </td>
                    <td className="py-3.5 px-3 text-right">
                      <button
                        onClick={() => navigate(`/agent/runs/${run.run_id}`)}
                        className="px-2.5 py-1 bg-white/5 hover:bg-white/10 text-gray-200 rounded-lg text-xs font-semibold inline-flex items-center gap-1 cursor-pointer transition-colors"
                      >
                        <Eye className="w-3 h-3" /> View Trace
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
};
