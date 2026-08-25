import React from 'react';
import { cn } from '@/lib/utils';

interface ProbabilityBarProps {
  probability: number; // 0.0 - 1.0 or 0 - 100
  className?: string;
  showPercent?: boolean;
}

export const ProbabilityBar: React.FC<ProbabilityBarProps> = ({
  probability,
  className,
  showPercent = true,
}) => {
  const pct = probability <= 1.0 ? probability * 100 : probability;
  const boundedPct = Math.max(0, Math.min(100, pct || 0));

  const getGradient = (val: number) => {
    if (val >= 75) return 'from-emerald-500 to-teal-400';
    if (val >= 50) return 'from-blue-500 to-indigo-400';
    if (val >= 30) return 'from-amber-500 to-yellow-400';
    return 'from-rose-500 to-pink-500';
  };

  return (
    <div className={cn('flex items-center gap-2.5 w-full', className)}>
      <div className="flex-1 h-2 bg-white/10 rounded-full overflow-hidden">
        <div
          className={cn('h-full rounded-full bg-gradient-to-r transition-all duration-500', getGradient(boundedPct))}
          style={{ width: `${boundedPct}%` }}
        />
      </div>
      {showPercent && (
        <span className="text-xs font-mono font-semibold text-gray-200 min-w-[36px] text-right">
          {Math.round(boundedPct)}%
        </span>
      )}
    </div>
  );
};
