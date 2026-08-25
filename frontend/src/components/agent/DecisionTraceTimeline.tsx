import React from 'react';
import { DecisionTrace } from '@/types/agent';
import { Clock, Eye, Lightbulb, ShieldCheck } from 'lucide-react';

interface DecisionTraceTimelineProps {
  traces: DecisionTrace[];
  toolCalls?: any[];
  className?: string;
}

export const DecisionTraceTimeline: React.FC<DecisionTraceTimelineProps> = ({
  traces,
  toolCalls,
  className,
}) => {
  return (
    <div className={className || 'space-y-4'}>
      <h4 className="font-heading font-semibold text-sm text-gray-300 flex items-center gap-2">
        <Clock className="w-4 h-4 text-indigo-400" />
        Safe Observability Decision Trace
      </h4>

      {toolCalls && toolCalls.length > 0 && (
        <div className="bg-white/5 border border-border rounded-xl p-3.5 space-y-2">
          <div className="text-xs font-semibold text-indigo-300 uppercase tracking-wider font-mono">
            Read-Only Tools Executed ({toolCalls.length})
          </div>
          <div className="space-y-1.5">
            {toolCalls.map((tc, idx) => (
              <div key={idx} className="flex items-center justify-between text-xs text-gray-300 bg-white/5 py-1.5 px-3 rounded-lg font-mono">
                <span>{tc.tool_name}</span>
                <span className="text-emerald-400">{tc.execution_time_ms}ms</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {traces.map((trace, idx) => (
        <div
          key={idx}
          className="relative pl-6 pb-4 border-l border-indigo-500/30 last:border-l-0 last:pb-0"
        >
          <div className="absolute -left-1.5 top-0 w-3 h-3 rounded-full bg-indigo-500 ring-4 ring-[#0B0F19]" />
          
          <div className="bg-surface-solid border border-border rounded-xl p-4 space-y-2">
            <div className="flex items-center justify-between gap-2">
              <div className="text-xs font-bold text-white flex items-center gap-1.5">
                <Lightbulb className="w-3.5 h-3.5 text-amber-400" />
                {trace.decision}
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300">
                Confidence: {(trace.confidence * 100).toFixed(0)}%
              </span>
            </div>

            <div className="text-xs text-gray-300 flex items-start gap-1.5">
              <Eye className="w-3.5 h-3.5 text-blue-400 shrink-0 mt-0.5" />
              <span><strong>Observation:</strong> {trace.observation}</span>
            </div>

            <div className="text-xs text-gray-400 flex items-start gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
              <span><strong>Evidence:</strong> {trace.evidence}</span>
            </div>

            <p className="text-xs text-indigo-200/80 bg-indigo-950/40 p-2.5 rounded-lg border border-indigo-500/20">
              <strong>Rationale:</strong> {trace.reason}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
};
