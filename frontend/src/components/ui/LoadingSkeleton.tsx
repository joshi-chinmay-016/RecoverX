import React from 'react';
import { cn } from '@/lib/utils';

export const Skeleton: React.FC<{ className?: string }> = ({ className }) => (
  <div className={cn('animate-pulse bg-white/5 rounded-lg', className)} />
);

export const MetricCardSkeleton: React.FC = () => (
  <div className="bg-surface-card border border-border rounded-2xl p-5 flex flex-col gap-3">
    <div className="flex justify-between items-center">
      <Skeleton className="h-4 w-28" />
      <Skeleton className="h-8 w-8 rounded-lg" />
    </div>
    <Skeleton className="h-8 w-36" />
    <Skeleton className="h-3 w-20" />
  </div>
);

export const TableSkeleton: React.FC<{ rows?: number }> = ({ rows = 5 }) => (
  <div className="flex flex-col gap-3 p-4">
    <div className="flex gap-4 mb-2">
      <Skeleton className="h-5 flex-1" />
      <Skeleton className="h-5 flex-1" />
      <Skeleton className="h-5 flex-1" />
      <Skeleton className="h-5 flex-1" />
    </div>
    {Array.from({ length: rows }).map((_, i) => (
      <Skeleton key={i} className="h-12 w-full" />
    ))}
  </div>
);
