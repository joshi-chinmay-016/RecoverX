import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { getOpportunity } from '@/api/opportunities';
import { getPayment } from '@/api/payments';
import { listActions } from '@/api/actions';
import { ActionExecutionCard } from '@/components/execution/ActionExecutionCard';
import { PriorityBadge } from '@/components/ui/PriorityBadge';
import { ScoreRing } from '@/components/ui/ScoreRing';
import { ProbabilityBar } from '@/components/ui/ProbabilityBar';
import { ErrorState } from '@/components/ui/ErrorState';
import { MetricCardSkeleton } from '@/components/ui/LoadingSkeleton';
import { formatCurrency, formatEnum, formatFactorName, formatDate } from '@/lib/formatters';
import {
  ArrowLeft,
  Bot,
  CreditCard,
  AlertCircle,
  Lightbulb,
  Cpu,
  History,
  CheckCircle2,
  TrendingUp,
  Zap,
} from 'lucide-react';

export const OpportunityDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const {
    data: opportunity,
    isLoading: isOppLoading,
    isError: isOppError,
    error: oppError,
    refetch,
  } = useQuery({
    queryKey: ['opportunity', id],
    queryFn: () => getOpportunity(id!),
    enabled: Boolean(id),
  });

  const { data: payment } = useQuery({
    queryKey: ['payment', opportunity?.payment_id],
    queryFn: () => getPayment(opportunity!.payment_id),
    enabled: Boolean(opportunity?.payment_id),
  });

  const { data: actionsData, refetch: refetchActions } = useQuery({
    queryKey: ['actions-for-opportunity', id],
    queryFn: () => listActions({ opportunity_id: id }),
    enabled: Boolean(id),
  });

  if (isOppLoading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-10 bg-surface-card rounded-xl w-48" />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <MetricCardSkeleton />
          <MetricCardSkeleton />
          <MetricCardSkeleton />
          <MetricCardSkeleton />
        </div>
      </div>
    );
  }

  if (isOppError || !opportunity) {
    return (
      <ErrorState
        title="Opportunity Not Found"
        message={oppError instanceof Error ? oppError.message : 'Could not retrieve opportunity intelligence data.'}
        onRetry={() => refetch()}
      />
    );
  }

  const existingActions = actionsData?.items || [];

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Navigation & Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/opportunities')}
            className="p-2.5 rounded-xl bg-surface-card hover:bg-white/5 border border-border text-gray-300 hover:text-white transition-colors cursor-pointer"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="font-heading font-extrabold text-xl sm:text-2xl text-white">
                Opportunity: {opportunity.payment_id}
              </h2>
              <PriorityBadge priority={opportunity.priority} />
            </div>
            <span className="text-xs text-gray-400 font-mono">
              Evaluated {formatDate(opportunity.created_at)}
            </span>
          </div>
        </div>

        {/* CTA: Launch Agent Studio */}
        <button
          onClick={() => navigate(`/agent?opportunityId=${opportunity.id}`)}
          className="flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-500 to-pink-500 hover:from-indigo-400 hover:to-pink-400 text-white font-heading font-extrabold text-xs shadow-lg shadow-indigo-500/25 active:scale-95 transition-all cursor-pointer w-full sm:w-auto"
        >
          <Bot className="w-4 h-4" />
          <span>Launch AI Recovery Agent</span>
        </button>
      </div>

      {/* Hero Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Revenue at Risk */}
        <div className="p-5 rounded-2xl bg-surface-card border border-border flex items-center justify-between">
          <div>
            <span className="text-xs font-mono uppercase text-gray-400 font-semibold block">Revenue at Risk</span>
            <span className="font-heading font-extrabold text-2xl text-rose-400 mt-1 block">
              {formatCurrency(opportunity.revenue_at_risk)}
            </span>
            <span className="text-[11px] text-gray-400 font-mono mt-0.5 block">PAISE: {opportunity.revenue_at_risk}</span>
          </div>
          <div className="w-10 h-10 rounded-xl bg-rose-500/10 text-rose-400 flex items-center justify-center">
            <AlertCircle className="w-5 h-5" />
          </div>
        </div>

        {/* Recovery Likelihood */}
        <div className="p-5 rounded-2xl bg-surface-card border border-border flex flex-col justify-between">
          <span className="text-xs font-mono uppercase text-gray-400 font-semibold block">Recovery Likelihood</span>
          <div className="mt-2">
            <ProbabilityBar probability={opportunity.recovery_likelihood} showLabel={false} />
            <div className="flex justify-between items-center text-xs font-mono mt-1 text-gray-300">
              <span>Likelihood:</span>
              <strong className="text-emerald-400">{Math.round(opportunity.recovery_likelihood * 100)}%</strong>
            </div>
          </div>
        </div>

        {/* Opportunity Score */}
        <div className="p-5 rounded-2xl bg-surface-card border border-border flex items-center justify-between">
          <div>
            <span className="text-xs font-mono uppercase text-gray-400 font-semibold block">Opportunity Score</span>
            <span className="font-heading font-extrabold text-2xl text-white mt-1 block">
              {opportunity.opportunity_score}/100
            </span>
            <span className="text-[11px] text-indigo-300 font-mono mt-0.5 block">Merchant Normalized</span>
          </div>
          <ScoreRing score={opportunity.opportunity_score} size={50} />
        </div>

        {/* Failure Category */}
        <div className="p-5 rounded-2xl bg-surface-card border border-border flex items-center justify-between">
          <div>
            <span className="text-xs font-mono uppercase text-gray-400 font-semibold block">Classified Root Cause</span>
            <span className="font-heading font-bold text-base text-indigo-300 mt-1 block truncate max-w-[140px]">
              {formatEnum(opportunity.failure_category)}
            </span>
            <span className="text-[11px] text-gray-400 font-mono mt-0.5 block">
              Confidence: {Math.round((opportunity.category_confidence || 0.9) * 100)}%
            </span>
          </div>
          <div className="w-10 h-10 rounded-xl bg-indigo-500/10 text-indigo-400 flex items-center justify-center">
            <Cpu className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* Controlled Execution Actions Section (Phase 4) */}
      {existingActions.length > 0 && (
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-heading font-bold text-base text-white flex items-center gap-2">
              <Zap className="w-4 h-4 text-pink-400" />
              Controlled Recovery Actions
            </h3>
            <span className="text-xs font-mono text-gray-400">
              {existingActions.length} Actions Linked
            </span>
          </div>

          <div className="space-y-4">
            {existingActions.map((act) => (
              <ActionExecutionCard
                key={act.id}
                action={act}
                onUpdated={() => {
                  refetch();
                  refetchActions();
                }}
              />
            ))}
          </div>
        </section>
      )}

      {/* Grid: Context & Contributing Factors */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Payment & Failure Context */}
        <div className="bg-surface-card border border-border rounded-2xl p-6 space-y-4">
          <h3 className="font-heading font-bold text-base text-white flex items-center gap-2">
            <CreditCard className="w-4 h-4 text-indigo-400" />
            Financial Payment Context
          </h3>

          <div className="divide-y divide-border text-xs">
            <div className="py-2.5 flex justify-between">
              <span className="text-gray-400">Payment ID:</span>
              <span className="font-mono text-indigo-300 font-semibold">{opportunity.payment_id}</span>
            </div>
            <div className="py-2.5 flex justify-between">
              <span className="text-gray-400">Status:</span>
              <span className="font-semibold text-rose-400">{payment?.status || 'FAILED'}</span>
            </div>
            <div className="py-2.5 flex justify-between">
              <span className="text-gray-400">Gateway Error Reason:</span>
              <span className="font-mono text-gray-200">{opportunity.failure_reason || 'N/A'}</span>
            </div>
            <div className="py-2.5 flex justify-between">
              <span className="text-gray-400">Created Timestamp:</span>
              <span className="text-gray-300">{formatDate(opportunity.created_at)}</span>
            </div>
            {payment?.attempts && (
              <div className="py-2.5 flex justify-between">
                <span className="text-gray-400">Payment Attempts:</span>
                <span className="font-mono text-white">{payment.attempts.length} attempts</span>
              </div>
            )}
          </div>
        </div>

        {/* Deterministic Rationale */}
        <div className="bg-surface-card border border-border rounded-2xl p-6 space-y-4">
          <h3 className="font-heading font-bold text-base text-white flex items-center gap-2">
            <Lightbulb className="w-4 h-4 text-amber-400" />
            Recommended Intervention
          </h3>

          <div className="p-4 rounded-xl bg-surface-solid border border-border space-y-2">
            <div className="text-xs font-semibold text-gray-400 uppercase">Recommendation:</div>
            <div className="font-heading font-bold text-base text-indigo-300">
              {formatEnum(opportunity.recommended_intervention)}
            </div>
            <p className="text-xs text-gray-300 leading-relaxed">
              {opportunity.intervention_reason || opportunity.explanation}
            </p>
          </div>

          <div className="flex items-center justify-between text-xs text-gray-400 pt-2">
            <span>Model Version: <code className="font-mono text-indigo-300">{opportunity.model_version}</code></span>
            <span>Est. Recoverable: <strong className="text-emerald-400">{formatCurrency(opportunity.estimated_recoverable_revenue)}</strong></span>
          </div>
        </div>
      </div>

      {/* Contributing Factors Analysis */}
      <div className="bg-surface-card border border-border rounded-2xl p-6 space-y-4">
        <h3 className="font-heading font-bold text-base text-white flex items-center gap-2">
          <TrendingUp className="w-4 h-4 text-emerald-400" />
          Contributing Scoring Factors & Telemetry
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
          {opportunity.factors && opportunity.factors.length > 0 ? (
            opportunity.factors.map((factor, idx) => {
              const factorName = factor.factor || factor.name || 'Factor';
              const impact = factor.impact !== undefined ? factor.impact : 0;
              const isPositive = impact >= 0;

              return (
                <div
                  key={idx}
                  className="p-3.5 rounded-xl bg-white/5 border border-border flex items-center justify-between"
                >
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className={`w-4 h-4 ${isPositive ? 'text-emerald-400' : 'text-amber-400'}`} />
                    <span className="text-xs font-medium text-gray-200">
                      {formatFactorName(factorName)}
                    </span>
                  </div>
                  <span
                    className={`text-xs font-mono font-bold px-2 py-0.5 rounded ${
                      isPositive
                        ? 'bg-emerald-500/20 text-emerald-300'
                        : 'bg-amber-500/20 text-amber-300'
                    }`}
                  >
                    {isPositive ? `+${impact}` : impact}
                  </span>
                </div>
              );
            })
          ) : (
            <div className="col-span-3 text-xs text-gray-500 py-4 text-center">
              Evaluated with standard baseline heuristic weights.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
