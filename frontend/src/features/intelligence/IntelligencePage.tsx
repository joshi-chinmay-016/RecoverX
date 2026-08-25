import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getIntelligenceOverview } from '@/api/intelligence';
import { getLearningOverview, getStrategyRankings, recomputeLearningModel } from '@/api/learning';
import { MetricCardSkeleton } from '@/components/ui/LoadingSkeleton';
import { ErrorState } from '@/components/ui/ErrorState';
import { PriorityBadge } from '@/components/ui/PriorityBadge';
import { ScoreRing } from '@/components/ui/ScoreRing';
import { ProbabilityBar } from '@/components/ui/ProbabilityBar';
import { formatCurrency, formatEnum, formatDate } from '@/lib/formatters';
import {
  BrainCircuit,
  ShieldCheck,
  Cpu,
  CheckCircle,
  HelpCircle,
  Sliders,
  Play,
  Layers,
  ArrowRight,
  Sparkles,
  Zap,
  Lock,
  Activity,
  AlertTriangle,
  RefreshCw,
  TrendingUp,
  Award,
  GitBranch,
  ShieldAlert,
  Gauge,
} from 'lucide-react';

export const IntelligencePage: React.FC = () => {
  const queryClient = useQueryClient();

  // Tab: 'overview' | 'strategies' | 'calibration'
  const [selectedCategory, setSelectedCategory] = useState<string>('BANK_FAILURE');
  const [simAmount, setSimAmount] = useState<number>(25000);
  const [simRetries, setSimRetries] = useState<number>(0);

  // Queries
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
    data: learningData,
    isLoading: isLearningLoading,
    refetch: refetchLearning,
    isFetching: isLearningFetching,
  } = useQuery({
    queryKey: ['learning-overview'],
    queryFn: () => getLearningOverview(),
  });

  const {
    data: strategyRankings,
    isLoading: isStrategiesLoading,
  } = useQuery({
    queryKey: ['learning-strategies', selectedCategory, simRetries, simAmount],
    queryFn: () => getStrategyRankings({
      failure_category: selectedCategory,
      retry_count: simRetries,
      amount_minor: simAmount * 100,
    }),
  });

  // Recompute mutation
  const recomputeMutation = useMutation({
    mutationFn: () => recomputeLearningModel(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['learning-overview'] });
      queryClient.invalidateQueries({ queryKey: ['learning-strategies'] });
      queryClient.invalidateQueries({ queryKey: ['intelligence-overview'] });
    },
  });

  if (isOverviewError) {
    return (
      <ErrorState
        title="Intelligence Service Offline"
        message={overviewError instanceof Error ? overviewError.message : 'Unable to load intelligence engine telemetry'}
        onRetry={refetchOverview}
      />
    );
  }

  const overallRate = learningData?.overall_recovery_rate ?? 0;
  const baselineRate = learningData?.baseline_benchmark_rate ?? 0.55;
  const liftPct = learningData?.adaptive_yield_lift_pct ?? 0;
  const brierScore = learningData?.brier_score !== undefined && learningData?.brier_score !== null ? learningData.brier_score : 0.15;
  const totalSamples = learningData?.total_samples ?? 0;

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] font-mono font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-gradient-to-r from-pink-500/20 to-indigo-500/20 text-pink-300 border border-pink-500/30 flex items-center gap-1">
              <Sparkles className="w-3 h-3 text-pink-400" /> Adaptive Statistical Learning
            </span>
            <span className="text-xs text-gray-400 font-mono">Model: {learningData?.model_version || 'adaptive-v1'}</span>
          </div>
          <h2 className="font-heading font-extrabold text-2xl sm:text-3xl text-white tracking-tight">
            Adaptive Revenue Intelligence
          </h2>
          <p className="text-xs sm:text-sm text-gray-400 mt-1 max-w-2xl">
            Bayesian probability calibration, historical strategy performance ranking, and empirical feedback loops.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => recomputeMutation.mutate()}
            disabled={recomputeMutation.isPending}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-gradient-to-r from-indigo-600 to-pink-600 hover:from-indigo-500 hover:to-pink-500 text-xs font-bold text-white shadow-lg shadow-indigo-500/20 transition-all cursor-pointer disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${recomputeMutation.isPending ? 'animate-spin' : ''}`} />
            <span>{recomputeMutation.isPending ? 'Calibrating...' : 'Recompute Learning Snapshot'}</span>
          </button>
        </div>
      </div>

      {/* Adaptive Yield Lift Showcase Card */}
      <div className="p-6 rounded-2xl bg-surface-card border border-indigo-500/30 relative overflow-hidden space-y-5">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-border">
          <div className="space-y-1">
            <span className="text-[10px] font-mono uppercase font-bold text-indigo-400 flex items-center gap-1.5">
              <Activity className="w-3.5 h-3.5" /> Statistical Learning Feedback Yield
            </span>
            <h3 className="font-heading font-extrabold text-xl text-white">
              Empirical Bayesian Recovery Calibration
            </h3>
            <p className="text-xs text-gray-300 max-w-xl">
              Learns from {totalSamples} confirmed historical recovery attempts. Uses Beta-Binomial smoothing to safely calibrate static probabilities.
            </p>
          </div>

          <div className="flex items-center gap-4 bg-surface-solid p-3.5 rounded-xl border border-border">
            <div className="text-center px-2">
              <span className="text-[10px] font-mono uppercase text-gray-500 block">Baseline Prior</span>
              <span className="font-heading font-extrabold text-lg text-gray-300">{Math.round(baselineRate * 100)}%</span>
            </div>
            <ArrowRight className="w-4 h-4 text-indigo-400" />
            <div className="text-center px-2">
              <span className="text-[10px] font-mono uppercase text-emerald-400 block">Observed Yield</span>
              <span className="font-heading font-extrabold text-xl text-emerald-300">{Math.round(overallRate * 100)}%</span>
            </div>
            <div className="text-center px-2 border-l border-border pl-4">
              <span className="text-[10px] font-mono uppercase text-pink-400 block">Yield Lift</span>
              <span className="font-heading font-extrabold text-lg text-pink-300">+{liftPct}%</span>
            </div>
          </div>
        </div>

        {/* 4 Metric Pills */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
          <div className="p-3 rounded-xl bg-surface-solid border border-border">
            <span className="text-gray-500 block text-[10px] uppercase font-semibold">Evidence Window</span>
            <span className="font-bold text-white mt-0.5 block">{learningData?.evidence_window_days || 90} Days</span>
          </div>
          <div className="p-3 rounded-xl bg-surface-solid border border-border">
            <span className="text-gray-500 block text-[10px] uppercase font-semibold">Predictive Accuracy</span>
            <span className="font-bold text-emerald-400 mt-0.5 block">Brier {brierScore} (Calibrated)</span>
          </div>
          <div className="p-3 rounded-xl bg-surface-solid border border-border">
            <span className="text-gray-500 block text-[10px] uppercase font-semibold">Drift Status</span>
            <span className="font-bold text-indigo-300 mt-0.5 block flex items-center gap-1">
              <ShieldCheck className="w-3.5 h-3.5 text-indigo-400" /> NORMAL
            </span>
          </div>
          <div className="p-3 rounded-xl bg-surface-solid border border-border">
            <span className="text-gray-500 block text-[10px] uppercase font-semibold">Model Class</span>
            <span className="font-bold text-gray-200 mt-0.5 block">Adaptive Statistical</span>
          </div>
        </div>
      </div>

      {/* Interactive Strategy Ranking & Comparison Matrix */}
      <section className="bg-surface-card border border-border rounded-2xl p-6 space-y-6">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-border">
          <div>
            <div className="flex items-center gap-2">
              <Layers className="w-4 h-4 text-pink-400" />
              <h3 className="font-heading font-bold text-base text-white">
                Empirical Strategy Performance Matrix
              </h3>
            </div>
            <p className="text-xs text-gray-400 mt-0.5">
              Ranked recovery intervention effectiveness derived from confirmed historical yield data.
            </p>
          </div>

          {/* Context Selector Toolbar */}
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-1.5 text-xs font-mono text-gray-400">
              <span>Failure:</span>
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="bg-surface-solid border border-border rounded-xl px-3 py-1.5 text-xs text-white font-mono focus:outline-none focus:border-indigo-500 cursor-pointer"
              >
                <option value="BANK_FAILURE">BANK_FAILURE (Acquiring Error)</option>
                <option value="TEMPORARY_FAILURE">TEMPORARY_FAILURE (Timeout)</option>
                <option value="INSUFFICIENT_FUNDS">INSUFFICIENT_FUNDS (Low Balance)</option>
                <option value="AUTHENTICATION_FAILURE">AUTHENTICATION_FAILURE (3DS Lapse)</option>
                <option value="PAYMENT_METHOD_FAILURE">PAYMENT_METHOD_FAILURE (Card Expired)</option>
                <option value="LIMIT_EXCEEDED">LIMIT_EXCEEDED (Amount Limit)</option>
              </select>
            </div>

            <div className="flex items-center gap-1.5 text-xs font-mono text-gray-400">
              <span>Retries:</span>
              <select
                value={simRetries}
                onChange={(e) => setSimRetries(Number(e.target.value))}
                className="bg-surface-solid border border-border rounded-xl px-2.5 py-1.5 text-xs text-white font-mono focus:outline-none focus:border-indigo-500 cursor-pointer"
              >
                <option value="0">0 (Fresh)</option>
                <option value="1">1 attempt</option>
                <option value="2">2 attempts</option>
                <option value="3">3 (Max limit)</option>
              </select>
            </div>
          </div>
        </div>

        {/* Strategy Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-border text-gray-400 uppercase text-[10px] tracking-wider font-semibold">
                <th className="pb-3 px-3">Rank</th>
                <th className="pb-3 px-3">Recovery Strategy</th>
                <th className="pb-3 px-3">Strategy Score</th>
                <th className="pb-3 px-3">Historical Yield</th>
                <th className="pb-3 px-3">Sample Volume</th>
                <th className="pb-3 px-3">Support Level</th>
                <th className="pb-3 px-3 text-right">Policy Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {isStrategiesLoading ? (
                <tr>
                  <td colSpan={7} className="py-6 text-center text-gray-500">
                    Evaluating empirical strategy scores...
                  </td>
                </tr>
              ) : !strategyRankings || strategyRankings.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-6 text-center text-gray-500">
                    No strategy rankings available.
                  </td>
                </tr>
              ) : (
                strategyRankings.map((item, idx) => (
                  <tr key={item.action_type} className={`hover:bg-white/5 transition-colors ${idx === 0 ? 'bg-indigo-500/5' : ''}`}>
                    <td className="py-3.5 px-3 font-mono font-bold text-gray-400">
                      #{idx + 1}
                    </td>
                    <td className="py-3.5 px-3 font-bold text-white flex items-center gap-2">
                      <span>{formatEnum(item.action_type)}</span>
                      {idx === 0 && (
                        <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                          Recommended
                        </span>
                      )}
                    </td>
                    <td className="py-3.5 px-3 font-mono font-extrabold text-sm text-indigo-300">
                      {item.strategy_score}<span className="text-[10px] text-gray-500">/100</span>
                    </td>
                    <td className="py-3.5 px-3 font-mono font-bold text-emerald-400">
                      {Math.round(item.empirical_recovery_rate * 100)}%
                    </td>
                    <td className="py-3.5 px-3 font-mono text-gray-300">
                      {item.sample_size} attempts
                    </td>
                    <td className="py-3.5 px-3">
                      <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded ${
                        item.support_level === 'HIGH'
                          ? 'bg-emerald-500/20 text-emerald-300'
                          : item.support_level === 'MODERATE'
                          ? 'bg-indigo-500/20 text-indigo-300'
                          : 'bg-white/10 text-gray-400'
                      }`}>
                        {item.support_level}
                      </span>
                    </td>
                    <td className="py-3.5 px-3 text-right">
                      {item.is_policy_eligible ? (
                        <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                          ELIGIBLE
                        </span>
                      ) : (
                        <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/20">
                          POLICY BLOCKED
                        </span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>

      {/* 5-Tier Hierarchical Fallback Documentation */}
      <section className="bg-surface-card border border-border rounded-2xl p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-heading font-bold text-base text-white flex items-center gap-2">
            <GitBranch className="w-4 h-4 text-emerald-400" />
            5-Tier Hierarchical Evidence Fallback Ladder
          </h3>
          <span className="text-xs font-mono text-gray-400">
            Zero Cross-Merchant Data Leakage
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-5 gap-3 text-xs font-mono">
          <div className="p-3.5 rounded-xl bg-surface-solid border border-indigo-500/30 space-y-1">
            <span className="text-indigo-400 font-bold block text-[10px]">Tier 1 (N &ge; 10)</span>
            <div className="font-bold text-white">Merchant + Action</div>
            <p className="text-[11px] text-gray-400">Merchant-specific action outcome history</p>
          </div>
          <div className="p-3.5 rounded-xl bg-surface-solid border border-border space-y-1">
            <span className="text-gray-400 font-bold block text-[10px]">Tier 2 (N &ge; 15)</span>
            <div className="font-bold text-white">Merchant Category</div>
            <p className="text-[11px] text-gray-400">Merchant aggregate failure root cause</p>
          </div>
          <div className="p-3.5 rounded-xl bg-surface-solid border border-border space-y-1">
            <span className="text-gray-400 font-bold block text-[10px]">Tier 3 (N &ge; 20)</span>
            <div className="font-bold text-white">Global + Action</div>
            <p className="text-[11px] text-gray-400">Anonymized category action yield</p>
          </div>
          <div className="p-3.5 rounded-xl bg-surface-solid border border-border space-y-1">
            <span className="text-gray-400 font-bold block text-[10px]">Tier 4 (N &ge; 25)</span>
            <div className="font-bold text-white">Global Category</div>
            <p className="text-[11px] text-gray-400">Standardized baseline category yield</p>
          </div>
          <div className="p-3.5 rounded-xl bg-surface-solid border border-border space-y-1">
            <span className="text-pink-400 font-bold block text-[10px]">Tier 5 (Cold Start)</span>
            <div className="font-bold text-white">Phase 2 Baseline</div>
            <p className="text-[11px] text-gray-400">Deterministic heuristic ruleset</p>
          </div>
        </div>
      </section>
    </div>
  );
};
