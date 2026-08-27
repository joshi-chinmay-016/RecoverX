import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  Zap,
  Bot,
  XCircle,
  Sparkles,
  Play,
  RotateCcw,
  Cpu,
  Lock,
  Database,
  TrendingUp,
} from 'lucide-react';
import { TiltCard } from './TiltCard';

interface ScenarioDef {
  id: string;
  name: string;
  category: string;
  amount: string;
  description: string;
  stages: {
    title: string;
    status: 'success' | 'blocked' | 'warning' | 'active';
    metric: string;
    details: string;
    icon: any;
  }[];
  finalStatus: 'CAPTURED' | 'POLICY BLOCKED' | 'RECONCILED' | 'TENANT ISOLATED';
  yieldLift: string;
  badgeColor: string;
}

const SCENARIOS: ScenarioDef[] = [
  {
    id: 'scenario_a',
    name: 'Scenario A: High-Yield Bank Outage',
    category: 'BANK_FAILURE (Razorpay 503)',
    amount: '₹2,450',
    description: 'Transient UPI/Netbanking gateway timeout during flash sale peak. Zero prior retries.',
    stages: [
      {
        title: '1. Webhook Ingest',
        status: 'success',
        metric: 'HMAC Valid (0.8ms)',
        details: 'SHA256 signature verified against raw bytes payload.',
        icon: Database,
      },
      {
        title: '2. Failure Intelligence',
        status: 'success',
        metric: 'Score: 85/100 (Critical)',
        details: 'Merchant-relative opportunity score evaluated. Recovery probability: 85%.',
        icon: Cpu,
      },
      {
        title: '3. AI Recovery Agent',
        status: 'success',
        metric: 'RecoveryPlan Synthesized',
        details: 'Gemini reasoning selects SMART_RETRY with 120s exponential backoff.',
        icon: Bot,
      },
      {
        title: '4. PolicyEngine Gate',
        status: 'success',
        metric: 'ALLOWED (Policy-v1)',
        details: 'Retry count 0 < 3 max limit. Action whitelisted.',
        icon: ShieldCheck,
      },
      {
        title: '5. Smart Execution',
        status: 'success',
        metric: 'Status: CAPTURED',
        details: 'Idempotent retry executed at secondary provider route. ₹2,450 settled.',
        icon: Zap,
      },
      {
        title: '6. Closed-Loop Feedback',
        status: 'success',
        metric: 'Bayesian Prior +0.4%',
        details: 'Learning outcome logged. Beta-Binomial posterior yield updated.',
        icon: TrendingUp,
      },
    ],
    finalStatus: 'CAPTURED',
    yieldLift: '+85% Yield',
    badgeColor: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30',
  },
  {
    id: 'scenario_b',
    name: 'Scenario B: Policy-Blocked High Risk',
    category: 'INSUFFICIENT_FUNDS (Retries Exceeded)',
    amount: '₹8,900',
    description: 'Card balance exhausted with 3 existing failed attempts. High chargeback risk.',
    stages: [
      {
        title: '1. Webhook Ingest',
        status: 'success',
        metric: 'HMAC Valid (1.1ms)',
        details: 'Normalized payment record created. 3 attempts indexed.',
        icon: Database,
      },
      {
        title: '2. Failure Intelligence',
        status: 'warning',
        metric: 'Score: 32/100 (Low)',
        details: 'Hard failure classified. Low organic recovery probability.',
        icon: Cpu,
      },
      {
        title: '3. AI Recovery Agent',
        status: 'warning',
        metric: 'Proposes RETRY_PAYMENT',
        details: 'Agent attempts aggressive retry strategy.',
        icon: Bot,
      },
      {
        title: '4. PolicyEngine Gate',
        status: 'blocked',
        metric: 'BLOCKED: Max Retries (3)',
        details: 'Deterministic safety intercept. Zero bypass allowed.',
        icon: Lock,
      },
      {
        title: '5. Safe Fallback',
        status: 'blocked',
        metric: 'Routed to SMS Reminder',
        details: 'Prevented duplicate processing fees. Alternate link dispatched.',
        icon: Zap,
      },
      {
        title: '6. Closed-Loop Feedback',
        status: 'success',
        metric: 'Fee Loss Avoided: ₹45',
        details: 'Policy enforcement verified and recorded in immutable audit ledger.',
        icon: TrendingUp,
      },
    ],
    finalStatus: 'POLICY BLOCKED',
    yieldLift: 'Loss Prevented',
    badgeColor: 'text-rose-400 bg-rose-500/10 border-rose-500/30',
  },
  {
    id: 'scenario_c',
    name: 'Scenario C: Timeout UNKNOWN Auto-Reconcile',
    category: 'GATEWAY_TIMEOUT (Network Drop)',
    amount: '₹4,200',
    description: 'Bank processing socket hung mid-transaction. State parked in UNKNOWN to prevent double charges.',
    stages: [
      {
        title: '1. Webhook Ingest',
        status: 'success',
        metric: 'Idempotency Lock Held',
        details: 'Unique constraint on payment_id + idempotency_key.',
        icon: Database,
      },
      {
        title: '2. Failure Intelligence',
        status: 'success',
        metric: 'Score: 78/100 (High)',
        details: 'Network socket dropped prior to bank acknowledgement.',
        icon: Cpu,
      },
      {
        title: '3. AI Recovery Agent',
        status: 'success',
        metric: 'Plan: RECONCILE_STATUS',
        details: 'Agent recommends active provider ledger query.',
        icon: Bot,
      },
      {
        title: '4. PolicyEngine Gate',
        status: 'success',
        metric: 'ALLOWED (Reconcile Mode)',
        details: 'Safe read-only state check permitted.',
        icon: ShieldCheck,
      },
      {
        title: '5. Reconcile Worker',
        status: 'active',
        metric: 'UNKNOWN -> SUCCEEDED',
        details: 'Provider verification query resolved payment as captured at clearing house.',
        icon: Zap,
      },
      {
        title: '6. Closed-Loop Feedback',
        status: 'success',
        metric: 'Revenue Restored: ₹4,200',
        details: 'Reconciliation verified in audit log without duplicate debit.',
        icon: TrendingUp,
      },
    ],
    finalStatus: 'RECONCILED',
    yieldLift: 'Zero Double Debit',
    badgeColor: 'text-amber-400 bg-amber-500/10 border-amber-500/30',
  },
  {
    id: 'scenario_d',
    name: 'Scenario D: Multi-Tenant Tenant Isolation',
    category: 'CROSS_TENANT_SECURITY (IDOR Guard)',
    amount: '₹15,000',
    description: 'Secondary merchant payment requested by unauthorized context. Rejected at boundary.',
    stages: [
      {
        title: '1. JWT Validation',
        status: 'success',
        metric: 'Tenant Context Extracted',
        details: 'Merchant A token decoded. Tenant ID verified.',
        icon: Lock,
      },
      {
        title: '2. Boundary Check',
        status: 'blocked',
        metric: 'Merchant Mismatch',
        details: 'Target payment belongs to Acme Global Payments (Merchant B).',
        icon: ShieldCheck,
      },
      {
        title: '3. Security Intercept',
        status: 'blocked',
        metric: 'HTTP 404 Returned',
        details: 'Anti-enumeration response. Zero cross-tenant data leak.',
        icon: Lock,
      },
      {
        title: '4. Policy Gate',
        status: 'blocked',
        metric: 'EXECUTION DENIED',
        details: 'Database queries scoped strictly to authenticated tenant_id.',
        icon: XCircle,
      },
      {
        title: '5. Action Engine',
        status: 'blocked',
        metric: 'NO-OP State Maintained',
        details: 'Zero database writes or external provider dispatches.',
        icon: Zap,
      },
      {
        title: '6. Security Audit',
        status: 'success',
        metric: 'Audit Security Logged',
        details: 'Security event registered in immutable hash-linked trail.',
        icon: Database,
      },
    ],
    finalStatus: 'TENANT ISOLATED',
    yieldLift: '100% Data Isolation',
    badgeColor: 'text-indigo-400 bg-indigo-500/10 border-indigo-500/30',
  },
];

