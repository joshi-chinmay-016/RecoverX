import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { getIntelligenceOverview } from '@/api/intelligence';
import { listOpportunities } from '@/api/opportunities';
import { MetricCard } from '@/components/ui/MetricCard';
import { MetricCardSkeleton } from '@/components/ui/LoadingSkeleton';
import { ErrorState } from '@/components/ui/ErrorState';
import { FailureDistributionChart } from '@/components/charts/FailureDistributionChart';
import { PriorityPieChart } from '@/components/charts/PriorityPieChart';
import { RevenueFunnelChart } from '@/components/charts/RevenueFunnelChart';
import { PriorityBadge } from '@/components/ui/PriorityBadge';
import { ScoreRing } from '@/components/ui/ScoreRing';
import { ProbabilityBar } from '@/components/ui/ProbabilityBar';
import { formatCurrency, formatEnum } from '@/lib/formatters';
import { Link, useNavigate } from 'react-router-dom';
import {
  AlertTriangle,
  Coins,
  TrendingDown,
  Flame,
  ArrowRight,
  Bot,
  BrainCircuit,
  Eye,
} from 'lucide-react';

export const OverviewPage: React.FC = () => {
  const navigate = useNavigate();

  const {
    data: overview,
    isLoading: isOverviewLoading,
    isError: isOverviewError,
    error: overviewError,
    refetch: refetchOverview,
  } = useQuery({
    queryKey: ['intelligence-overview'],
    queryFn: getIntelligenceOverview,
  });

  const {
    data: topOpps,
    isLoading: isOppsLoading,
  } = useQuery({
    queryKey: ['top-opportunities'],
    queryFn: () => listOpportunities({ page: 1, page_size: 5, priority: 'CRITICAL' }),
  });

  if (isOverviewError) {
    return (
      <ErrorState
        title="Revenue Intelligence Offline"
        message={overviewError instanceof Error ? overviewError.message : 'Unable to connect to RecoverX backend'}
        onRetry={refetchOverview}
      />
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="font-heading font-extrabold text-2xl sm:text-3xl text-white tracking-tight">
            Revenue Recovery Overview
          </h2>
          <p className="text-xs sm:text-sm text-gray-400 mt-1">
            Real-time financial truth, failure intelligence, and actionable recovery opportunities
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link
            to="/agent"
            className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-indigo-600 to-pink-600 hover:from-indigo-500 hover:to-pink-500 text-white font-semibold text-xs rounded-xl shadow-lg shadow-indigo-500/25 transition-all"
          >
            <Bot className="w-4 h-4" />
            <span>Launch Agent Studio</span>
          </Link>
        </div>
      </div>

      {/* KPI Metrics */}
      <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4" aria-label="Key Financial Metrics">
        {isOverviewLoading ? (
          <>
            <MetricCardSkeleton />
            <MetricCardSkeleton />
            <MetricCardSkeleton />
            <MetricCardSkeleton />
          </>
        ) : (
          <>
            <MetricCard
              title="Revenue at Risk"
              value={formatCurrency(overview?.revenue_at_risk || 0)}
              subtitle="Failed payment revenue needing recovery"
              variant="danger"
              icon={<AlertTriangle className="w-4 h-4" />}
            />
            <MetricCard
              title="Est. Recoverable"
              value={formatCurrency(overview?.estimated_recoverable_revenue || 0)}
              subtitle="Model: rules-v1 heuristic scoring"
              variant="success"
              icon={<Coins className="w-4 h-4" />}
            />
            <MetricCard
              title="Total Failed Revenue"
              value={formatCurrency(overview?.total_failed_revenue || overview?.revenue_at_risk || 0)}
              subtitle="Cumulative uncaptured gross volume"
              variant="warning"
              icon={<TrendingDown className="w-4 h-4" />}
            />
            <MetricCard
              title="High-Priority Queue"
              value={overview?.high_priority_opportunities || 0}
              subtitle="Critical & High recovery targets"
              variant="critical"
              icon={<Flame className="w-4 h-4" />}
            />
          </>
        )}
      </section>

      {/* Visual Intelligence Grid */}
      <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Failure Distribution */}
        <div className="bg-surface-card border border-border rounded-2xl p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-heading font-bold text-sm text-white flex items-center gap-2">
              <BrainCircuit className="w-4 h-4 text-indigo-400" />
              Failure Categories
            </h3>
            <span className="text-[10px] font-mono uppercase bg-indigo-500/20 text-indigo-300 px-2 py-0.5 rounded">
              Deterministic
            </span>
          </div>
          <FailureDistributionChart data={overview?.failure_distribution || {}} />
        </div>

        {/* Priority Allocation */}
        <div className="bg-surface-card border border-border rounded-2xl p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-heading font-bold text-sm text-white flex items-center gap-2">
              <Flame className="w-4 h-4 text-pink-400" />
              Priority Allocation
            </h3>
            <span className="text-[10px] font-mono uppercase bg-pink-500/20 text-pink-300 px-2 py-0.5 rounded">
              Bounded Scoring
            </span>
          </div>
          <PriorityPieChart data={overview?.priority_distribution || {}} />
        </div>

        {/* Revenue Spectrum Funnel */}
        <div className="bg-surface-card border border-border rounded-2xl p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-heading font-bold text-sm text-white flex items-center gap-2">
              <Coins className="w-4 h-4 text-emerald-400" />
              Revenue Recovery Spectrum
            </h3>
            <span className="text-[10px] font-mono uppercase bg-emerald-500/20 text-emerald-300 px-2 py-0.5 rounded">
              Live Telemetry
            </span>
          </div>
          <RevenueFunnelChart
            grossFailed={overview?.revenue_at_risk || 0}
            recoverable={overview?.estimated_recoverable_revenue || 0}
            recovered={overview?.recovered_revenue || 0}
          />
        </div>
      </section>

      {/* Critical Opportunities Queue Preview */}
      <section className="bg-surface-card border border-border rounded-2xl p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-heading font-bold text-base text-white">
              Critical Action Queue
            </h3>
            <p className="text-xs text-gray-400 mt-0.5">
              High-value recoverable targets recommended for AI agent investigation
            </p>
          </div>
          <Link
            to="/opportunities"
            className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 flex items-center gap-1 transition-colors"
          >
            View All ({overview?.total_opportunities || 0}) <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-border text-gray-400 uppercase text-[10px] tracking-wider font-semibold">
                <th className="pb-3">Payment ID</th>
                <th className="pb-3">Revenue at Risk</th>
                <th className="pb-3">Failure Category</th>
                <th className="pb-3">Recovery Likelihood</th>
                <th className="pb-3">Score</th>
                <th className="pb-3">Priority</th>
                <th className="pb-3">Recommendation</th>
                <th className="pb-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {isOppsLoading ? (
                <tr>
                  <td colSpan={8} className="py-6 text-center text-gray-500">
                    Loading critical opportunities queue...
                  </td>
                </tr>
              ) : !topOpps?.opportunities || topOpps.opportunities.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-6 text-center text-gray-500">
                    No critical opportunities found. View all opportunities in the queue.
                  </td>
                </tr>
              ) : (
                topOpps.opportunities.map((opp) => (
                  <tr key={opp.id} className="hover:bg-white/5 transition-colors group">
                    <td className="py-3.5 font-mono text-indigo-300">
                      {opp.payment_id.substring(0, 10)}...
                    </td>
                    <td className="py-3.5 font-bold text-white">
                      {formatCurrency(opp.revenue_at_risk)}
                    </td>
                    <td className="py-3.5 text-gray-300">
                      {formatEnum(opp.failure_category)}
                    </td>
                    <td className="py-3.5 min-w-[130px]">
                      <ProbabilityBar probability={opp.recovery_probability} />
                    </td>
                    <td className="py-3.5">
                      <ScoreRing score={opp.opportunity_score} size={36} strokeWidth={4} />
                    </td>
                    <td className="py-3.5">
                      <PriorityBadge priority={opp.priority} />
                    </td>
                    <td className="py-3.5 text-indigo-300 font-medium">
                      {formatEnum(opp.recommended_intervention)}
                    </td>
                    <td className="py-3.5 text-right space-x-2">
                      <button
                        onClick={() => navigate(`/opportunities/${opp.id}`)}
                        className="px-2.5 py-1 bg-white/5 hover:bg-white/10 text-gray-300 rounded-lg text-xs font-semibold inline-flex items-center gap-1 transition-colors cursor-pointer"
                      >
                        <Eye className="w-3 h-3" /> Inspect
                      </button>
                      <button
                        onClick={() => navigate(`/agent?opportunityId=${opp.id}`)}
                        className="px-2.5 py-1 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold inline-flex items-center gap-1 transition-colors cursor-pointer"
                      >
                        <Bot className="w-3 h-3" /> Agent
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
