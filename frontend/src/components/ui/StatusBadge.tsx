import React from 'react';
import { cn } from '@/lib/utils';

interface StatusBadgeProps {
  status: string;
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, className }) => {
  const s = (status || 'UNKNOWN').toUpperCase();

  const getStyle = (val: string) => {
    switch (val) {
      case 'ALLOWED':
      case 'CAPTURED':
      case 'RESOLVED':
      case 'COMPLETED':
        return 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30';
      case 'BLOCKED':
      case 'FAILED':
      case 'CLOSED':
        return 'bg-rose-500/15 text-rose-400 border-rose-500/30';
      case 'REQUIRES_APPROVAL':
      case 'AUTHORIZED':
      case 'INVESTIGATING':
      case 'PLANNING':
        return 'bg-amber-500/15 text-amber-400 border-amber-500/30';
      case 'OPEN':
      case 'CREATED':
        return 'bg-indigo-500/15 text-indigo-400 border-indigo-500/30';
      default:
        return 'bg-gray-500/15 text-gray-400 border-gray-500/30';
    }
  };

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wider border',
        getStyle(s),
        className
      )}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-current" />
      {s.replace(/_/g, ' ')}
    </span>
  );
};
