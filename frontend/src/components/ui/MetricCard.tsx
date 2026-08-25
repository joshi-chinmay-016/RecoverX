import React, { ReactNode } from 'react';
import { cn } from '@/lib/utils';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: ReactNode;
  variant?: 'danger' | 'success' | 'warning' | 'critical' | 'primary' | 'default';
  className?: string;
  badgeText?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  icon,
  variant = 'default',
  className,
  badgeText,
}) => {
  const borderStyles: Record<string, string> = {
    danger: 'before:bg-gradient-to-r before:from-rose-500 before:to-amber-500',
    success: 'before:bg-gradient-to-r before:from-emerald-500 before:to-indigo-500',
    warning: 'before:bg-gradient-to-r before:from-amber-500 before:to-rose-500',
    critical: 'before:bg-gradient-to-r before:from-pink-500 before:to-purple-500',
    primary: 'before:bg-gradient-to-r before:from-indigo-500 before:to-cyan-500',
    default: 'before:bg-gradient-to-r before:from-gray-600 before:to-gray-700',
  };

  const iconPillStyles: Record<string, string> = {
    danger: 'bg-rose-500/15 text-rose-400',
    success: 'bg-emerald-500/15 text-emerald-400',
    warning: 'bg-amber-500/15 text-amber-400',
    critical: 'bg-pink-500/15 text-pink-400',
    primary: 'bg-indigo-500/15 text-indigo-400',
    default: 'bg-gray-800 text-gray-400',
  };

  return (
    <div
      className={cn(
        'relative bg-surface-card backdrop-blur-md border border-border rounded-2xl p-5 overflow-hidden transition-all duration-300 hover:-translate-y-1 hover:border-highlight hover:shadow-xl hover:shadow-black/40',
        'before:absolute before:top-0 before:left-0 before:right-0 before:h-1',
        borderStyles[variant],
        className
      )}
    >
      <div className="flex items-center justify-between gap-2 mb-2">
        <span className="text-xs font-semibold uppercase tracking-wider text-gray-400 font-sans">
          {title}
        </span>
        {icon && (
          <div className={cn('w-8 h-8 rounded-lg flex items-center justify-center text-sm', iconPillStyles[variant])}>
            {icon}
          </div>
        )}
      </div>

      <div className="flex items-baseline gap-2">
        <div className="font-heading text-2xl sm:text-3xl font-bold tracking-tight text-white">
          {value}
        </div>
        {badgeText && (
          <span className="text-[10px] uppercase font-bold px-1.5 py-0.5 rounded bg-white/10 text-gray-300">
            {badgeText}
          </span>
        )}
      </div>

      {subtitle && (
        <div className="mt-1 text-xs text-gray-400 font-sans">
          {subtitle}
        </div>
      )}
    </div>
  );
};
