import React from 'react';
import { AgentAction } from '@/types/agent';
import { formatEnum } from '@/lib/formatters';
import { PriorityBadge } from '@/components/ui/PriorityBadge';
import { Lock, UserCheck } from 'lucide-react';

interface ProposedActionCardProps {
  action: AgentAction;
  index: number;
}

export const ProposedActionCard: React.FC<ProposedActionCardProps> = ({ action, index }) => {
  return (
    <div className="bg-surface-solid border border-border rounded-2xl p-5 space-y-3 hover:border-highlight transition-all">
      <div className="flex items-start justify-between gap-3">
        <div>
          <span className="text-[10px] font-mono font-bold uppercase text-indigo-400">
            Action #{index + 1}
          </span>
          <h4 className="font-heading font-bold text-base text-white mt-0.5">
            {formatEnum(action.action_type)}
          </h4>
        </div>
        <div className="flex items-center gap-2">
          <PriorityBadge priority={action.risk_level} />
          {action.requires_approval ? (
            <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30 flex items-center gap-1">
              <UserCheck className="w-3 h-3" /> Approval Required
            </span>
          ) : (
            <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
              Automated
            </span>
          )}
        </div>
      </div>

      <div className="text-xs text-gray-300">
        <span className="font-semibold text-gray-400">Purpose: </span>
        {action.purpose}
      </div>

      <div className="text-xs text-gray-400">
        <span className="font-semibold text-gray-400">Rationale: </span>
        {action.rationale}
      </div>

      <div className="text-xs text-emerald-400/90 bg-emerald-950/30 p-2.5 rounded-xl border border-emerald-500/20">
        <span className="font-semibold">Expected Outcome: </span>
        {action.expected_outcome}
      </div>

      {action.parameters && Object.keys(action.parameters).length > 0 && (
        <div className="text-xs">
          <span className="text-gray-400 font-semibold block mb-1">Parameters:</span>
          <pre className="font-mono text-[11px] bg-black/40 p-2.5 rounded-xl text-gray-300 overflow-x-auto border border-border">
            {JSON.stringify(action.parameters, null, 2)}
          </pre>
        </div>
      )}

      <div className="pt-2 border-t border-border flex items-center justify-between text-[11px] text-amber-400/90 font-medium">
        <span className="flex items-center gap-1">
          <Lock className="w-3 h-3" /> Execution Gate: Held for Approval
        </span>
        <span className="font-mono text-gray-500">Read-Only Safety</span>
      </div>
    </div>
  );
};
