import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Zap, ShieldCheck, Filter, RefreshCw, Layers, Clock, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { listActions } from '@/api/actions';
import { ActionExecutionCard } from '@/components/execution/ActionExecutionCard';
import { LoadingSkeleton } from '@/components/ui/LoadingSkeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { ErrorState } from '@/components/ui/ErrorState';

export const ActionsPage: React.FC = () => {
  const [selectedStatus, setSelectedStatus] = useState<string>('');
  const [selectedType, setSelectedType] = useState<string>('');

  const {
    data,
    isLoading,
    isError,
    error,
    refetch,
    isFetching,
  } = useQuery({
    queryKey: ['recovery-actions', selectedStatus, selectedType],
    queryFn: () => listActions({
      status: selectedStatus || undefined,
      action_type: selectedType || undefined,
      page: 1,
      page_size: 50,
    }),
  });

  const actions = data?.items || [];
  const total = data?.total || 0;

  const succeededCount = actions.filter((a) => a.status === 'SUCCEEDED').length;
  const authorizedCount = actions.filter((a) => a.status === 'AUTHORIZED' || a.status === 'PROPOSED').length;
  const unknownCount = actions.filter((a) => a.status === 'UNKNOWN').length;
  const blockedCount = actions.filter((a) => a.status === 'BLOCKED').length;

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] font-mono font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-pink-500/20 text-pink-300 border border-pink-500/30 flex items-center gap-1">
              <Zap className="w-3 h-3 text-pink-400" /> Controlled Execution
            </span>
            <span className="text-xs text-gray-400 font-mono">Adapter: MockPaymentAdapter</span>
          </div>
          <h2 className="font-heading font-extrabold text-2xl sm:text-3xl text-white tracking-tight">
            Recovery Action Execution Hub
          </h2>
          <p className="text-xs sm:text-sm text-gray-400 mt-1">
            Policy-authorized recovery action dispatch, execution retry control, and timeout reconciliation.
          </p>
        </div>

        <button
          onClick={() => refetch()}
          disabled={isFetching}
          className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-surface-card border border-border hover:bg-white/5 text-xs font-semibold text-gray-200 transition-all cursor-pointer disabled:opacity-50 w-fit"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isFetching ? 'animate-spin text-indigo-400' : ''}`} />
          <span>Refresh Actions</span>
        </button>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="p-4 rounded-2xl bg-surface-card border border-border">
          <div className="flex items-center justify-between text-xs text-gray-400 mb-1">
            <span>Total Actions</span>
            <Layers className="w-4 h-4 text-indigo-400" />
          </div>
          <span className="font-heading font-extrabold text-2xl text-white">{total}</span>
        </div>

        <div className="p-4 rounded-2xl bg-surface-card border border-emerald-500/20">
          <div className="flex items-center justify-between text-xs text-gray-400 mb-1">
            <span>Succeeded</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <span className="font-heading font-extrabold text-2xl text-emerald-300">{succeededCount}</span>
        </div>

        <div className="p-4 rounded-2xl bg-surface-card border border-amber-500/20">
          <div className="flex items-center justify-between text-xs text-gray-400 mb-1">
            <span>Timeouts / Unknown</span>
            <AlertTriangle className="w-4 h-4 text-amber-400" />
          </div>
          <span className="font-heading font-extrabold text-2xl text-amber-300">{unknownCount}</span>
        </div>

        <div className="p-4 rounded-2xl bg-surface-card border border-rose-500/20">
          <div className="flex items-center justify-between text-xs text-gray-400 mb-1">
            <span>Policy Blocked</span>
            <ShieldCheck className="w-4 h-4 text-rose-400" />
          </div>
          <span className="font-heading font-extrabold text-2xl text-rose-300">{blockedCount}</span>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="p-4 rounded-2xl bg-surface-card border border-border flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3">
          <span className="text-xs font-mono text-gray-400 flex items-center gap-1.5">
            <Filter className="w-3.5 h-3.5 text-indigo-400" /> Filter:
          </span>

          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="bg-surface-solid border border-border rounded-xl px-3 py-1.5 text-xs text-gray-200 focus:outline-none focus:border-indigo-500 cursor-pointer"
          >
            <option value="">All Statuses</option>
            <option value="PROPOSED">PROPOSED</option>
            <option value="AUTHORIZED">AUTHORIZED</option>
            <option value="EXECUTING">EXECUTING</option>
            <option value="SUCCEEDED">SUCCEEDED</option>
            <option value="FAILED">FAILED</option>
            <option value="RETRYABLE">RETRYABLE</option>
            <option value="UNKNOWN">UNKNOWN</option>
            <option value="BLOCKED">BLOCKED</option>
          </select>

          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="bg-surface-solid border border-border rounded-xl px-3 py-1.5 text-xs text-gray-200 focus:outline-none focus:border-indigo-500 cursor-pointer"
          >
            <option value="">All Action Types</option>
            <option value="RETRY_PAYMENT">RETRY_PAYMENT</option>
            <option value="WAIT_AND_RETRY">WAIT_AND_RETRY</option>
            <option value="REQUEST_ALTERNATE_PAYMENT_METHOD">REQUEST_ALTERNATE_PAYMENT_METHOD</option>
            <option value="SEND_PAYMENT_REMINDER">SEND_PAYMENT_REMINDER</option>
            <option value="MANUAL_REVIEW">MANUAL_REVIEW</option>
          </select>
        </div>

        <span className="text-xs font-mono text-gray-400">
          Showing {actions.length} of {total} Actions
        </span>
      </div>

      {/* Actions List */}
      {isLoading ? (
        <LoadingSkeleton count={3} />
      ) : isError ? (
        <ErrorState
          message={error instanceof Error ? error.message : 'Failed to load recovery actions'}
          onRetry={() => refetch()}
        />
      ) : actions.length === 0 ? (
        <EmptyState
          title="No Recovery Actions Found"
          description="Synthesize actions from an Opportunity or AI Agent Plan to begin controlled execution."
        />
      ) : (
        <div className="space-y-4">
          {actions.map((action) => (
            <ActionExecutionCard
              key={action.id}
              action={action}
              onUpdated={() => refetch()}
            />
          ))}
        </div>
      )}
    </div>
  );
};
