import React from 'react';
import { AgentAction } from '@/types/agent';
import { ArrowDown, CheckCircle, ShieldAlert } from 'lucide-react';
import { formatEnum } from '@/lib/formatters';

interface AgentFlowDiagramProps {
  proposedActions: AgentAction[];
  fallbackStrategy?: string;
  className?: string;
}

export const AgentFlowDiagram: React.FC<AgentFlowDiagramProps> = ({
  proposedActions,
  fallbackStrategy = 'MANUAL_REVIEW',
  className,
}) => {
  return (
    <div className={className || 'flex flex-col items-center gap-2 py-4'}>
      {proposedActions.map((action, idx) => (
        <React.Fragment key={idx}>
          <div className="w-full max-w-md bg-surface-solid border border-indigo-500/40 rounded-xl p-4 shadow-lg shadow-black/30 text-center relative group hover:border-indigo-400 transition-colors">
            <div className="text-[10px] font-mono font-bold tracking-wider uppercase text-indigo-400">
              Step {idx + 1} — Proposed Action
            </div>
            <div className="text-base font-heading font-bold text-white mt-1">
              {formatEnum(action.action_type)}
            </div>
            {action.purpose && (
              <p className="text-xs text-gray-400 mt-1 max-w-xs mx-auto">
                {action.purpose}
              </p>
            )}
            {action.parameters && Object.keys(action.parameters).length > 0 && (
              <div className="mt-2 text-[11px] font-mono bg-white/5 py-1 px-2.5 rounded-lg text-indigo-200 inline-block">
                {JSON.stringify(action.parameters)}
              </div>
            )}
          </div>
          <ArrowDown className="w-4 h-4 text-indigo-400 animate-bounce" />
        </React.Fragment>
      ))}

      {/* Outcome Gate */}
      <div className="w-full max-w-md bg-surface-solid border border-emerald-500/40 rounded-xl p-4 shadow-lg text-center">
        <div className="text-[10px] font-mono font-bold tracking-wider uppercase text-emerald-400 flex items-center justify-center gap-1">
          <CheckCircle className="w-3.5 h-3.5" /> Outcome Evaluation Gate
        </div>
        <div className="text-xs text-emerald-300 font-semibold mt-1">
          IF CAPTURED → CLOSE RECOVERY CASE
        </div>
        <div className="text-[11px] text-gray-400 mt-1 flex items-center justify-center gap-1">
          <ShieldAlert className="w-3 h-3 text-amber-400" /> IF FAILED → TRIGGER FALLBACK ({formatEnum(fallbackStrategy)})
        </div>
      </div>
    </div>
  );
};
