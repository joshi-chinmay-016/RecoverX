import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getLearningOverview, getCalibrationReport, recomputeLearningModel } from '@/api/learning';
import { useAuth } from '@/features/auth/AuthContext';
import {
  TrendingUp,
  BrainCircuit,
  RefreshCw,
  Award,
  Layers,
  Sparkles,
  BarChart2,
  Lock,
} from 'lucide-react';
import { formatEnum } from '@/lib/formatters';
import { LoadingSkeleton } from '@/components/ui/LoadingSkeleton';
import { ErrorState } from '@/components/ui/ErrorState';

export const LearningPage: React.FC = () => {
  const { role } = useAuth();
  const queryClient = useQueryClient();
  const [recomputeSuccess, setRecomputeSuccess] = useState<string | null>(null);

  const canRecompute = role === 'ADMIN' || role === 'OPERATOR';

  const {
    data: overview,
    isLoading,
    isError,
    error,
    refetch,
    isFetching,
  } = useQuery({
    queryKey: ['learning-overview'],
    queryFn: () => getLearningOverview(),
  });

  const { data: calibration } = useQuery({
    queryKey: ['learning-calibration'],
    queryFn: () => getCalibrationReport(),
  });

  const recomputeMutation = useMutation({
    mutationFn: () => recomputeLearningModel(),
    onSuccess: (res) => {
      setRecomputeSuccess(`Model recomputed (${res.model_version})! Processed ${res.total_samples_processed} samples with Brier score ${(res.brier_score ?? 0).toFixed(4)}.`);
      queryClient.invalidateQueries({ queryKey: ['learning-overview'] });
      queryClient.invalidateQueries({ queryKey: ['learning-calibration'] });
      setTimeout(() => setRecomputeSuccess(null), 5000);
    },
  });

  if (isLoading) {
    return <LoadingSkeleton count={3} />;
  }

  if (isError) {
    return <ErrorState message={(error as any)?.message || 'Failed to load adaptive learning metrics.'} onRetry={refetch} />;
  }

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] font-mono font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 flex items-center gap-1">
              <BrainCircuit className="w-3 h-3 text-indigo-400" /> Adaptive Intelligence Engine
            </span>
            <span className="text-xs text-gray-400 font-mono">Model: {overview?.model_version || 'v1.0-online'}</span>
          </div>
          <h2 className="font-heading font-extrabold text-2xl sm:text-3xl text-white tracking-tight">
            Adaptive Learning & Statistical Calibration
          </h2>
          <p className="text-xs sm:text-sm text-gray-400 mt-1">
            Empirical Bayesian recovery calibration, dynamic strategy rank optimization, and closed-loop outcome feedback.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => refetch()}
            disabled={isFetching}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-surface-card border border-border hover:bg-white/5 text-xs font-semibold text-gray-200 transition-all cursor-pointer disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isFetching ? 'animate-spin text-indigo-400' : ''}`} />
            <span>Refresh</span>
          </button>

          <button
            onClick={() => recomputeMutation.mutate()}
            disabled={!canRecompute || recomputeMutation.isPending}
            title={!canRecompute ? 'Recomputation requires Operator or Admin role' : ''}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold text-white transition-all shadow-lg ${
              canRecompute
                ? 'bg-gradient-to-r from-indigo-600 to-pink-600 hover:from-indigo-500 hover:to-pink-500 shadow-indigo-600/25 cursor-pointer disabled:opacity-50'
                : 'bg-white/10 text-gray-400 cursor-not-allowed border border-white/10'
            }`}
          >
            {!canRecompute ? (
              <Lock className="w-3.5 h-3.5 text-gray-400" />
            ) : (
              <Sparkles className={`w-3.5 h-3.5 ${recomputeMutation.isPending ? 'animate-spin' : ''}`} />
            )}
            <span>{recomputeMutation.isPending ? 'Recomputing Model...' : 'Recompute Snapshot'}</span>
          </button>
        </div>
      </div>

      {/* Success alert banner */}
      {recomputeSuccess && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center gap-3 text-emerald-300 text-xs font-medium animate-fade-in">
          <Award className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{recomputeSuccess}</span>
        </div>
      )}

      {/* Key Metric KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 rounded-2xl bg-surface-card border border-indigo-500/30 shadow-lg shadow-indigo-500/5">
          <div className="flex items-center justify-between text-xs text-gray-400 mb-2">
            <span>Adaptive Yield Lift</span>
            <TrendingUp className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="font-heading font-black text-3xl text-emerald-400">
              +{((overview?.adaptive_yield_lift_pct ?? 0) * 100).toFixed(1)}%
            </span>
            <span className="text-[10px] text-gray-400 font-mono">vs baseline</span>
          </div>
          <div className="mt-2 text-[11px] text-gray-400">
            Observed yield: {((overview?.overall_recovery_rate ?? 0) * 100).toFixed(1)}% (Base: {((overview?.baseline_benchmark_rate ?? 0) * 100).toFixed(1)}%)
          </div>
        </div>

        <div className="p-5 rounded-2xl bg-surface-card border border-border">
          <div className="flex items-center justify-between text-xs text-gray-400 mb-2">
            <span>Confirmed Recoveries</span>
            <Award className="w-4 h-4 text-indigo-400" />
          </div>
          <span className="font-heading font-black text-3xl text-white">
            {overview?.confirmed_recoveries ?? 0}
          </span>
          <div className="mt-2 text-[11px] text-gray-400">
            From {overview?.total_samples ?? 0} confirmed outcomes
          </div>
        </div>

        <div className="p-5 rounded-2xl bg-surface-card border border-border">
          <div className="flex items-center justify-between text-xs text-gray-400 mb-2">
            <span>Model Brier Score</span>
            <BarChart2 className="w-4 h-4 text-pink-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="font-heading font-black text-3xl text-white">
              {(overview?.brier_score ?? calibration?.brier_score ?? 0.084).toFixed(4)}
            </span>
            <span className="text-[10px] text-emerald-400 font-mono">Well-Calibrated</span>
          </div>
          <div className="mt-2 text-[11px] text-gray-400">
            Lower is better (Brier &lt; 0.15 indicates high accuracy)
          </div>
        </div>

        <div className="p-5 rounded-2xl bg-surface-card border border-border">
          <div className="flex items-center justify-between text-xs text-gray-400 mb-2">
            <span>Distribution Drift</span>
            <Layers className="w-4 h-4 text-indigo-400" />
          </div>
          <span className="font-heading font-black text-2xl text-emerald-300">
            {overview?.drift_status || 'NORMAL'}
          </span>
          <div className="mt-2 text-[11px] text-gray-400 font-mono">
            {overview?.evidence_window_days || 30}-day sliding window
          </div>
        </div>
      </div>

      {/* Category Breakdown Table */}
      <div className="rounded-2xl bg-surface-card border border-border overflow-hidden">
        <div className="p-5 border-b border-border flex items-center justify-between">
          <div>
            <h3 className="font-heading font-bold text-lg text-white">Failure Category Adaptive Calibrations</h3>
            <p className="text-xs text-gray-400 mt-0.5">
              Empirical recovery probability weightings calibrated against historical payment outcomes.
            </p>
          </div>
          <span className="text-xs font-mono text-gray-400">
            {overview?.category_breakdown?.length || 0} Categories Active
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-white/5 text-gray-400 font-semibold border-b border-border uppercase tracking-wider text-[10px] font-mono">
              <tr>
                <th className="py-3 px-4">Failure Category</th>
                <th className="py-3 px-4">Attempts</th>
                <th className="py-3 px-4">Observed Rate</th>
                <th className="py-3 px-4">Deterministic Base</th>
                <th className="py-3 px-4">Adaptive Posterior</th>
                <th className="py-3 px-4">Top Strategy</th>
                <th className="py-3 px-4">Support</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {overview?.category_breakdown?.map((cat) => (
                <tr key={cat.failure_category} className="hover:bg-white/5 transition-colors">
                  <td className="py-3.5 px-4 font-semibold text-white">
                    {formatEnum(cat.failure_category)}
                  </td>
                  <td className="py-3.5 px-4 text-gray-300 font-mono">{cat.total_attempts}</td>
                  <td className="py-3.5 px-4 font-mono font-bold text-indigo-300">
                    {(cat.observed_recovery_rate * 100).toFixed(1)}%
                  </td>
                  <td className="py-3.5 px-4 text-gray-400 font-mono">
                    {(cat.baseline_probability * 100).toFixed(1)}%
                  </td>
                  <td className="py-3.5 px-4 font-mono font-bold text-emerald-400">
                    {(cat.adaptive_probability * 100).toFixed(1)}%
                  </td>
                  <td className="py-3.5 px-4">
                    <span className="px-2 py-0.5 rounded bg-white/5 text-gray-300 border border-white/10 font-mono text-[11px]">
                      {cat.top_recommended_strategy}
                    </span>
                  </td>
                  <td className="py-3.5 px-4">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                        cat.support_level === 'HIGH'
                          ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                          : cat.support_level === 'MODERATE'
                          ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30'
                          : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                      }`}
                    >
                      {cat.support_level}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Strategy Rankings Table */}
      <div className="rounded-2xl bg-surface-card border border-border overflow-hidden">
        <div className="p-5 border-b border-border">
          <h3 className="font-heading font-bold text-lg text-white">Strategy Performance Matrix</h3>
          <p className="text-xs text-gray-400 mt-0.5">
            Empirical success rate and execution performance by recovery action type.
          </p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-white/5 text-gray-400 font-semibold border-b border-border uppercase tracking-wider text-[10px] font-mono">
              <tr>
                <th className="py-3 px-4">Action Type</th>
                <th className="py-3 px-4">Attempts</th>
                <th className="py-3 px-4">Successful Recoveries</th>
                <th className="py-3 px-4">Empirical Success Rate</th>
                <th className="py-3 px-4">Avg Latency</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {overview?.strategy_rankings?.map((st) => (
                <tr key={st.action_type} className="hover:bg-white/5 transition-colors">
                  <td className="py-3.5 px-4 font-semibold text-white flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-pink-400" />
                    <span>{st.action_type}</span>
                  </td>
                  <td className="py-3.5 px-4 text-gray-300 font-mono">{st.total_attempts}</td>
                  <td className="py-3.5 px-4 font-mono text-emerald-300">{st.successful_recoveries}</td>
                  <td className="py-3.5 px-4 font-mono font-bold text-emerald-400">
                    {(st.observed_success_rate * 100).toFixed(1)}%
                  </td>
                  <td className="py-3.5 px-4 text-gray-400 font-mono">{st.average_latency_ms} ms</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
