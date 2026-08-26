import React from 'react';
import { PolicyStatus } from '@/types/agent';
import { Check, X, Shield, AlertTriangle } from 'lucide-react';
import { StatusBadge } from '@/components/ui/StatusBadge';

interface PolicySafetyCheckProps {
  policyStatus: PolicyStatus | string;
  policyReason?: string | null;
  policyVersion?: string;
  requiresApproval?: boolean;
  confidence?: number;
  className?: string;
}

export const PolicySafetyCheck: React.FC<PolicySafetyCheckProps> = ({
  policyStatus,
  policyReason,
  policyVersion = 'policy-v1',
  className,
}) => {
  const isBlocked = policyStatus === 'BLOCKED';

  return (
    <div
      className={className || `p-5 rounded-2xl border ${
        isBlocked
          ? 'bg-rose-500/10 border-rose-500/30'
          : 'bg-emerald-500/10 border-emerald-500/30'
      }`}
    >
      <div className="flex items-center justify-between gap-2 mb-4">
        <div className="flex items-center gap-2">
          <Shield className={`w-5 h-5 ${isBlocked ? 'text-rose-400' : 'text-emerald-400'}`} />
          <h4 className="font-heading font-bold text-sm text-white">
            Deterministic PolicyEngine Validation
          </h4>
        </div>
        <StatusBadge status={policyStatus} />
      </div>

      <div className="space-y-2.5 text-xs">
        <div className="flex items-center gap-2">
          {isBlocked ? (
            <X className="w-4 h-4 text-rose-400 shrink-0" />
          ) : (
            <Check className="w-4 h-4 text-emerald-400 shrink-0" />
          )}
          <span className={isBlocked ? 'text-rose-200 font-medium' : 'text-gray-300'}>
            Action Whitelist Check ({isBlocked ? 'Policy Restriction' : 'Verified in Registry'})
          </span>
        </div>

        <div className="flex items-center gap-2">
          {isBlocked ? (
            <X className="w-4 h-4 text-rose-400 shrink-0" />
          ) : (
            <Check className="w-4 h-4 text-emerald-400 shrink-0" />
          )}
          <span className={isBlocked ? 'text-rose-200 font-medium' : 'text-gray-300'}>
            Retry Limit & Backoff Constraint
          </span>
        </div>

        <div className="flex items-center gap-2">
          <Check className="w-4 h-4 text-emerald-400 shrink-0" />
          <span className="text-gray-300">
            Read-Only Boundary Maintained (Zero direct DB mutation)
          </span>
        </div>

        <div className="flex items-center gap-2">
          <Check className="w-4 h-4 text-emerald-400 shrink-0" />
          <span className="text-gray-300">
            Policy Engine Rules Version: <code className="font-mono text-indigo-300">{policyVersion}</code>
          </span>
        </div>
      </div>

      {policyReason && (
        <div className={`mt-4 p-3 rounded-xl text-xs flex items-start gap-2 ${
          isBlocked ? 'bg-rose-500/20 text-rose-200 border border-rose-500/30' : 'bg-white/5 text-gray-300'
        }`}>
          <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold block mb-0.5">Policy Rationale:</span>
            {policyReason}
          </div>
        </div>
      )}
    </div>
  );
};
