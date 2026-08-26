import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import { listOpportunities } from '@/api/opportunities';
import { analyzeOpportunity, previewOpportunity, listAgentRuns } from '@/api/agent';
import { createActionsFromPlan } from '@/api/actions';
import { AgentRunResponse } from '@/types/agent';
import { RecoveryAction } from '@/types/action';
import { AgentFlowDiagram } from '@/components/agent/AgentFlowDiagram';
import { PolicySafetyCheck } from '@/components/agent/PolicySafetyCheck';
import { ProposedActionCard } from '@/components/agent/ProposedActionCard';
import { ActionExecutionCard } from '@/components/execution/ActionExecutionCard';
import { DecisionTraceTimeline } from '@/components/agent/DecisionTraceTimeline';
import { PriorityBadge } from '@/components/ui/PriorityBadge';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { formatCurrency, formatEnum, formatDate } from '@/lib/formatters';
import {
  Bot,
  Play,
  Eye,
  CheckCircle2,
  Lock,
  Sparkles,
  RefreshCw,
  History,
  Zap,
} from 'lucide-react';

export const AgentStudioPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const initialOppId = searchParams.get('opportunityId') || '';
  const [selectedOppId, setSelectedOppId] = useState<string>(initialOppId);

  const [activeStep, setActiveStep] = useState<number>(0);
  const [agentResult, setAgentResult] = useState<AgentRunResponse | null>(null);
  const [createdActions, setCreatedActions] = useState<RecoveryAction[]>([]);
  const [isCreatingActions, setIsCreatingActions] = useState<boolean>(false);

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
      setCreatedActions([]);
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
      setCreatedActions([]);
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
    setCreatedActions([]);
    setActiveStep(0);
  };

  const handleCreateExecutionActions = async () => {
    if (!selectedOppId) return;
    setIsCreatingActions(true);
    try {
      const actions = await createActionsFromPlan(selectedOppId);
      setCreatedActions(actions);
    } catch (err) {
      console.error('Failed to create actions from plan', err);
    } finally {
      setIsCreatingActions(false);
    }
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
            <Lock className="w-3.5 h-3.5" /> Policy-Gated Execution
          </span>
        </div>
      </div>

      {/* Target Opportunity Selector & Controls */}
      <section className="bg-surface-card border border-border rounded-2xl p-6 space-y-6">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-border">
          <div className="space-y-1 flex-1">
            <label className="text-xs font-semibold text-gray-300 uppercase tracking-wider font-mono">
              Select Target Recovery Opportunity:
            </label>
            <select
              value={selectedOppId}
              onChange={(e) => handleSelectOpportunity(e.target.value)}
              disabled={isRunning}
              className="w-full bg-surface-solid border border-border rounded-xl px-4 py-2.5 text-sm text-white font-mono focus:outline-none focus:border-indigo-500 cursor-pointer"
            >
              {oppsData?.opportunities.map((opp) => (
                <option key={opp.id} value={opp.id}>
                  {opp.payment_id} | {opp.failure_category} | {formatCurrency(opp.revenue_at_risk)} | Score: {opp.opportunity_score} ({opp.priority})
                </option>
              ))}
            </select>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={() => analyzeMutation.mutate(selectedOppId)}
              disabled={isRunning || !selectedOppId}
              className="flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-500 to-pink-500 hover:from-indigo-400 hover:to-pink-400 text-white font-heading font-extrabold text-xs shadow-lg shadow-indigo-500/25 active:scale-95 transition-all cursor-pointer disabled:opacity-50"
            >
              {analyzeMutation.isPending ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  <span>Investigating...</span>
                </>
              ) : (
                <>
                  <Play className="w-3.5 h-3.5 fill-current" />
                  <span>Run Agent Investigation</span>
                </>
              )}
            </button>

            <button
              onClick={() => previewMutation.mutate(selectedOppId)}
              disabled={isRunning || !selectedOppId}
              className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-surface-solid hover:bg-white/5 border border-border text-gray-200 font-semibold text-xs transition-all cursor-pointer disabled:opacity-50"
            >
              <Eye className="w-3.5 h-3.5 text-indigo-400" />
              <span>Dry-Run Preview</span>
            </button>
          </div>
        </div>

        {/* Selected Opportunity Snapshot Card */}
        {currentOpportunity && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-2 text-xs font-mono">
            <div className="p-3.5 rounded-xl bg-surface-solid border border-border">
              <span className="text-gray-400 block text-[10px] uppercase font-semibold">Revenue at Risk</span>
              <span className="font-bold text-sm text-white mt-0.5 block">
                {formatCurrency(currentOpportunity.revenue_at_risk)}
              </span>
            </div>

            <div className="p-3.5 rounded-xl bg-surface-solid border border-border">
              <span className="text-gray-400 block text-[10px] uppercase font-semibold">Failure Root Cause</span>
              <span className="font-bold text-sm text-indigo-300 mt-0.5 block truncate">
                {formatEnum(currentOpportunity.failure_category)}
              </span>
            </div>

            <div className="p-3.5 rounded-xl bg-surface-solid border border-border">
              <span className="text-gray-400 block text-[10px] uppercase font-semibold">Recovery Likelihood</span>
              <span className="font-bold text-sm text-emerald-400 mt-0.5 block">
                {Math.round(currentOpportunity.recovery_probability * 100)}%
              </span>
            </div>

            <div className="p-3.5 rounded-xl bg-surface-solid border border-border">
              <span className="text-gray-400 block text-[10px] uppercase font-semibold">Opportunity Score</span>
              <div className="flex items-center gap-2 mt-0.5">
                <span className="font-bold text-sm text-white">{currentOpportunity.opportunity_score}/100</span>
                <PriorityBadge priority={currentOpportunity.priority} />
              </div>
            </div>
          </div>
        )}
      </section>

      {/* 4-Step Animated Pipeline Visualizer */}
      <section className="bg-surface-card border border-border rounded-2xl p-6 space-y-4">
        <h3 className="font-heading font-bold text-base text-white flex items-center gap-2">
          <Bot className="w-4 h-4 text-pink-400" />
          Autonomous 4-Step Reasoning Pipeline
        </h3>
        <AgentFlowDiagram activeStep={activeStep} />
      </section>

      {/* Agent Analysis Results */}
      {agentResult && agentResult.plan && (
        <div className="space-y-6 animate-fade-in">
          {/* Strategy & Policy Evaluation Header Card */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 p-6 rounded-2xl bg-surface-card border border-border space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono uppercase tracking-wider text-gray-400 font-semibold flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  Synthesized Recovery Plan
                </span>
                <span className="text-xs font-mono px-2.5 py-1 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 font-bold">
                  Confidence: {Math.round((agentResult.confidence || 0.85) * 100)}%
                </span>
              </div>

              <div>
                <h3 className="font-heading font-extrabold text-xl text-white">
                  Strategy: {formatEnum(agentResult.selected_strategy || 'RETRY_PAYMENT')}
                </h3>
                <p className="text-xs sm:text-sm text-gray-300 mt-2 leading-relaxed">
                  {agentResult.plan.summary}
                </p>
              </div>

              <div className="p-4 rounded-xl bg-surface-solid border border-border text-xs space-y-1.5">
                <span className="font-semibold text-gray-400 uppercase text-[10px]">Diagnosis:</span>
                <p className="text-gray-200 leading-relaxed font-mono text-[11px]">
                  {agentResult.plan.diagnosis}
                </p>
              </div>
            </div>

            {/* Deterministic Policy Check Card */}
            <PolicySafetyCheck
              policyStatus={agentResult.policy_status || 'ALLOWED'}
              requiresApproval={agentResult.plan.requires_approval}
              confidence={agentResult.confidence || 0.85}
            />
          </div>

          {/* Decision Trace Timeline */}
          {(agentResult.plan as any)?.decision_trace && (agentResult.plan as any).decision_trace.length > 0 && (
            <DecisionTraceTimeline traces={(agentResult.plan as any).decision_trace} />
          )}

          {/* Proposed Actions Specifications */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h4 className="font-heading font-bold text-base text-white">
                Proposed Actions Specifications
              </h4>
              <button
                onClick={handleCreateExecutionActions}
                disabled={isCreatingActions}
                className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-gradient-to-r from-pink-500 to-indigo-500 hover:from-pink-400 hover:to-indigo-400 text-white font-extrabold text-xs shadow-md transition-all cursor-pointer disabled:opacity-50"
              >
                <Zap className="w-3.5 h-3.5" />
                <span>{isCreatingActions ? 'Authorizing Actions...' : 'Prepare Controlled Execution'}</span>
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {(agentResult.plan.proposed_actions || []).map((action, idx) => (
                <ProposedActionCard key={idx} action={action} index={idx} />
              ))}
            </div>
          </div>

          {/* Created Recovery Actions for Interactive Execution */}
          {createdActions.length > 0 && (
            <div className="space-y-4 pt-4 border-t border-border animate-fade-in">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-heading font-bold text-base text-emerald-300 flex items-center gap-2">
                    <Zap className="w-4 h-4 text-emerald-400" />
                    Policy-Gated Execution Ready
                  </h4>
                  <p className="text-xs text-gray-400 mt-0.5">
                    Authorized actions generated from the recovery plan ready for safe dispatch via MockPaymentAdapter.
                  </p>
                </div>
              </div>

              <div className="space-y-4">
                {createdActions.map((act) => (
                  <ActionExecutionCard
                    key={act.id}
                    action={act}
                    onUpdated={() => refetchRuns()}
                  />
                ))}
              </div>
            </div>
          )}
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
