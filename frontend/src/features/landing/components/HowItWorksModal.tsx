import React, { useState } from 'react';
import {
  X,
  Database,
  BrainCircuit,
  Bot,
  ShieldCheck,
  Zap,
  TrendingUp,
  CheckCircle2,
  Terminal,
} from 'lucide-react';

interface HowItWorksModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const HowItWorksModal: React.FC<HowItWorksModalProps> = ({ isOpen, onClose }) => {
  const [activeStep, setActiveStep] = useState<number>(0);

  if (!isOpen) return null;

  const steps = [
    {
      step: '01',
      title: 'Cryptographic Ingestion & Financial Core',
      tagline: 'Deterministic Financial Truth & Zero Floating-Point Drift',
      icon: Database,
      badge: 'HMAC-SHA256 Verified',
      color: 'indigo',
      summary:
        'When a payment drops at the gateway (Razorpay, Stripe, Adyen), RecoverX immediately intercepts the webhook before customer drop-off.',
      details: [
        {
          heading: 'Constant-Time HMAC-SHA256 Verification',
          desc: 'Calculates SHA256 digest against the raw byte payload using hmac.compare_digest to eliminate timing attacks.',
        },
        {
          heading: 'Strict Idempotency & Deduplication',
          desc: 'Locks on x-razorpay-event-id with database-level uniqueness constraints, ensuring out-of-order webhooks never duplicate financial state.',
        },
        {
          heading: 'Normalized Integer Arithmetic',
          desc: 'All values stored in minor units (Paise / Cents) eliminating IEEE 754 floating-point precision loss across high-volume ledgers.',
        },
      ],
      codeSnippet: `// Webhook Verifier (HMAC-SHA256)
expected_sig = hmac.new(webhook_secret, raw_bytes, sha256).hexdigest()
is_valid = hmac.compare_digest(expected_sig, signature_header)
if not is_valid:
    raise HTTPException(status_code=401, detail="Invalid signature")`,
      metrics: {
        latency: '~ 4.5ms',
        safety: '100% Constant-Time',
        guarantee: 'Zero Duplicate Entries',
      },
    },
    {
      step: '02',
      title: 'Deterministic Failure Intelligence',
      tagline: 'Merchant-Relative Scoring With Zero LLM In Math',
      icon: BrainCircuit,
      badge: 'Pure Python/SQL (< 1.3ms)',
      color: 'pink',
      summary:
        'Analyzes the failure taxonomy without calling non-deterministic LLMs for financial arithmetic, classifying root cause and recovery probability.',
      details: [
        {
          heading: 'Failure Code Classification',
          desc: 'Classifies root cause into BANK_FAILURE, NETWORK_TIMEOUT, INSUFFICIENT_FUNDS, or AUTHENTICATION_ERROR in < 0.2ms.',
        },
        {
          heading: 'Merchant-Relative Percentile Normalization',
          desc: 'Evaluates transaction value relative to the specific merchant historical volume distribution (e.g. ₹5,000 is top 5% for food delivery, but median for B2B SaaS).',
        },
        {
          heading: 'Bounded 0-100 Opportunity Score',
          desc: 'Combines recovery likelihood (40%), relative value (40%), value percentile (10%), and retry history penalty (±15%).',
        },
      ],
      codeSnippet: `# Deterministic Scoring Engine
score = (
    0.40 * (likelihood * 100) +
    0.40 * (normalized_value * 100) +
    0.10 * (percentile * 100) -
    (retry_penalty * 15)
)
opportunity_score = max(0.0, min(100.0, score))`,
      metrics: {
        latency: '~ 1.3ms',
        safety: '0% Math Hallucination',
        guarantee: 'Deterministic & Auditable',
      },
    },
    {
      step: '03',
      title: 'Bounded AI Recovery Agent',
      tagline: 'Autonomous Reasoning With Read-Only Sandboxed Tools',
      icon: Bot,
      badge: 'Sandboxed LLM Reasoning',
      color: 'sky',
      summary:
        'Deploys Google Gemini / Groq to analyze failure evidence and synthesize an optimal recovery plan with zero database mutation privileges.',
      details: [
        {
          heading: 'Read-Only Diagnostic Tool Registry',
          desc: 'Agent is granted access solely to read-only inspection tools (get_payment_context, get_recovery_history). Prohibited from running direct SQL writes or HTTP mutations.',
        },
        {
          heading: 'Prompt Injection Defense & Quarantining',
          desc: 'All untrusted user metadata and gateway error strings are quarantined inside strict XML boundaries (<UNTRUSTED_DATA>) preventing instruction override.',
        },
        {
          heading: 'Structured RecoveryPlan Schema',
          desc: 'Agent synthesizes a declarative, typed schema specifying the recommended strategy, backoff delay, and clinical rationale.',
        },
      ],
      codeSnippet: `// Synthesized RecoveryPlan Output
{
  "selected_strategy": "SMART_RETRY",
  "backoff_seconds": 120,
  "confidence": 0.88,
  "rationale": "Transient bank 503 error; retry via secondary clearing route",
  "requires_approval": false
}`,
      metrics: {
        latency: 'Background Worker',
        safety: '0 DB Mutation Authority',
        guarantee: 'Typed Schema Output',
      },
    },
    {
      step: '04',
      title: 'Deterministic PolicyEngine Gate',
      tagline: 'Zero-Bypass Deterministic Execution Authority',
      icon: ShieldCheck,
      badge: 'Zero-Bypass Intercept',
      color: 'emerald',
      summary:
        'The AI proposes, but the PolicyEngine decides. Enforces hard operational constraints before any external call is permitted.',
      details: [
        {
          heading: 'Maximum Retry Limit Enforcement',
          desc: 'Hard-blocks any retry request if attempt count >= 3, protecting merchants from duplicate provider fee burning.',
        },
        {
          heading: 'Action Whitelist Verification',
          desc: 'Ensures proposed action belongs to the strict registered enum set (RETRY_PAYMENT, SEND_REMINDER, MANUAL_REVIEW, etc.).',
        },
        {
          heading: 'State Machine Eligibility',
          desc: 'Verifies the payment and recovery case remain in FAILED and OPEN state before permitting authorization.',
        },
      ],
      codeSnippet: `# PolicyEngine Gate Checks
if action.type == ActionType.RETRY_PAYMENT and payment.attempts >= 3:
    return PolicyDecision(status=PolicyStatus.BLOCKED, reason="Max retry limit exceeded")
if action.type not in MERCHANT_ALLOWED_ACTIONS:
    return PolicyDecision(status=PolicyStatus.BLOCKED, reason="Action not whitelisted")
return PolicyDecision(status=PolicyStatus.ALLOWED)`,
      metrics: {
        latency: '~ 0.4ms',
        safety: '100% Policy Block Rate',
        guarantee: 'Zero LLM Bypass',
      },
    },
    {
      step: '05',
      title: 'Controlled Execution & Reconciliation',
      tagline: 'Idempotent Multi-Provider Retries & Timeout Safety',
      icon: Zap,
      badge: 'Double-Debit Safe',
      color: 'amber',
      summary:
        'Executes authorized actions via resilient provider adapters with smart exponential backoff and safe timeout parking.',
      details: [
        {
          heading: 'Atomic Idempotency Key Generation',
          desc: 'Every execution attempt generates hash(payment_id, action_type, attempt_number) preventing duplicate charges under concurrency.',
        },
        {
          heading: 'UNKNOWN State Timeout Parking',
          desc: 'If a payment gateway times out or hangs, the action transitions to UNKNOWN rather than re-attempting, preventing double debiting.',
        },
        {
          heading: 'Active Polling Reconciliation',
          desc: 'Background reconciliation worker queries clearinghouse status endpoints to verify final state and reconcile the financial ledger.',
        },
      ],
      codeSnippet: `// Execution & Timeout Safety
try:
    result = await provider_adapter.execute_retry(idempotency_key)
except ProviderTimeoutException:
    action.status = ActionStatus.UNKNOWN
    # Park in UNKNOWN and queue for active ledger reconciliation`,
      metrics: {
        latency: '~ 80ms - 250ms',
        safety: 'Idempotent Locked',
        guarantee: 'Zero Double Charges',
      },
    },
    {
      step: '06',
      title: 'Closed-Loop Bayesian Calibration',
      tagline: 'Continuous Online Feedback & Drift-Bounded Priors',
      icon: TrendingUp,
      badge: '±20% Bounded Calibration',
      color: 'purple',
      summary:
        'Every outcome automatically recalibrates strategy success distributions, making future recovery recommendations smarter over time.',
      details: [
        {
          heading: 'Conjugate Beta-Binomial Updating',
          desc: 'Closed-loop feedback automatically updates posterior recovery likelihoods based on empirical payment capture events.',
        },
        {
          heading: '±20% Bounded Priors Guardrail',
          desc: 'Mathematically clamps posterior probability estimates within ±20% of baseline domain priors, eliminating statistical manipulation or outlier drift.',
        },
        {
          heading: 'Immutable Audit Trail',
          desc: 'Every state transition, webhook receipt, agent decision, and policy decision is permanently recorded in hash-linked audit records.',
        },
      ],
      codeSnippet: `# Conjugate Bayesian Beta-Binomial Update
alpha_post = alpha_prior + successes
beta_post = beta_prior + failures
posterior_mean = alpha_post / (alpha_post + beta_post)

# Safety Clamp Guardrail
calibrated_prob = clamp(posterior_mean, prior * 0.8, prior * 1.2)`,
      metrics: {
        latency: 'Continuous Online',
        safety: '±20% Anti-Drift Clamp',
        guarantee: 'Immutable Hash Trail',
      },
    },
  ];

