import React from 'react';
import { PriorityLevel } from '@/types/intelligence';
import { cn } from '@/lib/utils';

interface PriorityBadgeProps {
  priority: PriorityLevel | string;
  className?: string;
}

export const PriorityBadge: React.FC<PriorityBadgeProps> = ({ priority, className }) => {
  const p = (priority || 'LOW').toUpperCase();

  const styles: Record<string, string> = {
    CRITICAL: 'bg-pink-500/15 text-pink-400 border-pink-500/30',
    HIGH: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
    MEDIUM: 'bg-blue-500/15 text-blue-400 border-blue-500/30',
    LOW: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
  };

  const styleClass = styles[p] || 'bg-gray-500/15 text-gray-400 border-gray-500/30';

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wider border',
        styleClass,
        className
      )}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-current opacity-75" />
      {p}
    </span>
  );
};
