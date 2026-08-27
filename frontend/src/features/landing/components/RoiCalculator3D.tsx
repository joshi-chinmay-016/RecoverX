import React, { useState } from 'react';
import { Coins, TrendingUp, Sparkles, Percent, ShieldCheck } from 'lucide-react';
import { TiltCard } from './TiltCard';

export const RoiCalculator3D: React.FC = () => {
  // Monthly GMV in Crores (default 10 Cr = ₹10,00,00,000)
  const [monthlyGmvCr, setMonthlyGmvCr] = useState<number>(10);
  // Average Ticket Size in INR (default ₹2,500)
  const [avgTicket, setAvgTicket] = useState<number>(2500);
  // Payment Failure Rate % (default 12%)
  const [failureRate, setFailureRate] = useState<number>(12);
  // Expected Recovery Lift % (default 65% based on RecoverX Bayesian model)
  const recoveryRate = 0.65;

  const monthlyGmvRupees = monthlyGmvCr * 10000000;
  const monthlyFailedRevenue = monthlyGmvRupees * (failureRate / 100);
  const monthlyRecoveredRevenue = monthlyFailedRevenue * recoveryRate;
  const annualRecoveredRevenue = monthlyRecoveredRevenue * 12;
  const recoveredTransactionsMonthly = Math.round((monthlyFailedRevenue / avgTicket) * recoveryRate);

  const formatCrores = (valRupees: number) => {
    if (valRupees >= 10000000) {
      return `₹${(valRupees / 10000000).toFixed(2)} Cr`;
    } else if (valRupees >= 100000) {
      return `₹${(valRupees / 100000).toFixed(2)} Lakh`;
    } else {
      return `₹${valRupees.toLocaleString('en-IN')}`;
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
      {/* Interactive Controls (Left 6 cols) */}
      <div className="lg:col-span-6 space-y-6">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="text-[10px] font-mono font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
              Interactive ROI Modeler
            </span>
          </div>
          <h3 className="font-heading font-extrabold text-2xl sm:text-3xl text-white tracking-tight">
            Calculate Your Recoverable Revenue
          </h3>
          <p className="text-xs sm:text-sm text-gray-400 mt-2 leading-relaxed">
            RecoverX dynamically routes recoverable payments through intelligent retries and alternate channels without incurring arbitrary provider fee penalties.
          </p>
        </div>

        <div className="space-y-5 bg-surface-card border border-border p-6 rounded-2xl">
          {/* Slider 1: Monthly GMV */}
          <div className="space-y-2">
            <div className="flex justify-between items-center text-xs">
              <span className="text-gray-300 font-semibold flex items-center gap-1.5">
                <Coins className="w-3.5 h-3.5 text-indigo-400" />
                Monthly Processing Volume (GMV)
              </span>
              <span className="font-mono text-indigo-300 font-bold text-sm">
                ₹{monthlyGmvCr} Crore / mo
              </span>
            </div>
            <input
              type="range"
              min="1"
              max="100"
              step="1"
              value={monthlyGmvCr}
              onChange={(e) => setMonthlyGmvCr(Number(e.target.value))}
              className="w-full h-2 bg-surface-solid rounded-lg appearance-none cursor-pointer accent-indigo-500"
            />
            <div className="flex justify-between text-[10px] font-mono text-gray-500">
              <span>₹1 Cr</span>
              <span>₹50 Cr</span>
              <span>₹100 Cr</span>
            </div>
          </div>

          {/* Slider 2: Average Ticket Size */}
          <div className="space-y-2">
            <div className="flex justify-between items-center text-xs">
              <span className="text-gray-300 font-semibold flex items-center gap-1.5">
                <TrendingUp className="w-3.5 h-3.5 text-pink-400" />
                Average Transaction Value (AOV)
              </span>
              <span className="font-mono text-pink-300 font-bold text-sm">
                ₹{avgTicket.toLocaleString('en-IN')}
              </span>
            </div>
            <input
              type="range"
              min="500"
              max="25000"
              step="250"
              value={avgTicket}
              onChange={(e) => setAvgTicket(Number(e.target.value))}
              className="w-full h-2 bg-surface-solid rounded-lg appearance-none cursor-pointer accent-pink-500"
            />
            <div className="flex justify-between text-[10px] font-mono text-gray-500">
              <span>₹500</span>
              <span>₹12,500</span>
              <span>₹25,000</span>
            </div>
          </div>

          {/* Slider 3: Failure Rate */}
          <div className="space-y-2">
            <div className="flex justify-between items-center text-xs">
              <span className="text-gray-300 font-semibold flex items-center gap-1.5">
                <Percent className="w-3.5 h-3.5 text-emerald-400" />
                Payment Drop Rate
              </span>
              <span className="font-mono text-emerald-300 font-bold text-sm">
                {failureRate}%
              </span>
            </div>
            <input
              type="range"
              min="3"
              max="25"
              step="1"
              value={failureRate}
              onChange={(e) => setFailureRate(Number(e.target.value))}
              className="w-full h-2 bg-surface-solid rounded-lg appearance-none cursor-pointer accent-emerald-500"
            />
            <div className="flex justify-between text-[10px] font-mono text-gray-500">
              <span>3% (Low)</span>
              <span>12% (Typical)</span>
              <span>25% (High)</span>
            </div>
          </div>
        </div>
      </div>

      {/* 3D Yield Card Projection (Right 6 cols) */}
      <div className="lg:col-span-6">
        <TiltCard
          maxRotation={14}
          depth={40}
          glowColor="rgba(236, 72, 153, 0.25)"
          className="rounded-3xl border border-pink-500/30 bg-gradient-to-br from-surface-card via-surface-solid to-[#111827] p-8 shadow-2xl shadow-indigo-500/10"
        >
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-xl bg-pink-500/20 text-pink-400 flex items-center justify-center">
                  <Sparkles className="w-4 h-4" />
                </div>
                <span className="font-heading font-extrabold text-sm text-white">
                  Projected Net Recovery Lift
                </span>
              </div>
              <span className="text-[10px] font-mono font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 px-2.5 py-0.5 rounded-full">
                65% Benchmark Recovery
              </span>
            </div>

            {/* Big Hero Number: Annual Lift */}
            <div>
              <span className="text-xs font-mono uppercase text-gray-400 font-semibold block">
                Estimated Annual Recovered Volume
              </span>
              <div className="font-heading font-black text-4xl sm:text-5xl text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 via-teal-300 to-sky-400 mt-1">
                {formatCrores(annualRecoveredRevenue)}
              </div>
              <span className="text-xs text-gray-400 font-mono mt-1 block">
                ~ {formatCrores(monthlyRecoveredRevenue)} / month added directly to topline
              </span>
            </div>

            {/* Micro Breakdown Grid */}
            <div className="grid grid-cols-2 gap-3 pt-4 border-t border-border">
              <div className="p-3.5 rounded-xl bg-black/20 border border-white/5 space-y-1">
                <span className="text-[11px] text-gray-400 block font-mono">Monthly Failed Vol</span>
                <span className="font-heading font-bold text-base text-rose-400">
                  {formatCrores(monthlyFailedRevenue)}
                </span>
              </div>

              <div className="p-3.5 rounded-xl bg-black/20 border border-white/5 space-y-1">
                <span className="text-[11px] text-gray-400 block font-mono">Saved Orders / mo</span>
                <span className="font-heading font-bold text-base text-indigo-300 font-mono">
                  {recoveredTransactionsMonthly.toLocaleString('en-IN')} orders
                </span>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-200 flex items-start gap-2.5">
              <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
              <span>
                <strong>Zero Fee Waste:</strong> PolicyEngine blocks unauthorized retries after 3 failures, saving up to <strong>₹{(recoveredTransactionsMonthly * 15).toLocaleString('en-IN')}</strong> in redundant gateway processing fees.
              </span>
            </div>
          </div>
        </TiltCard>
      </div>
    </div>
  );
};