  const currentStep = steps[activeStep];
  const StepIcon = currentStep.icon;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-black/85 backdrop-blur-xl animate-fade-in">
      <div
        className="relative w-full max-w-5xl rounded-3xl bg-[#0B0F19] border border-indigo-500/30 p-6 sm:p-8 shadow-2xl shadow-indigo-500/20 max-h-[92vh] overflow-y-auto space-y-6"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Top Header */}
        <div className="flex items-start justify-between border-b border-border pb-5">
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 rounded-2xl bg-gradient-to-tr from-indigo-500 to-pink-500 flex items-center justify-center text-white font-extrabold text-xl shadow-lg shadow-indigo-500/25 border border-white/20">
              ⚡
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="font-heading font-black text-xl sm:text-2xl text-white tracking-tight">
                  How RecoverX Works
                </h2>
                <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                  Closed-Loop System Architecture
                </span>
              </div>
              <p className="text-xs text-gray-400 mt-0.5">
                The engineering blueprint behind autonomous payment recovery, deterministic policy gates, and online Bayesian learning.
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="p-2.5 rounded-xl bg-surface-card hover:bg-white/10 text-gray-400 hover:text-white transition-colors cursor-pointer border border-border"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Step Navigation Bar (Pills 1 to 6) */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
          {steps.map((s, idx) => {
            const isSelected = activeStep === idx;
            const Icon = s.icon;
            return (
              <button
                key={idx}
                type="button"
                onClick={() => setActiveStep(idx)}
                className={`p-3 rounded-2xl border text-left transition-all cursor-pointer flex flex-col justify-between space-y-2 ${
                  isSelected
                    ? 'bg-gradient-to-br from-indigo-600/30 via-surface-card to-pink-600/20 border-indigo-500 shadow-lg shadow-indigo-500/20 scale-[1.02]'
                    : 'bg-surface-card hover:bg-surface-hover border-border text-gray-400 hover:text-gray-200'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className={`text-[11px] font-mono font-bold ${isSelected ? 'text-indigo-300' : 'text-gray-500'}`}>
                    STEP {s.step}
                  </span>
                  <Icon className={`w-3.5 h-3.5 ${isSelected ? 'text-pink-400' : 'text-gray-500'}`} />
                </div>
                <div className="font-heading font-bold text-xs text-white truncate">
                  {s.title.split('&')[0].trim()}
                </div>
              </button>
            );
          })}
        </div>

        {/* Main Step Detail Stage */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left Col: Step Breakdown & Architecture Details (7 cols) */}
          <div className="lg:col-span-7 space-y-5">
            <div className="p-6 rounded-3xl bg-surface-card border border-border space-y-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 flex items-center justify-center">
                  <StepIcon className="w-5 h-5" />
                </div>
                <div>
                  <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-pink-400">
                    Phase {currentStep.step} Engine
                  </span>
                  <h3 className="font-heading font-black text-lg sm:text-xl text-white">
                    {currentStep.title}
                  </h3>
                  <span className="text-xs font-mono text-indigo-300 font-semibold block">
                    {currentStep.tagline}
                  </span>
                </div>
              </div>

              <p className="text-xs text-gray-300 leading-relaxed pt-2 border-t border-border">
                {currentStep.summary}
              </p>

              <div className="space-y-3 pt-2">
                {currentStep.details.map((item, dIdx) => (
                  <div key={dIdx} className="p-3.5 rounded-2xl bg-surface-solid border border-border/80 space-y-1">
                    <div className="flex items-center gap-2 text-xs font-heading font-bold text-white">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                      <span>{item.heading}</span>
                    </div>
                    <p className="text-xs text-gray-400 pl-5 leading-relaxed">
                      {item.desc}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Right Col: Technical Code Snippet & Live Guarantees (5 cols) */}
          <div className="lg:col-span-5 space-y-5">
            {/* Live Metrics Box */}
            <div className="grid grid-cols-3 gap-2 text-center">
              <div className="p-3 rounded-2xl bg-surface-card border border-border">
                <span className="text-[10px] font-mono text-gray-500 block">Latency</span>
                <span className="font-mono text-xs font-bold text-emerald-400">
                  {currentStep.metrics.latency}
                </span>
              </div>
              <div className="p-3 rounded-2xl bg-surface-card border border-border">
                <span className="text-[10px] font-mono text-gray-500 block">Safety Mode</span>
                <span className="font-mono text-xs font-bold text-pink-400">
                  {currentStep.metrics.safety}
                </span>
              </div>
              <div className="p-3 rounded-2xl bg-surface-card border border-border">
                <span className="text-[10px] font-mono text-gray-500 block">Guarantee</span>
                <span className="font-mono text-[11px] font-bold text-indigo-300 truncate block">
                  {currentStep.metrics.guarantee}
                </span>
              </div>
            </div>

            {/* Interactive Code / Architecture Terminal */}
            <div className="rounded-3xl bg-black/80 border border-white/10 overflow-hidden shadow-xl">
              <div className="px-4 py-2.5 bg-white/5 border-b border-white/10 flex items-center justify-between text-xs text-gray-400 font-mono">
                <div className="flex items-center gap-2">
                  <Terminal className="w-3.5 h-3.5 text-pink-400" />
                  <span>source_implementation.py</span>
                </div>
                <span className="text-[10px] text-gray-500">Python 3.12</span>
              </div>
              <pre className="p-4 text-xs font-mono text-gray-300 overflow-x-auto leading-relaxed bg-[#050811]">
                <code>{currentStep.codeSnippet}</code>
              </pre>
            </div>

            {/* Step Navigation CTAs */}
            <div className="flex items-center justify-between pt-2">
              <button
                type="button"
                disabled={activeStep === 0}
                onClick={() => setActiveStep((prev) => Math.max(0, prev - 1))}
                className="px-4 py-2 rounded-xl bg-surface-card hover:bg-surface-hover border border-border text-xs font-semibold text-gray-300 disabled:opacity-30 disabled:cursor-not-allowed cursor-pointer transition-all"
              >
                ← Previous Step
              </button>

              <button
                type="button"
                onClick={() => {
                  if (activeStep < steps.length - 1) {
                    setActiveStep((prev) => prev + 1);
                  } else {
                    onClose();
                  }
                }}
                className="px-5 py-2 rounded-xl bg-gradient-to-r from-indigo-600 to-pink-600 hover:from-indigo-500 hover:to-pink-500 text-xs font-bold text-white transition-all shadow-md flex items-center gap-1.5 cursor-pointer"
              >
                <span>{activeStep === steps.length - 1 ? 'Explore Sandbox' : 'Next Step →'}</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
