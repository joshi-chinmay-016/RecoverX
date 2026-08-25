import React from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { RefreshCw, Server, Zap } from 'lucide-react';

export const Navbar: React.FC = () => {
  const queryClient = useQueryClient();
  const [isRefreshing, setIsRefreshing] = React.useState(false);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await queryClient.invalidateQueries();
    setTimeout(() => setIsRefreshing(false), 500);
  };

  return (
    <header className="h-16 border-b border-border bg-surface-solid/50 backdrop-blur-md px-8 flex items-center justify-between sticky top-0 z-40">
      {/* Pipeline Indicators */}
      <div className="flex items-center gap-2">
        <div className="hidden sm:flex items-center gap-2 bg-white/5 px-3 py-1.5 rounded-full border border-border text-xs">
          <span className="flex items-center gap-1.5 font-semibold text-emerald-300">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            Financial Core
          </span>
          <span className="text-gray-600">→</span>
          <span className="font-semibold text-indigo-300">
            Revenue Intelligence
          </span>
          <span className="text-gray-600">→</span>
          <span className="font-semibold text-pink-300 flex items-center gap-1">
            <Zap className="w-3 h-3 text-pink-400" />
            AI Recovery Agent
          </span>
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-surface-card border border-border text-[11px] font-mono text-gray-300">
          <Server className="w-3.5 h-3.5 text-emerald-400" />
          <span>API Connected</span>
        </div>

        <button
          onClick={handleRefresh}
          disabled={isRefreshing}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-white/5 hover:bg-white/10 active:scale-95 border border-border rounded-xl text-xs font-semibold text-gray-200 transition-all cursor-pointer disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin text-indigo-400' : ''}`} />
          <span>Refresh Live Data</span>
        </button>
      </div>
    </header>
  );
};
