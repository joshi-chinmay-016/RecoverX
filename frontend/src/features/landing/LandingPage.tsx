import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Zap,
  ArrowRight,
  TrendingUp,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Play,
  Clock,
  Github,
  HelpCircle,
  X,
  Cpu,
  ShieldCheck,
  Database,
  Sparkles,
} from 'lucide-react';
import { ParticleMeshBackground } from './components/ParticleMeshBackground';
import { TiltCard } from './components/TiltCard';
import { LivePipeline3D } from './components/LivePipeline3D';
import { RoiCalculator3D } from './components/RoiCalculator3D';
import { ArchitectureOrbit3D } from './components/ArchitectureOrbit3D';
import { HowItWorksModal } from './components/HowItWorksModal';

export const LandingPage: React.FC = () => {
  const [activeFaq, setActiveFaq] = useState<number | null>(0);
  const [showLatencyModal, setShowLatencyModal] = useState<boolean>(false);
  const [showHowItWorksModal, setShowHowItWorksModal] = useState<boolean>(false);

  const faqs = [
    {
      q: 'Why is the AI Agent prohibited from performing financial calculations?',
      a: 'LLMs are inherently non-deterministic. In RecoverX, all financial calculations, risk scoring, and percentage allocations are 100% deterministic code in Python/SQL using integer paises. The AI is utilized strictly as a reasoning component to synthesize structured recovery strategies over sanitized diagnostic context.',
    },
    {
      q: 'How does the PolicyEngine enforce zero-bypass authority?',
      a: 'The AI agent only produces a declarative RecoveryPlan data structure. The PolicyEngine independently checks the plan against maximum retry counts (<3), payment status eligibility, and merchant action whitelists. If a policy fails, the action is BLOCKED with zero database mutations.',
    },
    {
      q: 'How does RecoverX prevent double-charging during timeouts?',
      a: 'Every action generates an atomic idempotency key hash(payment_id, action_type, attempt_number). If an execution encounters a network timeout, it transitions into an UNKNOWN state rather than blindly retrying. It is then actively reconciled with the clearinghouse ledger.',
    },
    {
      q: 'How does Bayesian online calibration prevent strategy drift?',
      a: 'We use conjugate Beta-Binomial Bayesian updating (alpha_post = alpha_prior + successes, beta_post = beta_prior + failures). To eliminate manipulation from small anomalous sample bursts, posterior estimates are mathematically clamped within ±20% of baseline domain priors.',
    },
  ];

  return (
    <div className="min-h-screen bg-[#070B14] text-gray-100 relative overflow-x-hidden font-sans">
      {/* 3D Particle Mesh Canvas Background */}
      <ParticleMeshBackground />

      {/* Cybernetic ambient gradient glows */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[500px] bg-gradient-to-b from-indigo-600/15 via-pink-600/10 to-transparent blur-[120px] pointer-events-none z-0" />
      <div className="absolute top-[800px] -left-40 w-[600px] h-[600px] bg-blue-600/10 blur-[140px] pointer-events-none z-0" />
      <div className="absolute top-[1600px] -right-40 w-[600px] h-[600px] bg-pink-600/10 blur-[140px] pointer-events-none z-0" />

      {/* Navigation Header */}
      <header className="sticky top-0 z-50 backdrop-blur-xl bg-[#070B14]/80 border-b border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          {/* Brand Logo */}
          <Link to="/" className="flex items-center gap-3 group">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center text-white font-extrabold text-lg shadow-lg shadow-indigo-500/25 border border-white/20 group-hover:scale-105 transition-transform">
              ⚡
            </div>
            <div>
              <span className="font-heading font-black text-lg text-white tracking-tight flex items-center gap-1.5">
                Recover<span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-pink-400">X</span>
              </span>
              <span className="text-[9px] font-mono text-emerald-400 block -mt-1 font-bold">
                AI REVENUE RECOVERY
              </span>
            </div>
          </Link>

          {/* Center Links */}
          <nav className="hidden lg:flex items-center gap-5 text-xs font-semibold text-gray-300">
            <button
              type="button"
              onClick={() => setShowHowItWorksModal(true)}
              className="text-indigo-300 hover:text-white transition-colors cursor-pointer flex items-center gap-1 font-bold"
            >
              <Sparkles className="w-3.5 h-3.5 text-pink-400" />
              <span>How It Works?</span>
            </button>
            <a href="#pipeline" className="hover:text-white transition-colors">Simulation</a>
            <a href="#architecture" className="hover:text-white transition-colors">Architecture</a>
            <a href="#roi" className="hover:text-white transition-colors">ROI Calculator</a>
            <a href="#comparison" className="hover:text-white transition-colors">Comparison</a>
            <a href="#benchmarks" className="hover:text-white transition-colors">Benchmarks</a>
          </nav>

          {/* Action CTAs */}
          <div className="flex items-center gap-3">
            <a
              href="https://github.com/joshi-chinmay-016/RecoverX"
              target="_blank"
              rel="noopener noreferrer"
              className="p-2 rounded-xl bg-surface-card hover:bg-surface-hover border border-border text-gray-400 hover:text-white transition-all"
              title="View Source on GitHub"
            >
              <Github className="w-4 h-4" />
            </a>

            <Link
              to="/login"
              className="px-3.5 py-1.5 rounded-xl bg-surface-card hover:bg-surface-hover border border-border text-xs font-semibold text-gray-200 transition-all"
            >
              Sign In
            </Link>

            <Link
              to="/login"
              className="px-4 py-1.5 rounded-xl bg-gradient-to-r from-indigo-600 to-pink-600 hover:from-indigo-500 hover:to-pink-500 text-xs font-bold text-white shadow-lg shadow-indigo-500/25 hover:shadow-indigo-500/40 transition-all flex items-center gap-1.5"
            >
              <Zap className="w-3.5 h-3.5 fill-white" />
              <span>Launch Demo</span>
            </Link>
          </div>
        </div>
      </header>

      {/* Main Content Container */}
      <main className="relative z-10 space-y-24 sm:space-y-32 pb-24">
        {/* ============================================================ */}
        {/* HERO SECTION WITH 3D HOLOGRAPHIC CARD                        */}
        {/* ============================================================ */}
        <section className="pt-12 sm:pt-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
            {/* Left Col: Hero Typography & CTAs (7 cols) */}
            <div className="lg:col-span-7 space-y-6 text-center lg:text-left">
              {/* Telemetry pill */}
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 text-xs font-mono">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                <span className="font-bold">187/187 Tests Verified</span>
                <span className="text-gray-500">|</span>
                <span>Bayesian Engine Online</span>
              </div>

              {/* Punchy Heading */}
              <h1 className="font-heading font-black text-4xl sm:text-5xl lg:text-6xl text-white tracking-tight leading-[1.1]">
                Turn Payment Drops Into{' '}
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 via-pink-400 to-emerald-400">
                  Captured Revenue
                </span>
              </h1>

              {/* Subtitle */}
              <p className="text-sm sm:text-base text-gray-300 max-w-2xl mx-auto lg:mx-0 leading-relaxed">
                Autonomous AI reasoning meets deterministic policy guardrails. Ingest webhooks, diagnose failure codes, execute smart retries, and dynamically recalibrate recovery yields without mathematical hallucinations.
              </p>

              {/* Primary Action Buttons */}
              <div className="flex flex-col sm:flex-row items-center justify-center lg:justify-start gap-4 pt-2">
                <Link
                  to="/login"
                  className="w-full sm:w-auto px-7 py-3.5 rounded-2xl bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 hover:from-indigo-500 hover:to-pink-500 text-white font-heading font-extrabold text-sm shadow-xl shadow-indigo-500/30 hover:scale-105 transition-all flex items-center justify-center gap-2 cursor-pointer"
                >
                  <Play className="w-4 h-4 fill-white" />
                  <span>Explore Live Demo Sandbox</span>
                  <ArrowRight className="w-4 h-4" />
                </Link>

                <button
                  type="button"
                  onClick={() => setShowHowItWorksModal(true)}
                  className="w-full sm:w-auto px-6 py-3.5 rounded-2xl bg-surface-card hover:bg-surface-hover border border-border hover:border-pink-500/40 text-gray-200 font-heading font-bold text-sm transition-all flex items-center justify-center gap-2 cursor-pointer"
                >
                  <Sparkles className="w-4 h-4 text-pink-400" />
                  <span>How It Works? (Architecture)</span>
                </button>
              </div>

              {/* Micro specs row */}
              <div className="grid grid-cols-3 gap-4 pt-6 border-t border-border/80 text-left max-w-lg mx-auto lg:mx-0">
                <div>
                  <span className="font-mono text-xl font-extrabold text-white">0%</span>
                  <span className="text-[11px] text-gray-400 block font-mono">Math Hallucination</span>
                </div>
                <div>
                  <div className="flex items-center gap-1.5">
                    <span className="font-mono text-xl font-extrabold text-emerald-400">&lt; 12ms</span>
                    <button
                      type="button"
                      onClick={() => setShowLatencyModal(true)}
                      className="px-1.5 py-0.5 rounded-full bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 hover:text-white border border-emerald-500/40 text-[10px] font-mono font-bold transition-all cursor-pointer flex items-center gap-1 shadow-sm hover:scale-105 active:scale-95"
                      title="Click to view latency architecture breakdown"
                    >
                      <HelpCircle className="w-2.5 h-2.5" />
                      <span>How?</span>
                    </button>
                  </div>
                  <span className="text-[11px] text-gray-400 block font-mono">Decision Latency</span>
                </div>
                <div>
                  <span className="font-mono text-xl font-extrabold text-pink-400">100%</span>
                  <span className="text-[11px] text-gray-400 block font-mono">Idempotent Safe</span>
                </div>
              </div>
            </div>

            {/* Right Col: 3D Holographic Transaction Visualizer (5 cols) */}
            <div className="lg:col-span-5">
              <TiltCard
                maxRotation={14}
                depth={45}
                glowColor="rgba(99, 102, 241, 0.35)"
                className="rounded-3xl border border-indigo-500/30 bg-gradient-to-br from-surface-card via-surface-solid to-[#0e1424] p-6 sm:p-7 shadow-2xl shadow-indigo-500/15"
              >
                <div className="space-y-5">
                  {/* Hologram Header */}
                  <div className="flex items-center justify-between border-b border-border pb-3">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full bg-emerald-400 animate-pulse" />
                      <span className="text-xs font-mono text-gray-300 font-bold">
                        LIVE PAYMENT TELEMETRY
                      </span>
                    </div>
                    <span className="text-[10px] font-mono bg-indigo-500/20 text-indigo-300 px-2 py-0.5 rounded border border-indigo-500/30">
                      HMAC-SHA256
                    </span>
                  </div>

                  {/* Transaction Snapshot */}
                  <div className="p-4 rounded-2xl bg-black/40 border border-white/10 space-y-3">
                    <div className="flex justify-between items-start">
                      <div>
                        <span className="text-[10px] font-mono text-gray-400 uppercase">Payment Ref</span>
                        <div className="font-mono text-xs font-bold text-white">pay_demo_scenario_a_001</div>
                      </div>
                      <span className="text-xs font-mono font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded">
                        RECOVERED
                      </span>
                    </div>

                    <div className="flex justify-between items-baseline">
                      <span className="font-heading font-black text-3xl text-white">₹2,450.00</span>
                      <span className="text-xs font-mono text-pink-300 font-semibold">UPI Auto-Retry</span>
                    </div>

                    <div className="flex items-center gap-2 text-[11px] font-mono text-gray-400 pt-1 border-t border-white/5">
                      <Clock className="w-3 h-3 text-indigo-400" />
                      <span>Recovered in 1.4 seconds</span>
                    </div>
                  </div>

                  {/* 3D Pipeline Mini Steps */}
                  <div className="space-y-2 text-xs">
                    <div className="p-2.5 rounded-xl bg-surface-card border border-border flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                        <span className="text-gray-300">Failure Intelligence Classification</span>
                      </div>
                      <span className="font-mono text-indigo-300 text-[11px]">Score: 85</span>
                    </div>

                    <div className="p-2.5 rounded-xl bg-surface-card border border-border flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                        <span className="text-gray-300">AI Agent Recovery Plan</span>
                      </div>
                      <span className="font-mono text-pink-300 text-[11px]">Gemini 1.5</span>
                    </div>

                    <div className="p-2.5 rounded-xl bg-surface-card border border-border flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                        <span className="text-gray-300">Deterministic PolicyEngine Gate</span>
                      </div>
                      <span className="font-mono text-emerald-300 text-[11px]">ALLOWED</span>
                    </div>
                  </div>

                  {/* Bayesian Lift Callout */}
                  <div className="p-3 rounded-xl bg-gradient-to-r from-indigo-500/10 to-pink-500/10 border border-indigo-500/20 text-xs flex items-center justify-between">
                    <div className="flex items-center gap-1.5">
                      <TrendingUp className="w-4 h-4 text-pink-400" />
                      <span className="text-gray-300 font-semibold">Bayesian Posterior Lift:</span>
                    </div>
                    <span className="font-mono font-bold text-emerald-400">+0.4% Calibration</span>
                  </div>
                </div>
              </TiltCard>
            </div>
          </div>
        </section>

        {/* ============================================================ */}
        {/* HOW IT WORKS SECTION (ENTERPRISE / HIGH-TECH ARCHITECTURE)   */}
        {/* ============================================================ */}
        <section id="how-it-works" className="px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto scroll-mt-24 space-y-12">
          <div className="text-center max-w-3xl mx-auto space-y-3">
            <span className="text-[10px] font-mono font-bold uppercase tracking-wider px-3 py-1 rounded-full bg-gradient-to-r from-indigo-500/20 to-pink-500/20 text-indigo-300 border border-indigo-500/30 flex items-center gap-1.5 w-fit mx-auto">
              <Sparkles className="w-3.5 h-3.5 text-pink-400" />
              <span>How It Works • The Closed-Loop Blueprint</span>
            </span>
            <h2 className="font-heading font-black text-3xl sm:text-4xl text-white tracking-tight">
              From Webhook Ingestion to Bayesian Calibration
            </h2>
            <p className="text-xs sm:text-sm text-gray-300 leading-relaxed">
              Leading payment platforms lose up to 15% of transactions to transient network drops and gateway downtime. RecoverX intercepts payment failure events and executes an autonomous closed-loop recovery flow.
            </p>
          </div>

          {/* 3 High-Impact Process Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Process 1 */}
            <TiltCard
              maxRotation={10}
              depth={25}
              glowColor="rgba(99, 102, 241, 0.25)"
              className="p-6 rounded-3xl bg-surface-card border border-indigo-500/30 flex flex-col justify-between space-y-4"
            >
              <div className="space-y-3">
                <div className="w-10 h-10 rounded-2xl bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 flex items-center justify-center font-mono font-bold">
                  01
                </div>
                <h3 className="font-heading font-extrabold text-base text-white">
                  1. Ingest & Classify (<code className="text-emerald-400 font-mono">&lt;2ms</code>)
                </h3>
                <p className="text-xs text-gray-300 leading-relaxed">
                  Cryptographically verifies HMAC-SHA256 signatures, deduplicates on provider event ID, and scores opportunity value using deterministic Python rule classifiers. Zero LLM math hallucinations.
                </p>
              </div>
              <div className="text-[11px] font-mono text-indigo-300 font-semibold pt-2 border-t border-border">
                Paise Math • 100% Constant-Time
              </div>
            </TiltCard>

            {/* Process 2 */}
            <TiltCard
              maxRotation={10}
              depth={25}
              glowColor="rgba(236, 72, 153, 0.25)"
              className="p-6 rounded-3xl bg-surface-card border border-pink-500/30 flex flex-col justify-between space-y-4"
            >
              <div className="space-y-3">
                <div className="w-10 h-10 rounded-2xl bg-pink-500/20 text-pink-300 border border-pink-500/30 flex items-center justify-center font-mono font-bold">
                  02
                </div>
                <h3 className="font-heading font-extrabold text-base text-white">
                  2. Reason & Guardrail (<code className="text-pink-400 font-mono">0-Bypass</code>)
                </h3>
                <p className="text-xs text-gray-300 leading-relaxed">
                  The AI Recovery Agent reasons over read-only diagnostic context to propose a recovery plan. The deterministic PolicyEngine enforces hard business constraints (<code className="text-indigo-300 font-mono">retries &lt; 3</code>) before execution.
                </p>
              </div>
              <div className="text-[11px] font-mono text-pink-300 font-semibold pt-2 border-t border-border">
                Sandboxed Tools • Policy-v1 Intercept
              </div>
            </TiltCard>

            {/* Process 3 */}
            <TiltCard
              maxRotation={10}
              depth={25}
              glowColor="rgba(16, 185, 129, 0.25)"
              className="p-6 rounded-3xl bg-surface-card border border-emerald-500/30 flex flex-col justify-between space-y-4"
            >
              <div className="space-y-3">
                <div className="w-10 h-10 rounded-2xl bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 flex items-center justify-center font-mono font-bold">
                  03
                </div>
                <h3 className="font-heading font-extrabold text-base text-white">
                  3. Execute & Calibrate (<code className="text-emerald-400 font-mono">±20% Clamp</code>)
                </h3>
                <p className="text-xs text-gray-300 leading-relaxed">
                  Executes retries via secondary provider adapters with idempotency keys. If timeouts occur, parks in UNKNOWN for active status polling. Every capture outcome feeds online Bayesian Beta-Binomial updating.
                </p>
              </div>
              <div className="text-[11px] font-mono text-emerald-300 font-semibold pt-2 border-t border-border">
                UNKNOWN Parking • Bayesian Posterior
              </div>
            </TiltCard>
          </div>

          {/* Deep-Dive Interactive Modal Launcher Banner */}
          <div className="p-6 rounded-3xl bg-gradient-to-r from-indigo-950/60 via-surface-card to-pink-950/60 border border-indigo-500/40 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="space-y-1 text-center sm:text-left">
              <h4 className="font-heading font-bold text-base text-white flex items-center justify-center sm:justify-start gap-2">
                <Sparkles className="w-4 h-4 text-pink-400" />
                <span>Want to inspect the complete 6-stage technical blueprint?</span>
              </h4>
              <p className="text-xs text-gray-400">
                Explore source code snippets, algorithmic guarantees, and mathematical safety guardrails.
              </p>
            </div>

            <button
              type="button"
              onClick={() => setShowHowItWorksModal(true)}
              className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-pink-600 hover:from-indigo-500 hover:to-pink-500 text-xs font-bold text-white shadow-lg shadow-indigo-500/25 transition-all flex items-center gap-2 cursor-pointer shrink-0"
            >
              <span>Open Technical Walkthrough</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </section>

        {/* ============================================================ */}
        {/* LIVE SIMULATION PIPELINE SECTION                             */}
        {/* ============================================================ */}
        <section id="pipeline" className="px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto scroll-mt-24">
          <div className="text-center max-w-2xl mx-auto mb-10">
            <span className="text-[10px] font-mono font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
              Interactive 3D Pipeline Simulator
            </span>
            <h2 className="font-heading font-extrabold text-3xl sm:text-4xl text-white tracking-tight mt-2">
              Test Deterministic Recovery in Action
            </h2>
            <p className="text-xs sm:text-sm text-gray-400 mt-2">
              Choose a real-world scenario below and watch the 3D pipeline evaluate, validate, and execute each stage in real time.
            </p>
          </div>

          <LivePipeline3D />
        </section>

        {/* ============================================================ */}
        {/* 6-STAGE CLOSED-LOOP ARCHITECTURE                             */}
        {/* ============================================================ */}
        <section id="architecture" className="px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto scroll-mt-24">
          <ArchitectureOrbit3D />
        </section>

        {/* ============================================================ */}
        {/* ROI CALCULATOR SECTION                                       */}
        {/* ============================================================ */}
        <section id="roi" className="px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto scroll-mt-24">
          <RoiCalculator3D />
        </section>

        {/* ============================================================ */}
        {/* TECHNICAL COMPARISON MATRIX                                  */}
        {/* ============================================================ */}
        <section id="comparison" className="px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto scroll-mt-24 space-y-8">
          <div className="text-center max-w-2xl mx-auto">
            <span className="text-[10px] font-mono font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
              Technical Comparison
            </span>
            <h2 className="font-heading font-extrabold text-3xl sm:text-4xl text-white tracking-tight mt-2">
              Traditional Retries vs RecoverX
            </h2>
            <p className="text-xs sm:text-sm text-gray-400 mt-2">
              Why blind webhook loops fail and how bounded autonomous intelligence captures more revenue.
            </p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs bg-surface-card border border-border rounded-2xl overflow-hidden">
              <thead>
                <tr className="border-b border-border bg-surface-solid text-gray-300 font-heading font-bold text-xs uppercase">
                  <th className="p-4 sm:p-5">Capability</th>
                  <th className="p-4 sm:p-5 text-gray-400">Legacy Hardcoded Retries</th>
                  <th className="p-4 sm:p-5 text-gray-400">Generic Rule Engines</th>
                  <th className="p-4 sm:p-5 text-emerald-400 font-extrabold bg-indigo-500/10">RecoverX Engine</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border text-gray-300">
                <tr className="hover:bg-white/5 transition-colors">
                  <td className="p-4 sm:p-5 font-semibold text-white">Idempotency & Double Charge Safety</td>
                  <td className="p-4 sm:p-5 text-rose-400">❌ High risk of double debit on timeout</td>
                  <td className="p-4 sm:p-5 text-amber-400">⚠️ Basic Redis locks only</td>
                  <td className="p-4 sm:p-5 text-emerald-300 font-semibold bg-indigo-500/10">
                    ✅ Atomic DB constraints & UNKNOWN reconciliation
                  </td>
                </tr>
                <tr className="hover:bg-white/5 transition-colors">
                  <td className="p-4 sm:p-5 font-semibold text-white">Opportunity Valuation</td>
                  <td className="p-4 sm:p-5 text-rose-400">❌ Static global rupee thresholds</td>
                  <td className="p-4 sm:p-5 text-amber-400">⚠️ Simple IF/ELSE thresholds</td>
                  <td className="p-4 sm:p-5 text-emerald-300 font-semibold bg-indigo-500/10">
                    ✅ Merchant-relative percentile scoring (0-100)
                  </td>
                </tr>
                <tr className="hover:bg-white/5 transition-colors">
                  <td className="p-4 sm:p-5 font-semibold text-white">AI Reasoning & Plan Synthesis</td>
                  <td className="p-4 sm:p-5 text-rose-400">❌ None</td>
                  <td className="p-4 sm:p-5 text-rose-400">❌ Unbounded / Raw prompt injection risk</td>
                  <td className="p-4 sm:p-5 text-emerald-300 font-semibold bg-indigo-500/10">
                    ✅ Bounded AI Agent + Read-only Sandboxed Tools
                  </td>
                </tr>
                <tr className="hover:bg-white/5 transition-colors">
                  <td className="p-4 sm:p-5 font-semibold text-white">Execution Guardrails</td>
                  <td className="p-4 sm:p-5 text-rose-400">❌ Blind loops burning gateway fees</td>
                  <td className="p-4 sm:p-5 text-amber-400">⚠️ Manual operator scripts</td>
                  <td className="p-4 sm:p-5 text-emerald-300 font-semibold bg-indigo-500/10">
                    ✅ Zero-bypass deterministic PolicyEngine gate
                  </td>
                </tr>
                <tr className="hover:bg-white/5 transition-colors">
                  <td className="p-4 sm:p-5 font-semibold text-white">Adaptive Learning Loop</td>
                  <td className="p-4 sm:p-5 text-rose-400">❌ Zero feedback</td>
                  <td className="p-4 sm:p-5 text-rose-400">❌ Static quarterly rule updates</td>
                  <td className="p-4 sm:p-5 text-emerald-300 font-semibold bg-indigo-500/10">
                    ✅ Online Beta-Binomial Bayesian updating (±20% bound)
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        {/* ============================================================ */}
        {/* BENCHMARK & VERIFICATION STATS MATRIX                         */}
        {/* ============================================================ */}
        <section id="benchmarks" className="px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto scroll-mt-24">
          <div className="p-8 sm:p-10 rounded-3xl bg-gradient-to-r from-indigo-950/40 via-surface-card to-pink-950/40 border border-indigo-500/30 grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
            <div>
              <div className="font-heading font-black text-3xl sm:text-4xl text-white">187/187</div>
              <div className="text-xs font-mono text-indigo-300 font-bold mt-1">Automated Tests Passed</div>
              <div className="text-[11px] text-gray-400 mt-0.5">Unit, integration & resilience</div>
            </div>

            <div>
              <div className="font-heading font-black text-3xl sm:text-4xl text-emerald-400">100%</div>
              <div className="text-xs font-mono text-emerald-300 font-bold mt-1">Plan Structure Validity</div>
              <div className="text-[11px] text-gray-400 mt-0.5">50-scenario evaluation benchmark</div>
            </div>

            <div>
              <div className="font-heading font-black text-3xl sm:text-4xl text-pink-400">0</div>
              <div className="text-xs font-mono text-pink-300 font-bold mt-1">DB Mutations on Read</div>
              <div className="text-[11px] text-gray-400 mt-0.5">Strict tool immutability boundary</div>
            </div>

            <div>
              <div className="font-heading font-black text-3xl sm:text-4xl text-amber-400">±20%</div>
              <div className="text-xs font-mono text-amber-300 font-bold mt-1">Bayesian Safety Clamp</div>
              <div className="text-[11px] text-gray-400 mt-0.5">Guaranteed anti-drift protection</div>
            </div>
          </div>
        </section>

        {/* ============================================================ */}
        {/* TECHNICAL FAQ ACCORDION                                      */}
        {/* ============================================================ */}
        <section className="px-4 sm:px-6 lg:px-8 max-w-4xl mx-auto space-y-6">
          <div className="text-center mb-8">
            <span className="text-[10px] font-mono font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
              Technical FAQ
            </span>
            <h2 className="font-heading font-extrabold text-2xl sm:text-3xl text-white tracking-tight mt-2">
              Engineering Guardrails & Architecture
            </h2>
          </div>

          <div className="space-y-3">
            {faqs.map((faq, idx) => {
              const isOpen = activeFaq === idx;
              return (
                <div
                  key={idx}
                  className="rounded-2xl bg-surface-card border border-border overflow-hidden transition-all"
                >
                  <button
                    onClick={() => setActiveFaq(isOpen ? null : idx)}
                    className="w-full p-5 text-left flex items-center justify-between gap-4 font-heading font-bold text-sm text-white hover:text-indigo-300 transition-colors cursor-pointer"
                  >
                    <span>{faq.q}</span>
                    {isOpen ? (
                      <ChevronUp className="w-4 h-4 text-pink-400 shrink-0" />
                    ) : (
                      <ChevronDown className="w-4 h-4 text-gray-400 shrink-0" />
                    )}
                  </button>
                  {isOpen && (
                    <div className="px-5 pb-5 text-xs text-gray-300 leading-relaxed border-t border-border/40 pt-3">
                      {faq.a}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </section>

        {/* ============================================================ */}
        {/* BOTTOM CTA BANNER                                            */}
        {/* ============================================================ */}
        <section className="px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
          <div className="p-8 sm:p-12 rounded-3xl bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 text-center space-y-6 shadow-2xl shadow-indigo-500/20">
            <h2 className="font-heading font-black text-3xl sm:text-4xl text-white tracking-tight">
              Ready to Recover Dropped Payment Revenue?
            </h2>
            <p className="text-xs sm:text-sm text-white/80 max-w-xl mx-auto leading-relaxed">
              Launch the interactive live sandbox with pre-seeded demo scenarios, explore real-time failure intelligence, and run the autonomous recovery agent.
            </p>
            <div className="flex flex-wrap items-center justify-center gap-4">
              <Link
                to="/login"
                className="px-8 py-3.5 rounded-2xl bg-white text-gray-900 font-heading font-black text-sm hover:bg-gray-100 hover:scale-105 transition-all shadow-lg cursor-pointer"
              >
                Launch Sandbox Demo
              </Link>
              <button
                type="button"
                onClick={() => setShowHowItWorksModal(true)}
                className="px-6 py-3.5 rounded-2xl bg-white/10 hover:bg-white/20 border border-white/20 text-white font-heading font-bold text-sm transition-all cursor-pointer"
              >
                View Architectural Details
              </button>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-border bg-[#050810] py-12 px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-6 text-xs text-gray-400">
          <div className="flex items-center gap-3">
            <div className="w-7 h-7 rounded-lg bg-indigo-600 text-white flex items-center justify-center font-bold text-sm">
              ⚡
            </div>
            <span className="font-heading font-bold text-white">RecoverX</span>
            <span>• Autonomous Revenue Recovery Platform</span>
          </div>

          <div className="flex items-center gap-6">
            <button
              type="button"
              onClick={() => setShowHowItWorksModal(true)}
              className="text-indigo-300 hover:text-white transition-colors cursor-pointer font-bold flex items-center gap-1"
            >
              <Sparkles className="w-3.5 h-3.5 text-pink-400" />
              <span>How It Works?</span>
            </button>
            <Link to="/login" className="hover:text-white transition-colors">Sign In</Link>
            <a href="#pipeline" className="hover:text-white transition-colors">Simulation</a>
            <a href="#architecture" className="hover:text-white transition-colors">Architecture</a>
            <a href="#roi" className="hover:text-white transition-colors">ROI Calculator</a>
            <a
              href="https://github.com/joshi-chinmay-016/RecoverX"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 px-3 py-1 rounded-xl bg-white/5 hover:bg-white/10 text-gray-200 hover:text-white border border-white/10 transition-all font-semibold"
            >
              <Github className="w-3.5 h-3.5" />
              <span>GitHub</span>
            </a>
          </div>

          <div className="font-mono text-[11px] text-gray-500">
            Python 3.12 • FastAPI • PostgreSQL 16 • React 19
          </div>
        </div>
      </footer>

      {/* ============================================================ */}
      {/* 3D LATENCY EXPLAINER MODAL                                   */}
      {/* ============================================================ */}
      {showLatencyModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-black/80 backdrop-blur-md animate-fade-in">
          <div
            className="relative w-full max-w-2xl rounded-3xl bg-surface-solid border border-indigo-500/30 p-6 sm:p-8 shadow-2xl shadow-indigo-500/20 max-h-[90vh] overflow-y-auto space-y-6"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="flex items-start justify-between border-b border-border pb-4">
              <div className="flex items-center gap-2.5">
                <div className="w-9 h-9 rounded-xl bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center justify-center font-bold">
                  ⚡
                </div>
                <div>
                  <h3 className="font-heading font-black text-lg sm:text-xl text-white">
                    How RecoverX Achieves &lt; 12ms Decision Latency
                  </h3>
                  <span className="text-xs font-mono text-emerald-400 font-semibold">
                    Deterministic Ingestion & Gate Execution Path
                  </span>
                </div>
              </div>

              <button
                type="button"
                onClick={() => setShowLatencyModal(false)}
                className="p-2 rounded-xl bg-surface-card hover:bg-white/10 text-gray-400 hover:text-white transition-colors cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Intro paragraph */}
            <p className="text-xs text-gray-300 leading-relaxed">
              The <strong className="text-emerald-300 font-mono">&lt; 12ms</strong> decision latency metric represents the <strong>deterministic ingestion, failure classification, and policy evaluation path</strong> of RecoverX. Here is the exact architectural breakdown of how this speed is achieved:
            </p>

            {/* Section 1 */}
            <div className="p-4 rounded-2xl bg-surface-card border border-border space-y-2">
              <div className="flex items-center gap-2 text-sm font-heading font-bold text-indigo-300">
                <Cpu className="w-4 h-4 text-pink-400" />
                <span>1. Zero LLM in Financial Math & Scoring (&lt; 2ms)</span>
              </div>
              <p className="text-xs text-gray-300 leading-relaxed">
                In traditional AI setups, sending a raw payment failure to an LLM for classification takes <strong>1,500ms – 4,000ms</strong> and introduces prompt hallucination risk.
              </p>
              <p className="text-xs text-gray-300 leading-relaxed">
                In RecoverX, failure classification and opportunity valuation are executed by the deterministic <code className="font-mono text-indigo-300 bg-black/30 px-1.5 py-0.5 rounded">RevenueIntelligenceEngine</code>:
              </p>
              <ul className="text-xs text-gray-300 space-y-1 pl-4 list-disc">
                <li><strong>Error Code & Reason Extraction:</strong> In-memory mapping (<code className="font-mono text-emerald-400">&lt; 0.3ms</code>).</li>
                <li><strong>Rule-based Classification (<code className="font-mono text-indigo-300">FailureClassifier</code>):</strong> In-memory lookup matching Razorpay/gateway failure codes (<code className="font-mono text-emerald-400">&lt; 0.2ms</code>).</li>
                <li><strong>Merchant-Relative Valuation (<code className="font-mono text-indigo-300">MerchantRelativeOpportunityScorer</code>):</strong> Vectorized percentile and opportunity calculation (<code className="font-mono text-emerald-400">&lt; 0.8ms</code>).</li>
              </ul>
              <div className="pt-1 text-xs font-mono font-bold text-emerald-300">
                Total Classification & Scoring Latency: ~1.3ms.
              </div>
            </div>

            {/* Section 2 */}
            <div className="p-4 rounded-2xl bg-surface-card border border-border space-y-2">
              <div className="flex items-center gap-2 text-sm font-heading font-bold text-indigo-300">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                <span>2. O(1) Deterministic PolicyEngine Gate Checks (&lt; 1ms)</span>
              </div>
              <p className="text-xs text-gray-300 leading-relaxed">
                When validating an action or plan, the <code className="font-mono text-indigo-300 bg-black/30 px-1.5 py-0.5 rounded">PolicyEngine</code> runs high-speed constraint checks:
              </p>
              <ul className="text-xs text-gray-300 space-y-1 pl-4 list-disc">
                <li><strong>Whitelist dictionary containment check (<code className="font-mono text-indigo-300">ActionType</code>):</strong> <span className="font-mono text-emerald-400">O(1) (~ 0.05ms)</span>.</li>
                <li><strong>Retry attempt limit comparison (<code className="font-mono text-indigo-300">attempt_count &lt; MAX_RETRY_ATTEMPTS</code>):</strong> <span className="font-mono text-emerald-400">O(1) (~ 0.05ms)</span>.</li>
                <li><strong>Payment status & idempotency key verification:</strong> <span className="font-mono text-emerald-400">(~ 0.2ms)</span>.</li>
              </ul>
              <div className="pt-1 text-xs font-mono font-bold text-emerald-300">
                Total PolicyEngine Gate Latency: ~0.4ms.
              </div>
            </div>

            {/* Section 3 */}
            <div className="p-4 rounded-2xl bg-surface-card border border-border space-y-3">
              <div className="flex items-center gap-2 text-sm font-heading font-bold text-indigo-300">
                <Database className="w-4 h-4 text-amber-400" />
                <span>3. High-Throughput Asynchronous Decoupling Architecture</span>
              </div>

              <div className="bg-black/60 p-4 rounded-xl font-mono text-[11px] text-gray-300 overflow-x-auto leading-relaxed border border-white/10">
                <pre>{`Incoming Webhook Request
       │
       ▼
 [ 1. HMAC-SHA256 Verification & Deduplication Check ]  ──► ~ 4.5ms
       │
       ▼
 [ 2. Deterministic Intelligence Scoring (Paise Math) ] ──► ~ 1.3ms
       │
       ▼
 [ 3. Deterministic PolicyEngine Decision & Outbox ]   ──► ~ 0.8ms
       │
       ▼
 ┌────────────────────────────────────────────────────────┐
 │ SYNCHRONOUS INGESTION LATENCY: ~ 6.6ms - 11.8ms (<12ms)│
 └────────────────────────────────────────────────────────┘
       │
       ▼ (Asynchronous Background Queue)
 [ 4. Heavy AI Agent Reasoning / LLM Plan Synthesis ]   ──► (Background Worker)`}</pre>
              </div>

              <p className="text-xs text-gray-300 leading-relaxed">
                By decoupling the LLM reasoning agent to background workers, RecoverX guarantees that synchronous payment webhook ingestion and real-time policy decisions remain strictly sub-12ms without blocking high-volume checkout traffic.
              </p>
            </div>

            {/* Modal Footer */}
            <div className="flex justify-end pt-2">
              <button
                type="button"
                onClick={() => setShowLatencyModal(false)}
                className="px-5 py-2 rounded-xl bg-gradient-to-r from-indigo-600 to-pink-600 hover:from-indigo-500 hover:to-pink-500 text-xs font-bold text-white transition-all cursor-pointer shadow-md"
              >
                Got It, Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ============================================================ */}
      {/* HOW IT WORKS FULL-SCREEN TECHNICAL WALKTHROUGH MODAL        */}
      {/* ============================================================ */}
      <HowItWorksModal
        isOpen={showHowItWorksModal}
        onClose={() => setShowHowItWorksModal(false)}
      />
    </div>
  );
};
