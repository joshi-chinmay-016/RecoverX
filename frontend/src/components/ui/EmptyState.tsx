import React, { ReactNode } from 'react';
import { cn } from '@/lib/utils';
import { AlertCircle } from 'lucide-react';

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title,
  description,
  action,
  className,
}) => {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center p-12 text-center bg-surface-card/40 border border-border border-dashed rounded-2xl',
        className
      )}
    >
      <div className="w-12 h-12 rounded-xl bg-white/5 flex items-center justify-center text-gray-400 mb-4">
        {icon || <AlertCircle className="w-6 h-6" />}
      </div>
      <h3 className="font-heading font-semibold text-lg text-white mb-1">{title}</h3>
      {description && <p className="text-sm text-gray-400 max-w-sm mb-4">{description}</p>}
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
};
