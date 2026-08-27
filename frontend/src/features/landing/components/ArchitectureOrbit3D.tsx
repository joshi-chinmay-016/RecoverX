import React from 'react';
import {
  Database,
  BrainCircuit,
  Bot,
  ShieldCheck,
  Zap,
  TrendingUp,
} from 'lucide-react';
import { TiltCard } from './TiltCard';

const PILLARS = [
  {
    phase: '01',
    name: 'Financial Core & Outbox',
    tagline: 'Deterministic Financial Truth',
    description: 'Cryptographic HMAC-SHA256 signature verification, strict idempotent deduplication, and transactional outbox for 100% resilient payment state transitions.',
    techBadges: ['HMAC-SHA256', 'Integer Math (Paise)', 'Outbox Engine'],
    icon: Database,
    glow: 'rgba(99, 102, 241, 0.25)',
    border: 'border-indigo-500/30',
  },
  {
    phase: '02',
    name: 'Revenue Intelligence',
    tagline: 'Merchant-Relative Scoring',
    description: 'Zero LLM in financial arithmetic. Pure deterministic rule classifiers evaluate failure codes, customer tiering, and opportunity scores from 0-100.',
    techBadges: ['Zero LLM in Math', 'Percentile Normalization', 'Rules-v1'],
    icon: BrainCircuit,
    glow: 'rgba(236, 72, 153, 0.25)',
    border: 'border-pink-500/30',
  },
  {
    phase: '03',
    name: 'Bounded AI Recovery Agent',
    tagline: 'Sandboxed Reasoning Engine',
    description: 'Autonomous reasoning over failure context using read-only diagnostic tools. Untrusted input sanitization and zero direct database mutation authority.',
    techBadges: ['Read-Only Tools', 'Prompt Delimiters', 'Structured RecoveryPlan'],
    icon: Bot,
    glow: 'rgba(56, 189, 248, 0.25)',
    border: 'border-sky-500/30',
  },
  {
    phase: '04',
    name: 'Deterministic PolicyEngine',
    tagline: 'Zero-Bypass Execution Gate',
    description: 'Strict deterministic guardrails validate every AI proposal against maximum retry limits, payment status eligibility, and merchant action whitelists.',
    techBadges: ['Policy-v1 Gate', 'Max 3 Retries', 'ALLOWED/BLOCKED'],
    icon: ShieldCheck,
    glow: 'rgba(16, 185, 129, 0.25)',
    border: 'border-emerald-500/30',
  },
  {
    phase: '05',
    name: 'Controlled Execution & Reconcile',
    tagline: 'Idempotent Multi-Provider Adapters',
    description: 'Smart retry dispatching with exponential backoff and safe transition to UNKNOWN state during timeouts, followed by active clearinghouse polling.',
    techBadges: ['Idempotency Keys', 'UNKNOWN Safe Parking', 'Active Polling'],
    icon: Zap,
    glow: 'rgba(245, 158, 11, 0.25)',
    border: 'border-amber-500/30',
  },
  {
    phase: '06',
    name: 'Adaptive Bayesian Calibration',
    tagline: 'Closed-Loop Online Updating',
    description: 'Conjugate Beta-Binomial statistical updating recalibrates strategy success likelihoods with bounded ±20% safety guardrails against model drift.',
    techBadges: ['Beta-Binomial Updates', '±20% Bounded Priors', 'Brier Score Eval'],
    icon: TrendingUp,
    glow: 'rgba(139, 92, 246, 0.25)',
    border: 'border-purple-500/30',
  },
];

export const ArchitectureOrbit3D: React.FC = () => {
  return (
    <div className="space-y-8">
      <div className="text-center max-w-2xl mx-auto">
        <span className="text-[10px] font-mono font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-pink-500/20 text-pink-300 border border-pink-500/30">
          6-Stage Closed-Loop Architecture
        </span>
        <h3 className="font-heading font-extrabold text-2xl sm:text-3xl text-white tracking-tight mt-2">
          Engineered for Mathematical Rigor & Absolute Safety
        </h3>
        <p className="text-xs sm:text-sm text-gray-400 mt-2">
          Every payment follows a strictly bounded path where AI reasons, deterministic code verifies, and closed-loop feedback continuously optimizes yield.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {PILLARS.map((pillar, idx) => {
          const Icon = pillar.icon;
          return (
            <TiltCard
              key={idx}
              maxRotation={12}
              depth={30}
              glowColor={pillar.glow}
              className={`rounded-2xl border ${pillar.border} bg-surface-card hover:bg-surface-solid transition-all p-6 h-full flex flex-col justify-between space-y-4`}
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="w-10 h-10 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center text-white">
                    <Icon className="w-5 h-5" />
                  </div>
                  <span className="text-xs font-mono font-bold text-gray-500">
                    STAGE {pillar.phase}
                  </span>
                </div>

                <div>
                  <h4 className="font-heading font-extrabold text-base text-white">
                    {pillar.name}
                  </h4>
                  <span className="text-xs font-mono text-indigo-300 block mt-0.5">
                    {pillar.tagline}
                  </span>
                </div>

                <p className="text-xs text-gray-300 leading-relaxed">
                  {pillar.description}
                </p>
              </div>

              <div className="pt-3 border-t border-border flex flex-wrap gap-1.5">
                {pillar.techBadges.map((badge, bIdx) => (
                  <span
                    key={bIdx}
                    className="text-[10px] font-mono px-2 py-0.5 rounded bg-white/5 text-gray-300 border border-white/5"
                  >
                    {badge}
                  </span>
                ))}
              </div>
            </TiltCard>
          );
        })}
      </div>
    </div>
  );
};
