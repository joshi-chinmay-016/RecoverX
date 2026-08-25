import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { getPolicySummary } from '@/api/agent';
import { MetricCard } from '@/components/ui/MetricCard';
import { MetricCardSkeleton } from '@/components/ui/LoadingSkeleton';
import { ErrorState } from '@/components/ui/ErrorState';
import { formatEnum } from '@/lib/formatters';
import { ShieldCheck, Lock, UserCheck, AlertTriangle, CheckCircle, Shield } from 'lucide-react';

export const PoliciesPage: React.FC = () => {
  const {
    data: policy,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ['policy-summary'],
    queryFn: getPolicySummary,
  });

  const allowedActions = [
    {
      action: 'WAIT_AND_RETRY',
      purpose: 'Wait for transient bank/network recovery and trigger retry',
      risk: 'LOW',
      approval: 'Automated',
    },
    {
      action: 'REQUEST_ALTERNATE_PAYMENT_METHOD',
      purpose: 'Prompt customer to update card or UPI VPA upon balance failure',
      risk: 'LOW',
      approval: 'Automated',
    },
    {
      action: 'SEND_PAYMENT_REMINDER',
      purpose: 'Dispatch multi-channel reminder for abandoned or timed-out orders',
      risk: 'LOW',
      approval: 'Automated',
    },
    {
      action: 'REQUEST_REAUTHENTICATION',
      purpose: 'Re-trigger 3DS OTP authentication upon security token lapse',
      risk: 'MEDIUM',
      approval: 'Automated',
    },
    {
      action: 'RETRY_PAYMENT',
      purpose: 'Direct gateway retry within allowed retry counter limits',
      risk: 'MEDIUM',
      approval: 'Automated',
    },
    {
      action: 'MANUAL_REVIEW',
      purpose: 'Escalate to merchant human-in-the-loop review operations',
      risk: 'HIGH',
      approval: 'Human Gate',
    },
    {
      action: 'ESCALATE',
      purpose: 'Route to executive finance escalation for high-tier merchants',
      risk: 'HIGH',
      approval: 'Human Gate',
    },
    {
      action: 'CLOSE_RECOVERY_CASE',
      purpose: 'Close recovery case when unrecoverable or already resolved',
      risk: 'LOW',
      approval: 'Automated',
    },
  ];

  if (isError) {
    return (
      <ErrorState
        title="Policy Engine Offline"
        message={error instanceof Error ? error.message : 'Unable to load policy configuration'}
        onRetry={refetch}
      />
    );
  }

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-1">
          <span className="text-[10px] font-mono font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 flex items-center gap-1">
            <ShieldCheck className="w-3 h-3" /> Safety Boundary
          </span>
          <span className="text-xs text-gray-400 font-mono">
            Version: {policy?.policy_version || 'policy-v1'}
          </span>
        </div>
        <h2 className="font-heading font-extrabold text-2xl sm:text-3xl text-white tracking-tight">
          Deterministic PolicyEngine & Guardrails
        </h2>
        <p className="text-xs sm:text-sm text-gray-400 mt-1 max-w-2xl">
          The PolicyEngine holds non-negotiable authority over the AI Recovery Agent. The LLM proposes plans; the PolicyEngine enforces limits and permissions.
        </p>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {isLoading ? (
          <>
            <MetricCardSkeleton />
            <MetricCardSkeleton />
            <MetricCardSkeleton />
          </>
        ) : (
          <>
            <MetricCard
              title="Max Retry Limit"
              value={`${policy?.max_retry_attempts || 3} Attempts`}
              subtitle="Hard cap on automated payment retries"
              variant="primary"
              icon={<Shield className="w-4 h-4" />}
            />
            <MetricCard
              title="Confidence Floor"
              value={`${Math.round((policy?.confidence_threshold || 0.5) * 100)}%`}
              subtitle="Minimum confidence for automated allowance"
              variant="success"
              icon={<CheckCircle className="w-4 h-4" />}
            />
            <MetricCard
              title="Human Approval Actions"
              value={policy?.approval_required_for?.length || 2}
              subtitle="Strategies requiring operator consent"
              variant="warning"
              icon={<UserCheck className="w-4 h-4" />}
            />
          </>
        )}
      </div>

      {/* Allowed Actions Registry Table */}
      <div className="bg-surface-card border border-border rounded-2xl p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-heading font-bold text-base text-white">
              Action Whitelist & Governance Matrix
            </h3>
            <p className="text-xs text-gray-400 mt-0.5">
              The AI Agent is strictly prohibited from inventing arbitrary actions. Only registered actions are accepted.
            </p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-border text-gray-400 uppercase text-[10px] tracking-wider font-semibold">
                <th className="pb-3 px-3">Action Type</th>
                <th className="pb-3 px-3">Purpose & Specification</th>
                <th className="pb-3 px-3">Risk Level</th>
                <th className="pb-3 px-3">Execution Gate</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {allowedActions.map((action, idx) => (
                <tr key={idx} className="hover:bg-white/5 transition-colors">
                  <td className="py-3.5 px-3 font-mono font-bold text-indigo-300">
                    {action.action}
                  </td>
                  <td className="py-3.5 px-3 text-gray-300">
                    {action.purpose}
                  </td>
                  <td className="py-3.5 px-3">
                    <span
                      className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded ${
                        action.risk === 'HIGH'
                          ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                          : action.risk === 'MEDIUM'
                          ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                          : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                      }`}
                    >
                      {action.risk}
                    </span>
                  </td>
                  <td className="py-3.5 px-3">
                    <span
                      className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                        action.approval === 'Human Gate'
                          ? 'bg-amber-500/15 text-amber-300 border border-amber-500/30'
                          : 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30'
                      }`}
                    >
                      {action.approval}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Safety Boundary Callout */}
      <div className="p-6 rounded-2xl bg-surface-solid border border-border flex items-start gap-4">
        <div className="w-10 h-10 rounded-xl bg-amber-500/20 text-amber-400 flex items-center justify-center shrink-0">
          <Lock className="w-5 h-5" />
        </div>
        <div>
          <h4 className="font-heading font-bold text-sm text-white">
            Action Planning & Execution Governance
          </h4>
          <p className="text-xs text-gray-300 mt-1 leading-relaxed">
            The platform plans actions and creates transparent, auditable recovery proposals. The PolicyEngine guarantees that no financial mutations, retries, or customer messages are triggered without verified safety authorization.
          </p>
        </div>
      </div>
    </div>
  );
};