export const LivePipeline3D: React.FC = () => {
  const [selectedScenarioId, setSelectedScenarioId] = useState<string>('scenario_a');
  const [activeStageIndex, setActiveStageIndex] = useState<number>(5);
  const [isSimulating, setIsSimulating] = useState<boolean>(false);

  const scenario = SCENARIOS.find((s) => s.id === selectedScenarioId) || SCENARIOS[0];

  const handleTriggerScenario = (scId: string) => {
    setSelectedScenarioId(scId);
    setIsSimulating(true);
    setActiveStageIndex(0);
  };

  useEffect(() => {
    if (!isSimulating) return;

    const interval = setInterval(() => {
      setActiveStageIndex((prev) => {
        if (prev < 5) {
          return prev + 1;
        } else {
          setIsSimulating(false);
          return 5;
        }
      });
    }, 450);

    return () => clearInterval(interval);
  }, [isSimulating]);

  return (
    <div className="space-y-8">
      {/* Interactive Scenario Buttons */}
      <div className="flex flex-wrap items-center justify-center gap-3">
        {SCENARIOS.map((sc) => {
          const isSelected = sc.id === selectedScenarioId;
          return (
            <button
              key={sc.id}
              onClick={() => handleTriggerScenario(sc.id)}
              className={`px-4 py-2.5 rounded-xl font-heading font-bold text-xs transition-all duration-200 flex items-center gap-2 border cursor-pointer ${
                isSelected
                  ? 'bg-gradient-to-r from-indigo-600 to-pink-600 text-white border-white/20 shadow-lg shadow-indigo-500/25 scale-105'
                  : 'bg-surface-card hover:bg-surface-hover text-gray-300 border-border hover:border-indigo-500/40'
              }`}
            >
              <Play className={`w-3.5 h-3.5 ${isSelected ? 'fill-white text-white' : 'text-indigo-400'}`} />
              <span>{sc.name.split(':')[0]}</span>
              <span className="text-[10px] font-mono opacity-80 bg-black/20 px-1.5 py-0.5 rounded">
                {sc.amount}
              </span>
            </button>
          );
        })}
      </div>

      {/* Scenario Overview Banner */}
      <div className="p-5 rounded-2xl bg-surface-card border border-border flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <span className={`text-[10px] font-mono font-bold uppercase px-2.5 py-0.5 rounded-full border ${scenario.badgeColor}`}>
              {scenario.finalStatus}
            </span>
            <span className="text-xs font-mono text-gray-400">{scenario.category}</span>
          </div>
          <h4 className="font-heading font-extrabold text-lg text-white">
            {scenario.name} • <span className="text-pink-400 font-mono">{scenario.amount}</span>
          </h4>
          <p className="text-xs text-gray-300 mt-1 max-w-2xl">
            {scenario.description}
          </p>
        </div>

        <button
          onClick={() => handleTriggerScenario(scenario.id)}
          className="px-4 py-2 rounded-xl bg-surface-solid border border-border hover:border-pink-500/40 text-xs font-semibold text-gray-200 flex items-center gap-2 transition-all self-start md:self-center cursor-pointer"
        >
          <RotateCcw className={`w-3.5 h-3.5 ${isSimulating ? 'animate-spin text-pink-400' : ''}`} />
          <span>Re-Simulate Pipeline</span>
        </button>
      </div>

      {/* 3D Visual Pipeline Flow Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {scenario.stages.map((stage, idx) => {
          const Icon = stage.icon;
          const isPassed = idx <= activeStageIndex;
          const isCurrent = idx === activeStageIndex && isSimulating;

          return (
            <TiltCard
              key={idx}
              maxRotation={10}
              depth={25}
              glowColor={
                stage.status === 'blocked'
                  ? 'rgba(239, 68, 68, 0.3)'
                  : stage.status === 'warning'
                  ? 'rgba(245, 158, 11, 0.3)'
                  : 'rgba(99, 102, 241, 0.3)'
              }
              className={`rounded-2xl border transition-all duration-300 ${
                isCurrent
                  ? 'ring-2 ring-pink-500 shadow-xl shadow-pink-500/20'
                  : ''
              } ${
                isPassed
                  ? 'bg-surface-card border-border'
                  : 'bg-surface-card/40 border-border/40 opacity-40'
              }`}
            >
              <div className="p-5 h-full flex flex-col justify-between space-y-4">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2.5">
                    <div
                      className={`w-9 h-9 rounded-xl flex items-center justify-center border ${
                        stage.status === 'blocked'
                          ? 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                          : stage.status === 'warning'
                          ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                          : 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30'
                      }`}
                    >
                      <Icon className="w-4 h-4" />
                    </div>
                    <div>
                      <h5 className="font-heading font-bold text-sm text-white">{stage.title}</h5>
                      <span className="text-[11px] font-mono text-gray-400">Phase 0{idx + 1}</span>
                    </div>
                  </div>

                  {isPassed && (
                    <span
                      className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded ${
                        stage.status === 'blocked'
                          ? 'bg-rose-500/20 text-rose-300'
                          : stage.status === 'warning'
                          ? 'bg-amber-500/20 text-amber-300'
                          : 'bg-emerald-500/20 text-emerald-300'
                      }`}
                    >
                      {stage.status === 'blocked' ? 'INTERCEPT' : stage.status === 'warning' ? 'CAUTION' : 'ACTIVE'}
                    </span>
                  )}
                </div>

                <div className="space-y-1.5">
                  <div className="font-mono text-xs font-semibold text-indigo-300 flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-pink-400 shrink-0" />
                    <span>{stage.metric}</span>
                  </div>
                  <p className="text-xs text-gray-300 leading-relaxed">
                    {stage.details}
                  </p>
                </div>

                <div className="pt-2 border-t border-border flex items-center justify-between text-[11px] font-mono text-gray-400">
                  <span>Deterministic Gate</span>
                  <span className="text-gray-200 font-bold">
                    {isPassed ? '✓ Verified' : 'Waiting...'}
                  </span>
                </div>
              </div>
            </TiltCard>
          );
        })}
      </div>
    </div>
  );
};
