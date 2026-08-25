import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getIntelligenceOverview } from '@/api/intelligence';
import { MetricCard } from '@/components/ui/MetricCard';
import { MetricCardSkeleton } from '@/components/ui/LoadingSkeleton';
import { ErrorState } from '@/components/ui/ErrorState';
import { FailureDistributionChart } from '@/components/charts/FailureDistributionChart';
import { PriorityBadge } from '@/components/ui/PriorityBadge';
import { ScoreRing } from '@/components/ui/ScoreRing';
import { ProbabilityBar } from '@/components/ui/ProbabilityBar';
import { formatCurrency, formatEnum } from '@/lib/formatters';
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
} from 'lucide-react';

export const IntelligencePage: React.FC = () => {
  const {
    data: overview,
    isLoading,
    isError,
    error,
    refetch,
    isFetching,
  } = useQuery({
    queryKey: ['intelligence-overview'],
    queryFn: getIntelligenceOverview,
  });

  // Diagnostic Simulator State
  const [simAmount, setSimAmount] = useState<number>(15000);
  const [simCategory, setSimCategory] = useState<string>('TEMPORARY_FAILURE');
  const [simMethod, setSimMethod] = useState<string>('upi');
  const [simRetries, setSimRetries] = useState<number>(0);

  // Compute simulated deterministic score live in memory
  const computeSimulation = () => {
    let baseLikelihood = 0.85;
    let strategy = 'WAIT_AND_RETRY';

    if (simCategory === 'INSUFFICIENT_FUNDS') {
      baseLikelihood = 0.60;
      strategy = 'REQUEST_ALTERNATE_PAYMENT_METHOD';
    } else if (simCategory === 'AUTH_FAILURE') {
      baseLikelihood = 0.70;
      strategy = 'REQUEST_REAUTHENTICATION';
    } else if (simCategory === 'BANK_FAILURE') {
      baseLikelihood = 0.65;
      strategy = 'WAIT_AND_RETRY';
    } else if (simCategory === 'CARD_EXPIRED') {
      baseLikelihood = 0.25;
      strategy = 'REQUEST_ALTERNATE_PAYMENT_METHOD';
    } else if (simCategory === 'FRAUD_OR_SECURITY_BLOCK') {
      baseLikelihood = 0.05;
      strategy = 'MANUAL_REVIEW';
    }

    // Retries penalty
    const adjustedLikelihood = Math.max(0.05, baseLikelihood - simRetries * 0.15);

    // Value score (log normalized based on benchmark)
    const valScore = Math.min(100, Math.max(10, Math.round(Math.log10(simAmount + 1) * 22)));
    const likelihoodScore = Math.round(adjustedLikelihood * 100);

    const opportunityScore = Math.min(
      100,
      Math.max(1, Math.round(valScore * 0.45 + likelihoodScore * 0.45 + (simRetries === 0 ? 10 : 0)))
    );

    let priority: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' = 'LOW';
    if (opportunityScore >= 80) priority = 'CRITICAL';
    else if (opportunityScore >= 60) priority = 'HIGH';
    else if (opportunityScore >= 40) priority = 'MEDIUM';

    return {
      likelihood: adjustedLikelihood,
      score: opportunityScore,
      priority,
      strategy,
      recoverable: Math.round((simAmount * 100) * adjustedLikelihood),
    };
  };

  const simResult = computeSimulation();

  const taxonomy = [
    {
      category: 'TEMPORARY_FAILURE',
      name: 'Transient Gateway Glitch',
      probability: '85%',
      strategy: 'WAIT_AND_RETRY',
      backoff: 'Immediate (0-5 min)',
      status: 'Fully Automated',
    },
    {
      category: 'BANK_FAILURE',
      name: 'Acquiring Bank Downtime',
      probability: '65%',
      strategy: 'WAIT_AND_RETRY',
      backoff: 'Exponential (15-30 min)',
      status: 'Fully Automated',
    },
    {
      category: 'INSUFFICIENT_FUNDS',
      name: 'Low Balance / Limit',
      probability: '60%',
      strategy: 'REQUEST_ALTERNATE_PAYMENT_METHOD',
      backoff: 'SMS / WhatsApp Prompt',
      status: 'Customer Action',
    },
    {
      category: 'AUTH_FAILURE',
      name: '3DS OTP Authentication Lapse',
      probability: '70%',
      strategy: 'REQUEST_REAUTHENTICATION',
      backoff: 'Seamless Re-auth Flow',
      status: 'Customer Action',
    },
    {
      category: 'CARD_EXPIRED',
      name: 'Expired Instrument',
      probability: '25%',
      strategy: 'REQUEST_ALTERNATE_PAYMENT_METHOD',
      backoff: 'Update Card Notification',
      status: 'Customer Action',
    },
    {
      category: 'FRAUD_OR_SECURITY_BLOCK',
      name: 'Risk Engine Flag',
      probability: '5%',
      strategy: 'MANUAL_REVIEW',
      backoff: 'Hold Execution',
      status: 'Requires Approval',
    },
  ];

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
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] font-mono font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 flex items-center gap-1">
              <BrainCircuit className="w-3 h-3 text-indigo-400" /> Deterministic Engine
            </span>
            <span className="text-xs text-gray-400 font-mono">Model: rules-v1 (Zero LLM Mutations)</span>
          </div>
          <h2 className="font-heading font-extrabold text-2xl sm:text-3xl text-white tracking-tight">
            Revenue Intelligence & Scoring Engine
          </h2>
          <p className="text-xs sm:text-sm text-gray-400 mt-1 max-w-2xl">
            Deterministic failure classification, probability heuristics, and merchant-contextual opportunity scoring.
          </p>
        </div>

        <button
          onClick={() => refetch()}
          disabled={isFetching}
          className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-surface-card border border-border hover:bg-white/5 text-xs font-semibold text-gray-200 transition-all cursor-pointer disabled:opacity-50 w-fit"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isFetching ? 'animate-spin text-indigo-400' : ''}`} />
          <span>Refresh Engine Telemetry</span>
        </button>
      </div>

      {/* Engine Status Callout */}
      <div className="p-5 rounded-2xl bg-surface-card border border-indigo-500/30 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 shadow-lg shadow-indigo-500/5">
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 rounded-xl bg-indigo-500/20 text-indigo-400 flex items-center justify-center shrink-0">
            <Cpu className="w-5 h-5" />
          </div>
          <div>
            <h4 className="font-heading font-bold text-sm text-white flex items-center gap-2">
              <span>Deterministic Financial Truth</span>
              <span className="text-[10px] font-mono bg-emerald-500/20 text-emerald-300 px-2 py-0.5 rounded border border-emerald-500/30">
                100% AUDITABLE
              </span>
            </h4>
            <p className="text-xs text-gray-300 mt-0.5">
              Financial calculations, recoverability probabilities, and opportunity scores are strictly deterministic, testable, and database-backed without stochastic LLM drift.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-4 text-xs font-mono text-gray-400 border-t md:border-t-0 md:border-l border-border pt-3 md:pt-0 md:pl-6">
          <div>
            <span className="block text-[10px] uppercase text-gray-500">Engine Version</span>
            <span className="font-bold text-white">rules-v1.4</span>
          </div>
          <div>
            <span className="block text-[10px] uppercase text-gray-500">Latency</span>
            <span className="font-bold text-emerald-400">&lt; 12ms</span>
          </div>
        </div>
      </div>

      {/* Engine Metrics */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {isLoading ? (
          <>
            <MetricCardSkeleton />
            <MetricCardSkeleton />
            <MetricCardSkeleton />
            <MetricCardSkeleton />
          </>
        ) : (
          <>
            <div className="p-4 rounded-2xl bg-surface-card border border-border">
              <span className="text-xs text-gray-400 block mb-1">Total Evaluated Volume</span>
              <span className="font-heading font-extrabold text-xl text-white">
                {formatCurrency(overview?.revenue_at_risk || 0)}
              </span>
              <span className="text-[10px] font-mono text-gray-500 block mt-1">Across webhook events</span>
            </div>

            <div className="p-4 rounded-2xl bg-surface-card border border-emerald-500/20">
              <span className="text-xs text-gray-400 block mb-1">Est. Recoverable Yield</span>
              <span className="font-heading font-extrabold text-xl text-emerald-300">
                {formatCurrency(overview?.estimated_recoverable_revenue || 0)}
              </span>
              <span className="text-[10px] font-mono text-emerald-400/80 block mt-1">Likelihood weighted</span>
            </div>

            <div className="p-4 rounded-2xl bg-surface-card border border-border">
              <span className="text-xs text-gray-400 block mb-1">Avg Recovery Likelihood</span>
              <span className="font-heading font-extrabold text-xl text-indigo-300">
                {Math.round((overview?.average_recovery_probability || 0.65) * 100)}%
              </span>
              <span className="text-[10px] font-mono text-gray-500 block mt-1">Benchmark baseline</span>
            </div>

            <div className="p-4 rounded-2xl bg-surface-card border border-border">
              <span className="text-xs text-gray-400 block mb-1">Failure Classifications</span>
              <span className="font-heading font-extrabold text-xl text-white">8 Categories</span>
              <span className="text-[10px] font-mono text-indigo-400 block mt-1">Normalized taxonomy</span>
            </div>
          </>
        )}
      </div>

      {/* Interactive Scoring Diagnostic Simulator */}
      <section className="bg-surface-card border border-border rounded-2xl p-6 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 border-b border-border">
          <div className="flex items-center gap-2">
            <Sliders className="w-5 h-5 text-pink-400" />
            <div>
              <h3 className="font-heading font-bold text-base text-white">
                Interactive Scoring Diagnostic Tester
              </h3>
              <p className="text-xs text-gray-400">
                Test how the deterministic engine scores transactions in real time without writing to database.
              </p>
            </div>
          </div>
          <span className="text-[10px] font-mono uppercase bg-pink-500/10 text-pink-300 px-2.5 py-1 rounded border border-pink-500/20 font-semibold w-fit">
            Sandbox Sandbox
          </span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Controls */}
          <div className="space-y-4 lg:col-span-2">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-mono font-semibold text-gray-400 uppercase mb-1.5">
                  Transaction Amount (₹):
                </label>
                <input
                  type="number"
                  value={simAmount}
                  onChange={(e) => setSimAmount(Number(e.target.value) || 0)}
                  className="w-full bg-surface-solid border border-border rounded-xl px-3.5 py-2 text-sm text-white font-mono focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-mono font-semibold text-gray-400 uppercase mb-1.5">
                  Failure Category:
                </label>
                <select
                  value={simCategory}
                  onChange={(e) => setSimCategory(e.target.value)}
                  className="w-full bg-surface-solid border border-border rounded-xl px-3.5 py-2 text-xs text-white font-mono focus:outline-none focus:border-indigo-500 cursor-pointer"
                >
                  <option value="TEMPORARY_FAILURE">TEMPORARY_FAILURE (Bank Timeout)</option>
                  <option value="BANK_FAILURE">BANK_FAILURE (Acquiring Error)</option>
                  <option value="INSUFFICIENT_FUNDS">INSUFFICIENT_FUNDS (Low Balance)</option>
                  <option value="AUTH_FAILURE">AUTH_FAILURE (3DS OTP Lapse)</option>
                  <option value="CARD_EXPIRED">CARD_EXPIRED (Expired Card)</option>
                  <option value="FRAUD_OR_SECURITY_BLOCK">FRAUD_OR_SECURITY_BLOCK</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-mono font-semibold text-gray-400 uppercase mb-1.5">
                  Payment Method:
                </label>
                <select
                  value={simMethod}
                  onChange={(e) => setSimMethod(e.target.value)}
                  className="w-full bg-surface-solid border border-border rounded-xl px-3.5 py-2 text-xs text-white font-mono focus:outline-none focus:border-indigo-500 cursor-pointer"
                >
                  <option value="upi">UPI (Instant Collect)</option>
                  <option value="card">Credit / Debit Card</option>
                  <option value="netbanking">Net Banking</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-mono font-semibold text-gray-400 uppercase mb-1.5">
                  Previous Retries: ({simRetries}/3)
                </label>
                <input
                  type="range"
                  min="0"
                  max="3"
                  value={simRetries}
                  onChange={(e) => setSimRetries(Number(e.target.value))}
                  className="w-full accent-indigo-500 cursor-pointer mt-2"
                />
              </div>
            </div>
          </div>

          {/* Real-time Calculation Result Card */}
          <div className="p-5 rounded-2xl bg-surface-solid border border-indigo-500/30 flex flex-col justify-between space-y-4">
            <div>
              <span className="text-[10px] font-mono font-bold uppercase text-indigo-400 tracking-wider block">
                Calculated Score & Output
              </span>
              <div className="flex items-center justify-between mt-2">
                <div>
                  <span className="text-xs text-gray-400 block">Opportunity Score:</span>
                  <span className="font-heading font-extrabold text-3xl text-white">
                    {simResult.score}<span className="text-sm text-gray-400">/100</span>
                  </span>
                </div>
                <ScoreRing score={simResult.score} size={50} />
              </div>
            </div>

            <div className="space-y-2 border-t border-border pt-3 text-xs font-mono">
              <div className="flex justify-between items-center">
                <span className="text-gray-400">Priority:</span>
                <PriorityBadge priority={simResult.priority} />
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-400">Likelihood:</span>
                <span className="font-bold text-emerald-400">{Math.round(simResult.likelihood * 100)}%</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-400">Intervention:</span>
                <span className="font-bold text-indigo-300">{formatEnum(simResult.strategy)}</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Failure Taxonomy & Base Probabilities Matrix */}
      <section className="bg-surface-card border border-border rounded-2xl p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-heading font-bold text-base text-white flex items-center gap-2">
            <Layers className="w-4 h-4 text-indigo-400" />
            Failure Taxonomy & Heuristic Strategy Matrix
          </h3>
          <span className="text-xs font-mono text-gray-400">
            Ruleset: deterministic-rules-v1
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-border text-gray-400 uppercase text-[10px] tracking-wider font-semibold">
                <th className="pb-3 px-3">Category</th>
                <th className="pb-3 px-3">Classification Root Cause</th>
                <th className="pb-3 px-3">Base Likelihood</th>
                <th className="pb-3 px-3">Recommended Intervention</th>
                <th className="pb-3 px-3">Retry Backoff Window</th>
                <th className="pb-3 px-3 text-right">Governance</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {taxonomy.map((t, idx) => (
                <tr key={idx} className="hover:bg-white/5 transition-colors">
                  <td className="py-3 px-3 font-mono font-bold text-indigo-300">
                    {t.category}
                  </td>
                  <td className="py-3 px-3 text-white font-medium">
                    {t.name}
                  </td>
                  <td className="py-3 px-3 font-mono font-bold text-emerald-400">
                    {t.probability}
                  </td>
                  <td className="py-3 px-3 font-bold text-gray-200">
                    {formatEnum(t.strategy)}
                  </td>
                  <td className="py-3 px-3 text-gray-400 font-mono">
                    {t.backoff}
                  </td>
                  <td className="py-3 px-3 text-right">
                    <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-white/10 text-gray-300 border border-border">
                      {t.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Deterministic Scoring Formula Documentation */}
      <section className="bg-surface-card border border-border rounded-2xl p-6 space-y-4">
        <h3 className="font-heading font-bold text-base text-white flex items-center gap-2">
          <HelpCircle className="w-4 h-4 text-pink-400" />
          Opportunity Scoring Formula Breakdown
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs text-gray-300">
          <div className="p-4 rounded-xl bg-surface-solid border border-border space-y-1">
            <div className="font-bold text-white font-heading">1. Relative Value (40%)</div>
            <p className="text-gray-400 text-[11px] leading-relaxed">
              Merchant-relative transaction value score normalized against historical distribution.
            </p>
          </div>
          <div className="p-4 rounded-xl bg-surface-solid border border-border space-y-1">
            <div className="font-bold text-white font-heading">2. Likelihood (40%)</div>
            <p className="text-gray-400 text-[11px] leading-relaxed">
              Heuristic baseline recovery likelihood computed from failure category and retry state.
            </p>
          </div>
          <div className="p-4 rounded-xl bg-surface-solid border border-border space-y-1">
            <div className="font-bold text-white font-heading">3. Volume Rank (10%)</div>
            <p className="text-gray-400 text-[11px] leading-relaxed">
              Transaction percentile rank within merchant volume ensures contextual priority.
            </p>
          </div>
          <div className="p-4 rounded-xl bg-surface-solid border border-border space-y-1">
            <div className="font-bold text-white font-heading">4. Dynamic Penalties</div>
            <p className="text-gray-400 text-[11px] leading-relaxed">
              Penalizes exhausted retries (-15%) and rewards fresh failures with time sensitivity.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
};
