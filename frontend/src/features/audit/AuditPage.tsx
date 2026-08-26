import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { listPayments } from '@/api/payments';
import { listAgentRuns } from '@/api/agent';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { TableSkeleton } from '@/components/ui/LoadingSkeleton';
import { ErrorState } from '@/components/ui/ErrorState';
import { formatCurrency, formatEnum, formatDate } from '@/lib/formatters';
import { Bot, CreditCard } from 'lucide-react';

export const AuditPage: React.FC = () => {
  const [tab, setTab] = useState<'payments' | 'agent_runs'>('payments');

  const {
    data: paymentsData,
    isLoading: isPaymentsLoading,
    isError: isPaymentsError,
    error: paymentsError,
    refetch: refetchPayments,
  } = useQuery({
    queryKey: ['audit-payments'],
    queryFn: () => listPayments(undefined, 1, 30),
  });

  const {
    data: runsData,
    isLoading: isRunsLoading,
    isError: isRunsError,
    error: runsError,
    refetch: refetchRuns,
  } = useQuery({
    queryKey: ['audit-agent-runs'],
    queryFn: () => listAgentRuns(1, 30),
  });

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-1">
          <span className="text-[10px] font-mono font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
            System & Agent Telemetry
          </span>
          <span className="text-xs text-gray-400 font-mono">Immutable Audit Trail</span>
        </div>
        <h2 className="font-heading font-extrabold text-2xl sm:text-3xl text-white tracking-tight">
          System Audit Trail & State Transitions
        </h2>
        <p className="text-xs sm:text-sm text-gray-400 mt-1">
          Transparent history of external webhook events, payment state changes, and AI agent diagnostic tool executions.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-3 border-b border-border pb-3">
        <button
          onClick={() => setTab('payments')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
            tab === 'payments'
              ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/40 shadow-sm'
              : 'text-gray-400 hover:text-gray-200 hover:bg-white/5'
          }`}
        >
          <CreditCard className="w-4 h-4" />
          <span>Payment Events ({paymentsData?.total || 0})</span>
        </button>

        <button
          onClick={() => setTab('agent_runs')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
            tab === 'agent_runs'
              ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/40 shadow-sm'
              : 'text-gray-400 hover:text-gray-200 hover:bg-white/5'
          }`}
        >
          <Bot className="w-4 h-4" />
          <span>Agent Run Invocations ({runsData?.total || 0})</span>
        </button>
      </div>

      {/* Content */}
      <div className="bg-surface-card border border-border rounded-2xl overflow-hidden">
        {tab === 'payments' ? (
          isPaymentsLoading ? (
            <TableSkeleton rows={8} />
          ) : isPaymentsError ? (
            <div className="p-6">
              <ErrorState
                title="Failed to Load Payment Audit"
                message={paymentsError instanceof Error ? paymentsError.message : 'Backend error'}
                onRetry={refetchPayments}
              />
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="bg-white/5 border-b border-border text-gray-400 uppercase text-[10px] tracking-wider font-semibold">
                    <th className="py-3.5 px-4">Payment ID</th>
                    <th className="py-3.5 px-4">Gateway ID</th>
                    <th className="py-3.5 px-4">Amount</th>
                    <th className="py-3.5 px-4">Status</th>
                    <th className="py-3.5 px-4">Payment Method</th>
                    <th className="py-3.5 px-4">Error / Reason</th>
                    <th className="py-3.5 px-4">Timestamp</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {paymentsData?.payments.map((p) => (
                    <tr key={p.id} className="hover:bg-white/5 transition-colors">
                      <td className="py-3.5 px-4 font-mono font-semibold text-indigo-300">
                        {p.id.substring(0, 10)}...
                      </td>
                      <td className="py-3.5 px-4 font-mono text-gray-400">
                        {p.razorpay_payment_id || '—'}
                      </td>
                      <td className="py-3.5 px-4 font-bold text-white">
                        {formatCurrency(p.amount_minor, p.currency)}
                      </td>
                      <td className="py-3.5 px-4">
                        <StatusBadge status={p.status} />
                      </td>
                      <td className="py-3.5 px-4 text-gray-300 font-mono">
                        {p.method || 'card'}
                      </td>
                      <td className="py-3.5 px-4 text-gray-400 font-mono text-[11px]">
                        {p.failure_description || p.failure_code || '—'}
                      </td>
                      <td className="py-3.5 px-4 text-gray-400">
                        {formatDate(p.created_at)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )
        ) : isRunsLoading ? (
          <TableSkeleton rows={8} />
        ) : isRunsError ? (
          <div className="p-6">
            <ErrorState
              title="Failed to Load Agent Audit"
              message={runsError instanceof Error ? runsError.message : 'Backend error'}
              onRetry={refetchRuns}
            />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="bg-white/5 border-b border-border text-gray-400 uppercase text-[10px] tracking-wider font-semibold">
                  <th className="py-3.5 px-4">Run ID</th>
                  <th className="py-3.5 px-4">Opportunity ID</th>
                  <th className="py-3.5 px-4">Selected Strategy</th>
                  <th className="py-3.5 px-4">Policy Result</th>
                  <th className="py-3.5 px-4">Run Status</th>
                  <th className="py-3.5 px-4">Agent Version</th>
                  <th className="py-3.5 px-4">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {runsData?.runs.map((r) => (
                  <tr key={r.run_id} className="hover:bg-white/5 transition-colors">
                    <td className="py-3.5 px-4 font-mono font-semibold text-indigo-300">
                      {r.run_id.substring(0, 10)}...
                    </td>
                    <td className="py-3.5 px-4 font-mono text-gray-400">
                      {r.opportunity_id.substring(0, 10)}...
                    </td>
                    <td className="py-3.5 px-4 font-bold text-white">
                      {formatEnum(r.selected_strategy || 'MANUAL_REVIEW')}
                    </td>
                    <td className="py-3.5 px-4">
                      <StatusBadge status={r.policy_status || 'ALLOWED'} />
                    </td>
                    <td className="py-3.5 px-4 font-mono text-emerald-400">
                      {r.status}
                    </td>
                    <td className="py-3.5 px-4 font-mono text-gray-400">
                      {r.agent_version}
                    </td>
                    <td className="py-3.5 px-4 text-gray-400">
                      {formatDate(r.created_at || r.started_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
