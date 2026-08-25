import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { getIntelligenceOverview } from '@/api/intelligence';
import { MetricCard } from '@/components/ui/MetricCard';
import { MetricCardSkeleton } from '@/components/ui/LoadingSkeleton';
import { ErrorState } from '@/components/ui/ErrorState';
import { FailureDistributionChart } from '@/components/charts/FailureDistributionChart';
import { formatCurrency, formatEnum } from '@/lib/formatters';
import { BrainCircuit, ShieldAlert, Cpu, CheckCircle, HelpCircle } from 'lucide-react';

export const IntelligencePage: React.FC = () => {
  const {
    data: overview,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ['intelligence-overview'],
    queryFn: getIntelligenceOverview,
  });

  if (isError) {
    return (
      <ErrorState
        title="Intelligence Service Offline"
        message={error instanceof Error ? error.message : 'Unable to load intelligence engine telemetry'}
        onRetry={refetch}
      />
    );
  }

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-1">
          <span className="text-[10px] font-mono font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
            Scoring Engine
          </span>
          <span className="text-xs text-gray-400 font-mono">Model: rules-v1</span>
        </div>
        <h2 className="font-heading font-extrabold text-2xl sm:text-3xl text-white tracking-tight">
          Deterministic Revenue Intelligence
        </h2>
        <p className="text-xs sm:text-sm text-gray-400 mt-1 max-w-2xl">
          Deterministic financial heuristics, merchant-relative transaction valuation, and explainable failure classification.
        </p>
      </div>

      {/* Intelligence vs Agent Callout */}
      <div className="p-5 rounded-2xl bg-surface-card border border-border flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 rounded-xl bg-indigo-500/20 text-indigo-400 flex items-center justify-center shrink-0">
            <Cpu className="w-5 h-5" />
          </div>
          <div>
            <h4 className="font-heading font-bold text-sm text-white">
              Zero LLMs in Financial Scoring
            </h4>
            <p className="text-xs text-gray-300 mt-0.5">
              Financial calculations, recoverability probabilities, and opportunity scores are strictly deterministic, testable, and database-backed.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0 text-xs font-mono text-emerald-400 bg-emerald-500/10 px-3 py-1.5 rounded-xl border border-emerald-500/20">
          <CheckCircle className="w-3.5 h-3.5" /> 100% Deterministic & Auditable
        </div>
      </div>

      {/* Overview Metric Row */}
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
              title="Revenue at Risk"
              value={formatCurrency(overview?.revenue_at_risk || 0)}
              subtitle="Evaluated across failed payments"
              variant="danger"
            />
            <MetricCard
              title="Est. Recoverable Revenue"
              value={formatCurrency(overview?.estimated_recoverable_revenue || 0)}
              subtitle="Likelihood-weighted recovery yield"
              variant="success"
            />
            <MetricCard
              title="Avg Recovery Likelihood"
              value={`${Math.round((overview?.average_recovery_probability || 0.6) * 100)}%`}
              subtitle="Based on failure category & history"
              variant="primary"
            />
          </>
        )}
      </div>

      {/* Engine Rules & Logic Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Failure Categories */}
        <div className="bg-surface-card border border-border rounded-2xl p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-heading font-bold text-base text-white flex items-center gap-2">
              <BrainCircuit className="w-4 h-4 text-indigo-400" />
              Normalized Failure Taxonomy
            </h3>
          </div>
          <p className="text-xs text-gray-400">
            Raw payment gateway error codes are mapped into standardized failure categories to isolate root causes.
          </p>
          <FailureDistributionChart data={overview?.failure_distribution || {}} />
        </div>

        {/* Top Root Cause Reasons */}
        <div className="bg-surface-card border border-border rounded-2xl p-6 space-y-4">
          <h3 className="font-heading font-bold text-base text-white flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-amber-400" />
            Top Root Cause Reasons
          </h3>
          <p className="text-xs text-gray-400">
            Most frequent payment failure codes recorded across incoming webhooks.
          </p>

          <div className="space-y-2 pt-2">
            {!overview?.top_failure_reasons || overview.top_failure_reasons.length === 0 ? (
              <div className="text-xs text-gray-500 py-6 text-center">
                No failure reasons recorded yet.
              </div>
            ) : (
              overview.top_failure_reasons.slice(0, 6).map((item, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between p-3 rounded-xl bg-white/5 border border-border text-xs"
                >
                  <span className="font-mono text-gray-300 truncate max-w-[80%]">
                    {item.reason}
                  </span>
                  <span className="font-mono font-bold text-indigo-300 px-2 py-0.5 rounded bg-indigo-500/20">
                    {item.count}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Deterministic Scoring Formula Documentation */}
      <div className="bg-surface-card border border-border rounded-2xl p-6 space-y-4">
        <h3 className="font-heading font-bold text-base text-white flex items-center gap-2">
          <HelpCircle className="w-4 h-4 text-pink-400" />
          Explainable Opportunity Scoring Architecture
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs text-gray-300">
          <div className="p-4 rounded-xl bg-surface-solid border border-border space-y-1">
            <div className="font-bold text-white font-heading">1. Relative Value (40%)</div>
            <p className="text-gray-400">
              Merchant-relative transaction value score normalized against historical distribution.
            </p>
          </div>
          <div className="p-4 rounded-xl bg-surface-solid border border-border space-y-1">
            <div className="font-bold text-white font-heading">2. Likelihood (40%)</div>
            <p className="text-gray-400">
              Heuristic baseline recovery likelihood computed from failure category and retry state.
            </p>
          </div>
          <div className="p-4 rounded-xl bg-surface-solid border border-border space-y-1">
            <div className="font-bold text-white font-heading">3. Percentile (10%)</div>
            <p className="text-gray-400">
              Transaction percentile rank within merchant volume ensures contextual priority.
            </p>
          </div>
          <div className="p-4 rounded-xl bg-surface-solid border border-border space-y-1">
            <div className="font-bold text-white font-heading">4. Dynamic Penalties</div>
            <p className="text-gray-400">
              Penalizes exhausted retries (-15%) and rewards fresh failures with time sensitivity.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
