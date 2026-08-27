import React from 'react';
import { NavLink, Link } from 'react-router-dom';
import {
  LayoutDashboard,
  BrainCircuit,
  TrendingUp,
  Bot,
  Zap,
  ShieldCheck,
  History,
  Shield,
  Sparkles,
  ExternalLink,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface NavItem {
  label: string;
  path: string;
  icon: React.ReactNode;
  badge?: string;
}

export const Sidebar: React.FC = () => {
  const navItems: NavItem[] = [
    {
      label: 'Overview',
      path: '/',
      icon: <LayoutDashboard className="w-4 h-4" />,
    },
    {
      label: 'Revenue Intelligence',
      path: '/intelligence',
      icon: <BrainCircuit className="w-4 h-4" />,
    },
    {
      label: 'Recovery Queue',
      path: '/opportunities',
      icon: <TrendingUp className="w-4 h-4" />,
    },
    {
      label: 'AI Recovery Agent',
      path: '/agent',
      icon: <Bot className="w-4 h-4" />,
      badge: 'Active Studio',
    },
    {
      label: 'Recovery Actions',
      path: '/actions',
      icon: <Zap className="w-4 h-4 text-pink-400" />,
      badge: 'Execution',
    },
    {
      label: 'Adaptive Learning',
      path: '/learning',
      icon: <Sparkles className="w-4 h-4 text-indigo-400" />,
      badge: 'Adaptive',
    },
    {
      label: 'Policies & Safety',
      path: '/policies',
      icon: <ShieldCheck className="w-4 h-4" />,
    },
    {
      label: 'Audit Trail',
      path: '/audit',
      icon: <History className="w-4 h-4" />,
    },
  ];

  return (
    <aside className="w-64 bg-surface-solid/90 backdrop-blur-xl border-r border-border flex flex-col justify-between shrink-0 h-screen sticky top-0">
      <div>
        {/* Brand */}
        <div className="p-6 border-b border-border flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-500 to-pink-500 flex items-center justify-center text-white font-bold text-xl shadow-lg shadow-indigo-500/25">
            ⚡
          </div>
          <div>
            <h1 className="font-heading font-extrabold text-xl text-white tracking-tight flex items-center gap-0.5">
              Recover<span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-pink-400">X</span>
            </h1>
            <span className="text-[10px] uppercase tracking-wider font-semibold text-gray-400">
              Revenue Recovery
            </span>
          </div>
        </div>

        {/* Navigation Links */}
        <nav className="p-4 space-y-1.5">
          <div className="px-3 py-2 text-[10px] font-mono uppercase tracking-wider text-gray-500 font-semibold">
            Platform
          </div>
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                cn(
                  'flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all group',
                  isActive
                    ? 'bg-indigo-600/20 text-white border border-indigo-500/40 shadow-sm shadow-indigo-500/10'
                    : 'text-gray-400 hover:text-gray-200 hover:bg-white/5'
                )
              }
            >
              <div className="flex items-center gap-3">
                <span className="group-hover:text-indigo-400 transition-colors">
                  {item.icon}
                </span>
                <span>{item.label}</span>
              </div>
              {item.badge && (
                <span className="text-[9px] font-mono font-bold px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                  {item.badge}
                </span>
              )}
            </NavLink>
          ))}
        </nav>
      </div>

      {/* Footer Navigation Area */}
      <div className="p-4 space-y-3">
        {/* 3D Showcase Link */}
        <Link
          to="/landing"
          className="flex items-center justify-between p-3 rounded-xl bg-gradient-to-r from-indigo-500/10 via-purple-500/10 to-pink-500/10 border border-indigo-500/30 hover:border-pink-500/50 text-xs font-semibold text-gray-200 transition-all group"
        >
          <div className="flex items-center gap-2">
            <Sparkles className="w-3.5 h-3.5 text-pink-400 group-hover:rotate-12 transition-transform" />
            <span>3D Product Tour</span>
          </div>
          <ExternalLink className="w-3 h-3 text-gray-400 group-hover:text-white" />
        </Link>

        {/* Safety Policy Status Card */}
        <div className="p-3.5 rounded-xl bg-surface-card border border-indigo-500/20 text-[11px] text-gray-300 flex items-start gap-2.5">
          <Shield className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold block text-indigo-300">Policy Guardrails Active</span>
            Controlled execution layer active.
          </div>
        </div>
      </div>
    </aside>
  );
};
