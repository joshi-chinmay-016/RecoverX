import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { getOpportunity } from '@/api/opportunities';
import { getPayment } from '@/api/payments';
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

  if (isOppLoading) {
    return (
      <div className="space-y-6">
        <MetricCardSkeleton />
        <MetricCardSkeleton />
      </div>
    );
  }

  if (isOppError || !opportunity) {
    return (
      <div className="space-y-4">
        <button
          onClick={() => navigate('/opportunities')}
          className="text-xs text-gray-400 hover:text-white flex items-center gap-1 cursor-pointer"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Opportunities
        </button>
        <ErrorState
          title="Opportunity Not Found"
          message={oppError instanceof Error ? oppError.message : 'Unable to find opportunity result in backend'}
          onRetry={refetch}
        />
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Back Button & Top Bar */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => navigate('/opportunities')}
          className="text-xs font-semibold text-gray-400 hover:text-white flex items-center gap-1.5 transition-colors cursor-pointer"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Opportunities Queue
        </button>

        <button
          onClick={() => navigate(`/agent?opportunityId=${opportunity.id}`)}
          className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-indigo-600 to-pink-600 hover:from-indigo-500 hover:to-pink-500 text-white font-bold text-xs rounded-xl shadow-lg shadow-indigo-500/25 transition-all cursor-pointer"
        >
          <Bot className="w-4 h-4" />
          <span>Launch AI Recovery Agent</span>
        </button>
      </div>

      {/* Hero Diagnostic Card */}
      <div className="p-6 rounded-2xl bg-surface-card border border-border flex flex-col md:flex-row items-start md:items-center justify-between gap-6 relative overflow-hidden before:absolute before:top-0 before:left-0 before:right-0 before:h-1 before:bg-gradient-to-r before:from-indigo-500 before:via-pink-500 before:to-emerald-500">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="text-[10px] font-mono uppercase font-bold text-indigo-400 bg-indigo-500/15 px-2 py-0.5 rounded border border-indigo-500/30">
              Recovery Opportunity
            </span>
            <PriorityBadge priority={opportunity.priority} />
          </div>
          <h2 className="font-heading font-extrabold text-3xl sm:text-4xl text-white tracking-tight">
            {formatCurrency(opportunity.revenue_at_risk)}
          </h2>
          <p className="text-xs sm:text-sm text-gray-400 mt-1 flex items-center gap-2">
            <span>Root Cause:</span>
            <strong className="text-gray-200">{formatEnum(opportunity.failure_category)}</strong>
          </p>
        </div>

        <div className="flex items-center gap-8 border-t md:border-t-0 md:border-l border-border pt-4 md:pt-0 md:pl-8">
          <div className="text-center">
            <div className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-1">
              Recovery Likelihood
            </div>
            <div className="font-heading font-bold text-2xl text-emerald-400">
              {Math.round(opportunity.recovery_probability * 100)}%
            </div>
          </div>

          <div className="text-center">
            <div className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-1">
              Opportunity Score
            </div>
            <ScoreRing score={opportunity.opportunity_score} size={54} strokeWidth={5} />
          </div>
        </div>
      </div>

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
              <span className="font-semibold text-rose-400">FAILED</span>
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
