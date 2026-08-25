import React, { useState } from 'react';
import { Play, Shield, ShieldAlert, ShieldCheck, RefreshCw, Lock, Zap, Clock, Terminal } from 'lucide-react';
import { RecoveryAction, ExecutionResultResponse } from '@/types/action';
import { executeAction, authorizeAction, reconcileAction, retryAction } from '@/api/actions';
import { ExecutionResultBanner } from './ExecutionResultBanner';
import { formatEnum } from '@/lib/formatters';

interface ActionExecutionCardProps {
  action: RecoveryAction;
  onUpdated?: () => void;
}

export const ActionExecutionCard: React.FC<ActionExecutionCardProps> = ({ action, onUpdated }) => {
  const [currentAction, setCurrentAction] = useState<RecoveryAction>(action);
  const [isAuthorizing, setIsAuthorizing] = useState(false);
  const [isExecuting, setIsExecuting] = useState(false);
  const [isReconciling, setIsReconciling] = useState(false);
  const [simulationOverride, setSimulationOverride] = useState<string>('');
  const [lastResult, setLastResult] = useState<ExecutionResultResponse | null>(null);

  const handleAuthorize = async () => {
    setIsAuthorizing(true);
    try {
      const res = await authorizeAction(currentAction.action_id, true);
      setCurrentAction(res.action);
      if (onUpdated) onUpdated();
    } catch (err) {
      console.error('Authorization failed', err);
    } finally {
      setIsAuthorizing(false);
    }
  };

  const handleExecute = async () => {
    setIsExecuting(true);
    setLastResult(null);
    try {
      const res = await executeAction(
        currentAction.action_id,
        simulationOverride ? simulationOverride : undefined
      );
      setLastResult(res);
      // Refresh action state
      if (onUpdated) onUpdated();
    } catch (err) {
      console.error('Execution failed', err);
    } finally {
      setIsExecuting(false);
    }
  };

  const handleReconcile = async () => {
    setIsReconciling(true);
    try {
      const updated = await reconcileAction(currentAction.action_id);
      setCurrentAction(updated);
      setLastResult({
        action_id: updated.action_id,
        status: updated.status,
        success: updated.status === 'SUCCEEDED',
        recovered_amount_minor: updated.payment_id ? 2500000 : null,
        provider_reference: updated.provider_reference,
        latency_ms: 45,
        attempt_number: updated.execution_attempts_count,
        is_retryable: false,
        is_unknown: false,
        message: updated.status === 'SUCCEEDED' ? 'Action successfully reconciled with gateway: CAPTURED' : 'Reconciliation confirmed failure.',
      });
      if (onUpdated) onUpdated();
    } catch (err) {
      console.error('Reconciliation failed', err);
    } finally {
      setIsReconciling(false);
    }
  };

  const isTerminal = ['SUCCEEDED', 'BLOCKED', 'CANCELLED'].includes(currentAction.status);
  const isAllowed = currentAction.status === 'AUTHORIZED' || currentAction.status === 'RETRYABLE';

  return (
    <div className="p-6 rounded-2xl bg-surface-card border border-border space-y-5 hover:border-indigo-500/30 transition-all">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border pb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center font-bold">
            <Zap className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-heading font-extrabold text-base text-white">
                {formatEnum(currentAction.action_type)}
              </span>
              <span className="font-mono text-[10px] bg-white/5 text-gray-400 px-2 py-0.5 rounded border border-border">
                {currentAction.action_id}
              </span>
            </div>
            <span className="text-xs text-gray-400 font-mono mt-0.5 block">
              Idempotency: {currentAction.idempotency_key}
            </span>
          </div>
        </div>

        {/* Status Badge */}
        <div className="flex items-center gap-2">
          {currentAction.status === 'SUCCEEDED' ? (
            <span className="px-3 py-1 rounded-xl text-xs font-mono font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5" /> SUCCEEDED
            </span>
          ) : currentAction.status === 'AUTHORIZED' ? (
            <span className="px-3 py-1 rounded-xl text-xs font-mono font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5" /> AUTHORIZED
            </span>
          ) : currentAction.status === 'BLOCKED' ? (
            <span className="px-3 py-1 rounded-xl text-xs font-mono font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30 flex items-center gap-1.5">
              <ShieldAlert className="w-3.5 h-3.5" /> BLOCKED
            </span>
          ) : currentAction.status === 'UNKNOWN' ? (
            <span className="px-3 py-1 rounded-xl text-xs font-mono font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30 flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5" /> UNKNOWN
            </span>
          ) : (
            <span className="px-3 py-1 rounded-xl text-xs font-mono font-bold bg-white/10 text-gray-300 border border-border">
              {currentAction.status}
            </span>
          )}
        </div>
      </div>

      {/* Action Parameters & Policy Checks */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs font-mono">
        <div className="p-3 rounded-xl bg-surface-solid border border-border">
          <span className="text-gray-400 block text-[10px] uppercase font-semibold">Policy Authority</span>
          <span className="font-bold text-indigo-300 mt-1 flex items-center gap-1">
            <Shield className="w-3.5 h-3.5" /> {currentAction.policy_version}
          </span>
        </div>
        <div className="p-3 rounded-xl bg-surface-solid border border-border">
          <span className="text-gray-400 block text-[10px] uppercase font-semibold">Attempts</span>
          <span className="font-bold text-white mt-1 block">
            {currentAction.execution_attempts_count} / {currentAction.max_attempts} Max
          </span>
        </div>
        <div className="p-3 rounded-xl bg-surface-solid border border-border">
          <span className="text-gray-400 block text-[10px] uppercase font-semibold">Execution Engine</span>
          <span className="font-bold text-emerald-400 mt-1 block">
            {currentAction.execution_version}
          </span>
        </div>
      </div>

      {/* Policy Reasons */}
      {currentAction.policy_decision?.reasons && (
        <div className="p-3 rounded-xl bg-surface-solid/50 border border-border/80 text-xs">
          <span className="text-gray-400 font-semibold uppercase text-[10px] block mb-1">Policy Rationale:</span>
          <ul className="space-y-1 text-gray-300">
            {currentAction.policy_decision.reasons.map((r, i) => (
              <li key={i} className="flex items-start gap-1.5">
                <span className="text-indigo-400 shrink-0">•</span>
                <span>{r}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Live Result Feedback Banner */}
      {lastResult && (
        <ExecutionResultBanner
          result={lastResult}
          onReconcile={handleReconcile}
          isReconciling={isReconciling}
        />
      )}

      {/* Execution Controls Toolbar */}
      {!isTerminal && (
        <div className="pt-2 flex flex-col sm:flex-row items-center justify-between gap-3 border-t border-border">
          {/* Demo Scenario Simulation Selector */}
          <div className="flex items-center gap-2 w-full sm:w-auto">
            <span className="text-[11px] font-mono text-gray-400 shrink-0 flex items-center gap-1">
              <Terminal className="w-3 h-3" /> Simulation:
            </span>
            <select
              value={simulationOverride}
              onChange={(e) => setSimulationOverride(e.target.value)}
              className="bg-surface-solid border border-border rounded-xl px-2.5 py-1.5 text-xs text-gray-200 focus:outline-none focus:border-indigo-500 cursor-pointer w-full sm:w-auto font-mono"
            >
              <option value="">Default (Gateway Heuristics)</option>
              <option value="SUCCESS">Scenario A: Force Success (Captured)</option>
              <option value="TEMPORARY_FAILURE">Force Temporary Glitch (Retryable)</option>
              <option value="PERMANENT_FAILURE">Force Permanent Decline (Card Expired)</option>
              <option value="TIMEOUT">Scenario C: Force Provider Timeout (Unknown)</option>
            </select>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-2 w-full sm:w-auto justify-end">
            {currentAction.status === 'PROPOSED' && (
              <button
                onClick={handleAuthorize}
                disabled={isAuthorizing}
                className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-white/10 hover:bg-white/15 text-white font-bold text-xs transition-all cursor-pointer disabled:opacity-50"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isAuthorizing ? 'animate-spin' : ''}`} />
                <span>Authorize Policy</span>
              </button>
            )}

            <button
              onClick={handleExecute}
              disabled={isExecuting || (!isAllowed && currentAction.status !== 'PROPOSED')}
              className="flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-500 to-pink-500 hover:from-indigo-400 hover:to-pink-400 text-white font-heading font-extrabold text-xs shadow-lg shadow-indigo-500/20 active:scale-95 transition-all cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed w-full sm:w-auto"
            >
              {isExecuting ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  <span>Executing Adapter...</span>
                </>
              ) : (
                <>
                  <Play className="w-3.5 h-3.5 fill-current" />
                  <span>Execute Recovery Action</span>
                </>
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
