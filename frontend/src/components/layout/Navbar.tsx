import React, { useState, useRef, useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useAuth } from '@/features/auth/AuthContext';
import {
  RefreshCw,
  Zap,
  Building2,
  ChevronDown,
  LogOut,
  User,
  ShieldCheck,
  Check,
} from 'lucide-react';

export const Navbar: React.FC = () => {
  const queryClient = useQueryClient();
  const { user, activeMerchant, availableMerchants, role, switchMerchant, logout } = useAuth();
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isMerchantOpen, setIsMerchantOpen] = useState(false);
  const [isUserOpen, setIsUserOpen] = useState(false);

  const merchantRef = useRef<HTMLDivElement>(null);
  const userRef = useRef<HTMLDivElement>(null);

  // Close dropdowns on click outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (merchantRef.current && !merchantRef.current.contains(event.target as Node)) {
        setIsMerchantOpen(false);
      }
      if (userRef.current && !userRef.current.contains(event.target as Node)) {
        setIsUserOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await queryClient.invalidateQueries();
    setTimeout(() => setIsRefreshing(false), 500);
  };

  const getRoleBadge = () => {
    switch (role) {
      case 'ADMIN':
        return (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 flex items-center gap-1">
            <ShieldCheck className="w-3 h-3 text-emerald-400" /> ADMIN
          </span>
        );
      case 'OPERATOR':
        return (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-pink-500/20 text-pink-300 border border-pink-500/30 flex items-center gap-1">
            <Zap className="w-3 h-3 text-pink-400" /> OPERATOR
          </span>
        );
      case 'ANALYST':
      default:
        return (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 flex items-center gap-1">
            <User className="w-3 h-3 text-indigo-400" /> ANALYST
          </span>
        );
    }
  };

  return (
    <header className="h-16 border-b border-border bg-surface-solid/50 backdrop-blur-md px-6 sm:px-8 flex items-center justify-between sticky top-0 z-40">
      {/* Left: Tenant Switcher & Pipeline Indicators */}
      <div className="flex items-center gap-4">
        {/* Merchant Tenant Switcher Dropdown */}
        <div className="relative" ref={merchantRef}>
          <button
            onClick={() => setIsMerchantOpen(!isMerchantOpen)}
            className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-surface-card hover:bg-white/10 border border-border text-xs font-semibold text-white transition-all cursor-pointer shadow-sm"
          >
            <Building2 className="w-4 h-4 text-indigo-400" />
            <span className="max-w-[140px] truncate">{activeMerchant?.merchant_name || 'Select Merchant'}</span>
            <ChevronDown className={`w-3.5 h-3.5 text-gray-400 transition-transform ${isMerchantOpen ? 'rotate-180' : ''}`} />
          </button>

          {isMerchantOpen && (
            <div className="absolute left-0 mt-2 w-64 rounded-2xl bg-[#111726] border border-white/10 shadow-2xl py-2 z-50 animate-fade-in">
              <div className="px-4 py-2 border-b border-white/10 text-[10px] font-mono uppercase tracking-wider text-gray-400 font-semibold">
                Select Active Tenant
              </div>
              <div className="max-h-60 overflow-y-auto py-1">
                {availableMerchants.map((m) => {
                  const isCurrent = m.merchant_id === activeMerchant?.merchant_id;
                  return (
                    <button
                      key={m.merchant_id}
                      onClick={() => {
                        switchMerchant(m.merchant_id);
                        setIsMerchantOpen(false);
                      }}
                      className={`w-full flex items-center justify-between px-4 py-2 text-xs text-left transition-colors cursor-pointer ${
                        isCurrent
                          ? 'bg-indigo-600/20 text-white font-semibold'
                          : 'text-gray-300 hover:bg-white/5 hover:text-white'
                      }`}
                    >
                      <div className="flex flex-col">
                        <span className="truncate">{m.merchant_name}</span>
                        <span className="text-[10px] text-gray-500 font-mono">{m.currency} &bull; Role: {m.role}</span>
                      </div>
                      {isCurrent && <Check className="w-4 h-4 text-indigo-400 shrink-0" />}
                    </button>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* Pipeline Indicators */}
        <div className="hidden lg:flex items-center gap-2 bg-white/5 px-3 py-1.5 rounded-full border border-border text-xs">
          <span className="flex items-center gap-1.5 font-semibold text-emerald-300">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            Financial Core
          </span>
          <span className="text-gray-600">&rarr;</span>
          <span className="font-semibold text-indigo-300">
            Revenue Intelligence
          </span>
          <span className="text-gray-600">&rarr;</span>
          <span className="font-semibold text-pink-300 flex items-center gap-1">
            <Zap className="w-3 h-3 text-pink-400" />
            AI Recovery Agent
          </span>
        </div>
      </div>

      {/* Right: Actions & User Profile */}
      <div className="flex items-center gap-3">
        <button
          onClick={handleRefresh}
          disabled={isRefreshing}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-white/5 hover:bg-white/10 active:scale-95 border border-border rounded-xl text-xs font-semibold text-gray-200 transition-all cursor-pointer disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin text-indigo-400' : ''}`} />
          <span className="hidden sm:inline">Refresh Data</span>
        </button>

        {/* User Profile & Role Dropdown */}
        <div className="relative" ref={userRef}>
          <button
            onClick={() => setIsUserOpen(!isUserOpen)}
            className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-surface-card hover:bg-white/10 border border-border text-xs font-semibold text-white transition-all cursor-pointer shadow-sm"
          >
            <div className="w-6 h-6 rounded-lg bg-gradient-to-tr from-indigo-500 to-pink-500 flex items-center justify-center text-white font-bold text-xs">
              {user?.full_name?.charAt(0) || 'U'}
            </div>
            <span className="hidden sm:inline max-w-[120px] truncate">{user?.full_name || 'User'}</span>
            {getRoleBadge()}
            <ChevronDown className={`w-3.5 h-3.5 text-gray-400 transition-transform ${isUserOpen ? 'rotate-180' : ''}`} />
          </button>

          {isUserOpen && (
            <div className="absolute right-0 mt-2 w-64 rounded-2xl bg-[#111726] border border-white/10 shadow-2xl py-2 z-50 animate-fade-in">
              <div className="px-4 py-3 border-b border-white/10">
                <div className="font-semibold text-sm text-white truncate">{user?.full_name}</div>
                <div className="text-xs text-gray-400 truncate font-mono">{user?.email}</div>
                <div className="mt-2 flex items-center gap-2">
                  <span className="text-[10px] text-gray-400 font-mono">Role:</span>
                  {getRoleBadge()}
                </div>
              </div>

              <div className="p-2">
                <button
                  onClick={() => {
                    setIsUserOpen(false);
                    logout();
                  }}
                  className="w-full flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-semibold text-red-400 hover:bg-red-500/10 transition-colors cursor-pointer"
                >
                  <LogOut className="w-4 h-4 text-red-400" />
                  <span>Log Out</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
