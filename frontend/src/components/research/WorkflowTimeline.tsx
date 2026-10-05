import React from 'react';
import { Check, Loader2, Sparkles, Database, FileText, ShieldAlert, CheckCircle2, RotateCw } from 'lucide-react';
import { cn } from '../../lib/utils';
import type { ResearchRunStatus } from '../../api/types';

interface WorkflowTimelineProps {
  stepsCompleted?: number;
  revisionCount?: number;
  status: ResearchRunStatus;
  elapsedSeconds?: number;
}

interface StepItem {
  id: string;
  name: string;
  description: string;
  icon: React.ElementType;
}

const WORKFLOW_STEPS: StepItem[] = [
  {
    id: 'planner',
    name: 'Planner Agent',
    description: 'Deconstructs topic into targeted sub-questions',
    icon: Sparkles,
  },
  {
    id: 'retriever',
    name: 'Retriever Agent',
    description: 'Queries pgvector with 0.255 distance threshold',
    icon: Database,
  },
  {
    id: 'synthesizer',
    name: 'Synthesizer Agent',
    description: 'Extracts verbatim sentences with 0.50 relevance floor',
    icon: FileText,
  },
  {
    id: 'critic',
    name: 'Critic Agent',
    description: 'Verifies internal consistency and sub-question coverage',
    icon: ShieldAlert,
  },
  {
    id: 'finalize',
    name: 'Finalize & Ground',
    description: 'Assembles verified report and establishes citation trail',
    icon: CheckCircle2,
  },
];

export const WorkflowTimeline: React.FC<WorkflowTimelineProps> = ({
  stepsCompleted = 0,
  revisionCount = 0,
  status,
  elapsedSeconds,
}) => {
  const isFinished = status !== 'running';
  const isFailed = status === 'failed';

  // Determine active step index safely based on backend steps_completed
  // LangGraph steps: 0=planner, 1=retriever, 2=synthesizer, 3=critic/revisions, 4+=finalize
  const getStepState = (index: number) => {
    if (isFailed) {
      if (index === Math.min(stepsCompleted, 4)) return 'failed';
      if (index < stepsCompleted) return 'completed';
      return 'pending';
    }

    if (isFinished) {
      return 'completed';
    }

    // Active run:
    if (index < stepsCompleted) return 'completed';
    if (index === stepsCompleted || (stepsCompleted >= 4 && index === 4)) return 'running';
    return 'pending';
  };

  return (
    <div className="w-full space-y-4">
      {/* Header bar with live metrics */}
      <div className="flex flex-wrap items-center justify-between gap-3 text-xs text-zinc-500 dark:text-zinc-400 border-b border-zinc-200 dark:border-zinc-800 pb-3">
        <div className="flex items-center gap-2">
          <span className="font-mono text-zinc-700 dark:text-zinc-300 font-medium">LangGraph Pipeline</span>
          <span className="w-1 h-1 rounded-full bg-zinc-400" />
          <span>{stepsCompleted} step{stepsCompleted === 1 ? '' : 's'} recorded</span>
        </div>
        <div className="flex items-center gap-4">
          {revisionCount > 0 && (
            <span className="flex items-center gap-1.5 text-amber-600 dark:text-amber-400 font-medium">
              <RotateCw className="w-3.5 h-3.5 animate-spin" />
              {revisionCount} revision loop{revisionCount === 1 ? '' : 's'}
            </span>
          )}
          {typeof elapsedSeconds === 'number' && (
            <span className="font-mono">
              Elapsed: {Math.floor(elapsedSeconds / 60)}m {elapsedSeconds % 60}s
            </span>
          )}
        </div>
      </div>

      {/* Stepper items */}
      <div className="space-y-3">
        {WORKFLOW_STEPS.map((step, idx) => {
          const stepState = getStepState(idx);
          const Icon = step.icon;

          return (
            <div
              key={step.id}
              className={cn(
                'flex items-start gap-3.5 p-3 rounded-xl border transition-all duration-200',
                stepState === 'running' && 'bg-indigo-50/60 dark:bg-indigo-950/20 border-indigo-200 dark:border-indigo-800 shadow-xs',
                stepState === 'completed' && 'bg-zinc-50/50 dark:bg-zinc-900/40 border-zinc-200/70 dark:border-zinc-800/70',
                stepState === 'pending' && 'bg-transparent border-transparent opacity-50',
                stepState === 'failed' && 'bg-rose-50/50 dark:bg-rose-950/20 border-rose-200 dark:border-rose-900'
              )}
            >
              {/* Step indicator circle */}
              <div
                className={cn(
                  'w-8 h-8 rounded-lg flex items-center justify-center shrink-0 border text-xs font-mono font-medium transition-colors',
                  stepState === 'completed' && 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/30',
                  stepState === 'running' && 'bg-indigo-600 text-white border-indigo-600 shadow-xs shadow-indigo-500/30',
                  stepState === 'pending' && 'bg-zinc-100 dark:bg-zinc-800 text-zinc-400 border-zinc-200 dark:border-zinc-700',
                  stepState === 'failed' && 'bg-rose-600 text-white border-rose-600'
                )}
              >
                {stepState === 'completed' && <Check className="w-4 h-4 stroke-[2.5]" />}
                {stepState === 'running' && <Loader2 className="w-4 h-4 animate-spin" />}
                {stepState === 'pending' && <Icon className="w-4 h-4" />}
                {stepState === 'failed' && '!'}
              </div>

              {/* Step details */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <h4 className={cn(
                    'text-sm font-semibold truncate',
                    stepState === 'running' && 'text-indigo-950 dark:text-indigo-200',
                    stepState === 'completed' && 'text-zinc-800 dark:text-zinc-200',
                    stepState === 'pending' && 'text-zinc-400 dark:text-zinc-500',
                    stepState === 'failed' && 'text-rose-700 dark:text-rose-400'
                  )}>
                    {step.name}
                  </h4>
                  {stepState === 'running' && (
                    <span className="text-[11px] font-medium text-indigo-600 dark:text-indigo-400 flex items-center gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-ping" />
                      Active
                    </span>
                  )}
                  {stepState === 'completed' && (
                    <span className="text-[11px] text-emerald-600 dark:text-emerald-400 font-medium">Done</span>
                  )}
                </div>
                <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-0.5 leading-relaxed">
                  {step.description}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
