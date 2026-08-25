import React from 'react';
import { AgentAction } from '@/types/agent';
import {
  Database,
  BrainCircuit,
  ShieldCheck,
  FileCheck,
  CheckCircle,
  ArrowRight,
  ArrowDown,
  ShieldAlert,
  Zap,
} from 'lucide-react';
import { formatEnum } from '@/lib/formatters';

interface AgentFlowDiagramProps {
  activeStep?: number;
  proposedActions?: AgentAction[];
  fallbackStrategy?: string;
  className?: string;
}

export const AgentFlowDiagram: React.FC<AgentFlowDiagramProps> = ({
  activeStep = 0,
  proposedActions = [],
  fallbackStrategy = 'MANUAL_REVIEW',
  className,
}) => {
  // If proposedActions is explicitly passed with items, render strategy flow
  if (proposedActions && proposedActions.length > 0) {
    return (
      <div className={className || 'flex flex-col items-center gap-2 py-4'}>
        {proposedActions.map((action, idx) => (
          <React.Fragment key={idx}>
            <div className="w-full max-w-md bg-surface-solid border border-indigo-500/40 rounded-xl p-4 shadow-lg shadow-black/30 text-center relative group hover:border-indigo-400 transition-colors">
              <div className="text-[10px] font-mono font-bold tracking-wider uppercase text-indigo-400">
                Step {idx + 1} — Proposed Action
              </div>
              <div className="text-base font-heading font-bold text-white mt-1">
                {formatEnum(action.action_type)}
              </div>
              {action.purpose && (
                <p className="text-xs text-gray-400 mt-1 max-w-xs mx-auto">
                  {action.purpose}
                </p>
              )}
              {action.parameters && Object.keys(action.parameters).length > 0 && (
                <div className="mt-2 text-[11px] font-mono bg-white/5 py-1 px-2.5 rounded-lg text-indigo-200 inline-block">
                  {JSON.stringify(action.parameters)}
                </div>
              )}
            </div>
            <ArrowDown className="w-4 h-4 text-indigo-400 animate-bounce" />
          </React.Fragment>
        ))}

        {/* Outcome Gate */}
        <div className="w-full max-w-md bg-surface-solid border border-emerald-500/40 rounded-xl p-4 shadow-lg text-center">
          <div className="text-[10px] font-mono font-bold tracking-wider uppercase text-emerald-400 flex items-center justify-center gap-1">
            <CheckCircle className="w-3.5 h-3.5" /> Outcome Evaluation Gate
          </div>
          <div className="text-xs text-emerald-300 font-semibold mt-1">
            IF CAPTURED → CLOSE RECOVERY CASE
          </div>
          <div className="text-[11px] text-gray-400 mt-1 flex items-center justify-center gap-1">
            <ShieldAlert className="w-3 h-3 text-amber-400" /> IF FAILED → TRIGGER FALLBACK ({formatEnum(fallbackStrategy)})
          </div>
        </div>
      </div>
    );
  }

  // 4-Step Animated Pipeline Visualizer (Default)
  const steps = [
    {
      number: 1,
      title: 'Context Retrieval',
      desc: 'Read-only tools aggregate payment, history & merchant data',
      icon: <Database className="w-4 h-4" />,
    },
    {
      number: 2,
      title: 'Autonomous Reasoning',
      desc: 'Bounded AI agent diagnoses failure and evaluates strategies',
      icon: <BrainCircuit className="w-4 h-4" />,
    },
    {
      number: 3,
      title: 'PolicyEngine Gate',
      desc: 'Deterministic rules enforce max retries & safety boundaries',
      icon: <ShieldCheck className="w-4 h-4" />,
    },
    {
      number: 4,
      title: 'Plan Synthesis',
      desc: 'Structured RecoveryPlan ready for Phase 4 execution',
      icon: <FileCheck className="w-4 h-4" />,
    },
  ];

  return (
    <div className={className || 'py-4'}>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 relative">
        {steps.map((step) => {
          const isCompleted = activeStep > step.number;
          const isCurrent = activeStep === step.number;

          return (
            <div
              key={step.number}
              className={`p-4 rounded-2xl border transition-all relative flex flex-col justify-between ${
                isCurrent
                  ? 'bg-indigo-600/15 border-indigo-500 shadow-lg shadow-indigo-500/20 scale-[1.02]'
                  : isCompleted
                  ? 'bg-emerald-500/10 border-emerald-500/30'
                  : 'bg-surface-solid border-border opacity-70'
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div
                    className={`w-7 h-7 rounded-lg flex items-center justify-center font-mono font-bold text-xs ${
                      isCurrent
                        ? 'bg-indigo-500 text-white animate-pulse'
                        : isCompleted
                        ? 'bg-emerald-500 text-white'
                        : 'bg-white/5 text-gray-400'
                    }`}
                  >
                    {isCompleted ? <CheckCircle className="w-4 h-4" /> : step.number}
                  </div>

                  <span
                    className={`text-[10px] font-mono font-semibold uppercase ${
                      isCurrent
                        ? 'text-indigo-300'
                        : isCompleted
                        ? 'text-emerald-300'
                        : 'text-gray-500'
                    }`}
                  >
                    {isCurrent ? 'Running...' : isCompleted ? 'Passed' : 'Step ' + step.number}
                  </span>
                </div>

                <div className="flex items-center gap-1.5 font-heading font-bold text-sm text-white">
                  <span className={isCurrent ? 'text-indigo-400' : isCompleted ? 'text-emerald-400' : 'text-gray-400'}>
                    {step.icon}
                  </span>
                  <span>{step.title}</span>
                </div>

                <p className="text-xs text-gray-400 mt-1 leading-relaxed">
                  {step.desc}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
