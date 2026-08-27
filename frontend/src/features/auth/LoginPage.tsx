import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from './AuthContext';
import { Lock, Mail, Shield, ArrowRight, AlertCircle, Eye, EyeOff, ShieldCheck, Zap, UserCheck } from 'lucide-react';

export const LoginPage: React.FC = () => {
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Redirect if already authenticated
  React.useEffect(() => {
    if (isAuthenticated) {
      const from = (location.state as any)?.from?.pathname || '/';
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, navigate, location]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setError('Please enter both email and password.');
      return;
    }

    setError(null);
    setIsSubmitting(true);
    try {
      await login(email, password);
      const from = (location.state as any)?.from?.pathname || '/';
      navigate(from, { replace: true });
    } catch (err: any) {
      setError(err?.message || 'Authentication failed. Please verify your credentials.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const setDemoCredentials = (demoEmail: string, demoPass: string) => {
    setEmail(demoEmail);
    setPassword(demoPass);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-[#0b0f19] flex flex-col justify-center py-12 sm:px-6 lg:px-8 relative overflow-hidden">
      {/* Ambient background glow effects */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-gradient-to-tr from-indigo-600/15 to-pink-600/15 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-10 right-10 w-80 h-80 bg-blue-600/10 rounded-full blur-3xl pointer-events-none" />

      <div className="sm:mx-auto sm:w-full sm:max-w-md relative z-10">
        {/* Brand Header */}
        <div className="flex justify-center mb-4">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-indigo-500 to-pink-500 flex items-center justify-center text-white font-bold text-2xl shadow-xl shadow-indigo-500/25 border border-white/20">
            ⚡
          </div>
        </div>
        <h2 className="text-center font-heading font-extrabold text-3xl text-white tracking-tight">
          Recover<span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-pink-400">X</span>
        </h2>
        <p className="mt-2 text-center text-xs text-gray-400">
          Multi-Tenant Adaptive AI Revenue Recovery Platform
        </p>

        {/* 3D Showcase Banner Link */}
        <div className="mt-4 flex justify-center">
          <button
            type="button"
            onClick={() => navigate('/landing')}
            className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-gradient-to-r from-indigo-500/20 to-pink-500/20 border border-indigo-500/40 text-xs font-semibold text-indigo-300 hover:text-white hover:border-pink-500/60 transition-all cursor-pointer shadow-sm"
          >
            <span>✨ View 3D Product Showcase & Live Simulator</span>
            <ArrowRight className="w-3.5 h-3.5 text-pink-400" />
          </button>
        </div>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md relative z-10 px-4">
        <div className="bg-[#111726]/90 backdrop-blur-xl border border-white/10 py-8 px-6 shadow-2xl rounded-2xl sm:px-10">
          {error && (
            <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/30 flex items-start gap-3 text-red-300 text-xs">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-red-400" />
              <span>{error}</span>
            </div>
          )}

          <form className="space-y-5" onSubmit={handleSubmit}>
            <div>
              <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-2">
                Work Email Address
              </label>
              <div className="relative rounded-xl shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-gray-400">
                  <Mail className="h-4 w-4" />
                </div>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="admin@recoverx.io"
                  required
                  className="block w-full pl-10 pr-3 py-2.5 bg-white/5 border border-white/10 rounded-xl text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-2">
                Password
              </label>
              <div className="relative rounded-xl shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-gray-400">
                  <Lock className="h-4 w-4" />
                </div>
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  required
                  className="block w-full pl-10 pr-10 py-2.5 bg-white/5 border border-white/10 rounded-xl text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-gray-400 hover:text-gray-200 transition-colors"
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full flex justify-center items-center gap-2 py-3 px-4 rounded-xl shadow-lg shadow-indigo-600/30 text-sm font-bold text-white bg-gradient-to-r from-indigo-600 to-pink-600 hover:from-indigo-500 hover:to-pink-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 transition-all cursor-pointer"
            >
              {isSubmitting ? (
                <span>Authenticating...</span>
              ) : (
                <>
                  <span>Sign In to Workspace</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {/* Quick-Fill Demo Accounts */}
          <div className="mt-8 pt-6 border-t border-white/10">
            <span className="block text-[11px] font-mono uppercase tracking-wider text-gray-400 font-semibold mb-3">
              Quick-Fill Demo Roles (RBAC Enabled)
            </span>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => setDemoCredentials('admin@recoverx.io', 'Admin@RecoverX2026!')}
                className="flex flex-col items-center justify-center p-2.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-xs font-semibold text-gray-200 transition-all cursor-pointer group"
              >
                <ShieldCheck className="w-4 h-4 text-emerald-400 mb-1 group-hover:scale-110 transition-transform" />
                <span>Admin</span>
                <span className="text-[9px] text-gray-500 font-mono">Full Access</span>
              </button>

              <button
                type="button"
                onClick={() => setDemoCredentials('operator@recoverx.io', 'Operator@RecoverX2026!')}
                className="flex flex-col items-center justify-center p-2.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-xs font-semibold text-gray-200 transition-all cursor-pointer group"
              >
                <Zap className="w-4 h-4 text-pink-400 mb-1 group-hover:scale-110 transition-transform" />
                <span>Operator</span>
                <span className="text-[9px] text-gray-500 font-mono">Execute Ops</span>
              </button>

              <button
                type="button"
                onClick={() => setDemoCredentials('analyst@recoverx.io', 'Analyst@RecoverX2026!')}
                className="flex flex-col items-center justify-center p-2.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-xs font-semibold text-gray-200 transition-all cursor-pointer group"
              >
                <UserCheck className="w-4 h-4 text-indigo-400 mb-1 group-hover:scale-110 transition-transform" />
                <span>Analyst</span>
                <span className="text-[9px] text-gray-500 font-mono">Read Only</span>
              </button>
            </div>
          </div>

          {/* Sandbox Demo & RBAC Disclaimer Card */}
          <div className="mt-6 p-4 rounded-xl bg-indigo-950/40 border border-indigo-500/20 text-xs text-gray-300 space-y-2">
            <div className="flex items-center gap-2 text-indigo-300 font-semibold">
              <Shield className="w-4 h-4 text-indigo-400 shrink-0" />
              <span>Sandbox Demo & Role-Based Access</span>
            </div>
            <p className="text-[11px] leading-relaxed text-gray-400">
              <strong className="text-gray-200">Why all roles are accessible here:</strong> We have made all three demo accounts (Admin, Operator, and Analyst) openly available so you can explore how different team members see and interact with RecoverX.
            </p>
            <p className="text-[11px] leading-relaxed text-gray-400">
              <strong className="text-gray-200">Test Data Only:</strong> This environment contains only simulated recovery test data with zero risk to production financial systems.
            </p>
            <p className="text-[11px] leading-relaxed text-gray-400">
              <strong className="text-gray-200">Production Ready:</strong> In production deployments with live payment gateways, access is strictly locked down using hardened SSO and multi-tenant RBAC permissions.
            </p>
          </div>
        </div>

        {/* Security badge footer */}
        <div className="mt-6 flex items-center justify-center gap-2 text-[11px] text-gray-500">
          <Shield className="w-3.5 h-3.5 text-indigo-400" />
          <span>Tenant Isolated &bull; Argon2/Bcrypt Identity &bull; Server-Side Policy Guardrails</span>
        </div>
      </div>
    </div>
  );
};
