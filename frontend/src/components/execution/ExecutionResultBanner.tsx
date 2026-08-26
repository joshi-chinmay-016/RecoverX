import React from 'react';
import { CheckCircle2, XCircle, AlertTriangle, RefreshCw } from 'lucide-react';
import { ExecutionResultResponse } from '@/types/action';
import { formatCurrency } from '@/lib/formatters';

interface ExecutionResultBannerProps {
  result: ExecutionResultResponse;
  onReconcile?: () => void;
  onRetry?: () => void;
  isReconciling?: boolean;
  isRetrying?: boolean;
}

export const ExecutionResultBanner: React.FC<ExecutionResultBannerProps> = ({
  result,
  onReconcile,
  onRetry,
  isReconciling,
  isRetrying,
}) => {
  if (result.success) {
    return (
      <div className="p-5 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 space-y-3 animate-fade-in">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
            <div>
              <span className="font-heading font-extrabold text-sm text-emerald-300">
                RECOVERY ACTION SUCCEEDED
              </span>
              <p className="text-xs text-emerald-200/80 mt-0.5">
                {result.message}
              </p>
            </div>
          </div>
          {result.recovered_amount_minor && (
            <div className="text-right">
              <span className="text-[10px] uppercase font-mono text-emerald-400 font-semibold block">Recovered</span>
              <span className="font-mono font-bold text-base text-emerald-300">
                {formatCurrency(result.recovered_amount_minor)}
              </span>
            </div>
          )}
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 border-t border-emerald-500/20 text-[11px] font-mono text-emerald-200/80">
          <div>
            <span className="text-gray-400 block text-[10px]">Provider Ref:</span>
            <span className="font-semibold text-white">{result.provider_reference || 'N/A'}</span>
          </div>
          <div>
            <span className="text-gray-400 block text-[10px]">Attempt:</span>
            <span className="font-semibold text-white">#{result.attempt_number}</span>
          </div>
          <div>
            <span className="text-gray-400 block text-[10px]">Gateway Latency:</span>
            <span className="font-semibold text-white">{result.latency_ms}ms</span>
          </div>
          <div>
            <span className="text-gray-400 block text-[10px]">Financial Truth:</span>
            <span className="font-semibold text-emerald-300">CAPTURED</span>
          </div>
        </div>
      </div>
    );
  }

  if (result.is_unknown) {
    return (
      <div className="p-5 rounded-2xl bg-amber-500/10 border border-amber-500/30 space-y-3 animate-fade-in">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0" />
            <div>
              <span className="font-heading font-extrabold text-sm text-amber-300">
                OUTCOME UNKNOWN — PROVIDER TIMEOUT
              </span>
              <p className="text-xs text-amber-200/80 mt-0.5">
                The gateway did not confirm the transaction status within the timeout window. Blind retries are strictly blocked by PolicyEngine.
              </p>
            </div>
          </div>
          {onReconcile && (
            <button
              onClick={onReconcile}
              disabled={isReconciling}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-amber-500 text-black font-bold text-xs hover:bg-amber-400 transition-all cursor-pointer disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isReconciling ? 'animate-spin' : ''}`} />
              <span>Reconcile Now</span>
            </button>
          )}
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 pt-2 border-t border-amber-500/20 text-[11px] font-mono text-amber-200/80">
          <div>
            <span className="text-gray-400 block text-[10px]">Error Code:</span>
            <span className="font-semibold text-amber-300">{result.error_code || 'TIMEOUT'}</span>
          </div>
          <div>
            <span className="text-gray-400 block text-[10px]">Action Status:</span>
            <span className="font-semibold text-amber-300">RECONCILIATION_REQUIRED</span>
          </div>
          <div>
            <span className="text-gray-400 block text-[10px]">Blind Retry:</span>
            <span className="font-semibold text-rose-400">DISABLED (SAFETY)</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-5 rounded-2xl bg-rose-500/10 border border-rose-500/30 space-y-3 animate-fade-in">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <XCircle className="w-5 h-5 text-rose-400 shrink-0" />
          <div>
            <span className="font-heading font-extrabold text-sm text-rose-300">
              RECOVERY ACTION FAILED
            </span>
            <p className="text-xs text-rose-200/80 mt-0.5">
              {result.error_message || result.message}
            </p>
          </div>
        </div>
        {result.is_retryable && onRetry && (
          <button
            onClick={onRetry}
            disabled={isRetrying}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs transition-all cursor-pointer disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRetrying ? 'animate-spin' : ''}`} />
            <span>Retry Action</span>
          </button>
        )}
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 pt-2 border-t border-rose-500/20 text-[11px] font-mono text-rose-200/80">
        <div>
          <span className="text-gray-400 block text-[10px]">Error Code:</span>
          <span className="font-semibold text-rose-300">{result.error_code || 'EXECUTION_ERROR'}</span>
        </div>
        <div>
          <span className="text-gray-400 block text-[10px]">Retryable:</span>
          <span className="font-semibold text-white">{result.is_retryable ? 'YES (Backoff)' : 'NO (Terminal)'}</span>
        </div>
        <div>
          <span className="text-gray-400 block text-[10px]">Attempt:</span>
          <span className="font-semibold text-white">#{result.attempt_number}</span>
        </div>
      </div>
    </div>
  );
};
