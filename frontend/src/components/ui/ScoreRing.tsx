import React from 'react';
import { cn } from '@/lib/utils';

interface ScoreRingProps {
  score: number; // 0 - 100
  size?: number;
  strokeWidth?: number;
  className?: string;
  showLabel?: boolean;
}

export const ScoreRing: React.FC<ScoreRingProps> = ({
  score,
  size = 72,
  strokeWidth = 6,
  className,
  showLabel = true,
}) => {
  const boundedScore = Math.max(0, Math.min(100, score || 0));
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (boundedScore / 100) * circumference;

  const getColor = (s: number) => {
    if (s >= 80) return '#EC4899'; // Critical / High value
    if (s >= 60) return '#F59E0B'; // High
    if (s >= 40) return '#3B82F6'; // Medium
    return '#10B981'; // Low
  };

  return (
    <div className={cn('relative inline-flex items-center justify-center', className)}>
      <svg width={size} height={size} className="transform -rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="rgba(255, 255, 255, 0.08)"
          strokeWidth={strokeWidth}
          fill="none"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={getColor(boundedScore)}
          strokeWidth={strokeWidth}
          fill="none"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          className="transition-all duration-700 ease-out"
        />
      </svg>
      {showLabel && (
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="font-heading font-bold text-sm text-white">
            {boundedScore.toFixed(0)}
          </span>
          <span className="text-[9px] text-gray-400 font-sans -mt-1">/100</span>
        </div>
      )}
    </div>
  );
};

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
