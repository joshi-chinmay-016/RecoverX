import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { listOpportunities } from '@/api/opportunities';
import { PriorityLevel, FailureCategory } from '@/types/intelligence';
import { PriorityBadge } from '@/components/ui/PriorityBadge';
import { ScoreRing } from '@/components/ui/ScoreRing';
import { ProbabilityBar } from '@/components/ui/ProbabilityBar';
import { TableSkeleton } from '@/components/ui/LoadingSkeleton';
import { ErrorState } from '@/components/ui/ErrorState';
import { EmptyState } from '@/components/ui/EmptyState';
import { formatCurrency, formatEnum } from '@/lib/formatters';
import { useNavigate } from 'react-router-dom';
import {
  TrendingUp,
  Filter,
  Eye,
  Bot,
  ChevronLeft,
  ChevronRight,
  Search,
} from 'lucide-react';

export const OpportunitiesPage: React.FC = () => {
  const navigate = useNavigate();
  const [priority, setPriority] = useState<PriorityLevel | ''>('');
  const [category, setCategory] = useState<FailureCategory | ''>('');
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [page, setPage] = useState<number>(1);
  const pageSize = 15;

  const {
    data,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ['opportunities', priority, category, page, pageSize],
    queryFn: () =>
      listOpportunities({
        priority: priority || undefined,
        failure_category: category || undefined,
        page,
        page_size: pageSize,
      }),
  });

  const opportunities = data?.opportunities || [];
  const total = data?.total || 0;
  const totalPages = Math.ceil(total / pageSize) || 1;

  // Local search filter for payment ID
  const filteredOpportunities = opportunities.filter((opp) => {
    if (!searchTerm) return true;
    return (
      opp.payment_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (opp.failure_reason && opp.failure_reason.toLowerCase().includes(searchTerm.toLowerCase()))
    );
  });

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="font-heading font-extrabold text-2xl sm:text-3xl text-white tracking-tight">
            Recovery Opportunities Queue
          </h2>
          <p className="text-xs sm:text-sm text-gray-400 mt-1">
            Prioritized revenue opportunities evaluated by Revenue Intelligence ready for AI reasoning.
          </p>
        </div>

        <div className="text-xs font-mono text-gray-400 bg-surface-card px-3 py-1.5 rounded-xl border border-border">
          Total Opportunities: <strong className="text-white">{total}</strong>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="p-4 rounded-2xl bg-surface-card border border-border flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
          <div className="relative flex-1 sm:w-64">
            <Search className="w-4 h-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search Payment ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-surface-solid border border-border rounded-xl pl-9 pr-3 py-2 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 transition-colors"
            />
          </div>

          <div className="flex items-center gap-2">
            <Filter className="w-3.5 h-3.5 text-gray-400" />
            <select
              value={priority}
              onChange={(e) => {
                setPriority(e.target.value as PriorityLevel | '');
                setPage(1);
              }}
              className="bg-surface-solid border border-border rounded-xl px-3 py-2 text-xs text-gray-200 focus:outline-none focus:border-indigo-500 cursor-pointer"
            >
              <option value="">All Priorities</option>
              <option value="CRITICAL">Critical</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
            </select>

            <select
              value={category}
              onChange={(e) => {
                setCategory(e.target.value as FailureCategory | '');
                setPage(1);
              }}
              className="bg-surface-solid border border-border rounded-xl px-3 py-2 text-xs text-gray-200 focus:outline-none focus:border-indigo-500 cursor-pointer"
            >
              <option value="">All Categories</option>
              <option value="TEMPORARY_FAILURE">Temporary Failure</option>
              <option value="INSUFFICIENT_FUNDS">Insufficient Funds</option>
              <option value="NETWORK_FAILURE">Network Failure</option>
              <option value="AUTHENTICATION_FAILURE">Authentication Failure</option>
              <option value="BANK_FAILURE">Bank Failure</option>
            </select>
          </div>
        </div>

        {(priority || category || searchTerm) && (
          <button
            onClick={() => {
              setPriority('');
              setCategory('');
              setSearchTerm('');
              setPage(1);
            }}
            className="text-xs text-indigo-400 hover:text-indigo-300 font-semibold transition-colors cursor-pointer"
          >
            Clear Filters
          </button>
        )}
      </div>

      {/* Primary Opportunities Data Table */}
      <div className="bg-surface-card border border-border rounded-2xl overflow-hidden">
        {isLoading ? (
          <TableSkeleton rows={8} />
        ) : isError ? (
          <div className="p-6">
            <ErrorState
              title="Failed to Load Opportunities"
              message={error instanceof Error ? error.message : 'Backend connection error'}
              onRetry={refetch}
            />
          </div>
        ) : filteredOpportunities.length === 0 ? (
          <EmptyState
            icon={<TrendingUp className="w-8 h-8 text-indigo-400" />}
            title="No Opportunities Found"
            description="No recovery opportunities match your current filter criteria."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="bg-white/5 border-b border-border text-gray-400 uppercase text-[10px] tracking-wider font-semibold">
                  <th className="py-3.5 px-4">Payment ID</th>
                  <th className="py-3.5 px-4">Revenue at Risk</th>
                  <th className="py-3.5 px-4">Failure Category</th>
                  <th className="py-3.5 px-4">Likelihood</th>
                  <th className="py-3.5 px-4">Opportunity Score</th>
                  <th className="py-3.5 px-4">Priority</th>
                  <th className="py-3.5 px-4">Recommended Strategy</th>
                  <th className="py-3.5 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {filteredOpportunities.map((opp) => (
                  <tr
                    key={opp.id}
                    className="hover:bg-white/5 transition-colors cursor-pointer"
                    onClick={() => navigate(`/opportunities/${opp.id}`)}
                  >
                    <td className="py-4 px-4 font-mono font-semibold text-indigo-300">
                      {opp.payment_id.substring(0, 12)}...
                    </td>
                    <td className="py-4 px-4 font-bold text-white text-sm">
                      {formatCurrency(opp.revenue_at_risk)}
                    </td>
                    <td className="py-4 px-4 text-gray-300">
                      {formatEnum(opp.failure_category)}
                    </td>
                    <td className="py-4 px-4 min-w-[140px]">
                      <ProbabilityBar probability={opp.recovery_probability} />
                    </td>
                    <td className="py-4 px-4">
                      <ScoreRing score={opp.opportunity_score} size={40} strokeWidth={4} />
                    </td>
                    <td className="py-4 px-4">
                      <PriorityBadge priority={opp.priority} />
                    </td>
                    <td className="py-4 px-4 font-semibold text-indigo-300">
                      {formatEnum(opp.recommended_intervention)}
                    </td>
                    <td className="py-4 px-4 text-right space-x-2" onClick={(e) => e.stopPropagation()}>
                      <button
                        onClick={() => navigate(`/opportunities/${opp.id}`)}
                        className="px-2.5 py-1.5 bg-white/5 hover:bg-white/10 text-gray-300 rounded-lg font-semibold inline-flex items-center gap-1 transition-colors cursor-pointer"
                      >
                        <Eye className="w-3.5 h-3.5" /> Inspect
                      </button>
                      <button
                        onClick={() => navigate(`/agent?opportunityId=${opp.id}`)}
                        className="px-3 py-1.5 bg-gradient-to-r from-indigo-600 to-pink-600 hover:from-indigo-500 hover:to-pink-500 text-white rounded-lg font-semibold inline-flex items-center gap-1.5 shadow-sm shadow-indigo-500/20 transition-all cursor-pointer"
                      >
                        <Bot className="w-3.5 h-3.5" /> Run Agent
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Footer */}
        {totalPages > 1 && (
          <div className="p-4 border-t border-border flex items-center justify-between text-xs text-gray-400">
            <div>
              Showing page <strong className="text-white">{page}</strong> of{' '}
              <strong className="text-white">{totalPages}</strong> ({total} total)
            </div>
            <div className="flex items-center gap-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="px-3 py-1.5 bg-surface-solid border border-border rounded-lg disabled:opacity-40 hover:bg-white/5 text-white flex items-center gap-1 cursor-pointer transition-colors"
              >
                <ChevronLeft className="w-3.5 h-3.5" /> Prev
              </button>
              <button
                disabled={page >= totalPages}
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                className="px-3 py-1.5 bg-surface-solid border border-border rounded-lg disabled:opacity-40 hover:bg-white/5 text-white flex items-center gap-1 cursor-pointer transition-colors"
              >
                Next <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
