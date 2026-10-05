import React, { useState, useEffect } from 'react';
import { Card } from '../ui/Card';
import { Skeleton } from '../ui/Skeleton';
import { WorkflowTimeline } from './WorkflowTimeline';
import { ResearchStatusBadge } from './ResearchStatusBadge';
import type { ResearchRunResponse } from '../../api/types';

interface ResearchProgressProps {
  run: ResearchRunResponse;
}

export const ResearchProgress: React.FC<ResearchProgressProps> = ({ run }) => {
  const [elapsedSeconds, setElapsedSeconds] = useState<number>(0);

  useEffect(() => {
    if (!run.started_at) return;
    const start = new Date(run.started_at).getTime();

    const updateTimer = () => {
      const now = Date.now();
      setElapsedSeconds(Math.max(0, Math.floor((now - start) / 1000)));
    };

    updateTimer();
    const interval = setInterval(updateTimer, 1000);
    return () => clearInterval(interval);
  }, [run.started_at]);

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Top Run Status Card */}
      <Card className="p-6 border-indigo-200/50 dark:border-indigo-900/50 bg-gradient-to-b from-indigo-50/20 to-transparent dark:from-indigo-950/10">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-zinc-200/80 dark:border-zinc-800">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-mono text-zinc-500 uppercase tracking-wider">Run #{run.run_id}</span>
              <ResearchStatusBadge status={run.status} size="sm" />
            </div>
            <h2 className="text-lg sm:text-xl font-semibold text-zinc-900 dark:text-zinc-100">
              {run.topic}
            </h2>
          </div>
        </div>

        {/* Workflow Timeline */}
        <div className="mt-6">
          <WorkflowTimeline
            stepsCompleted={run.summary?.steps_completed ?? 0}
            revisionCount={run.summary?.revision_count ?? 0}
            status={run.status}
            elapsedSeconds={elapsedSeconds}
          />
        </div>
      </Card>

      {/* Loading Skeleton Simulation for Report drafting */}
      <Card className="p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div className="space-y-1.5">
            <Skeleton className="h-5 w-44" />
            <Skeleton className="h-3.5 w-72" />
          </div>
          <Skeleton className="h-7 w-24 rounded-full" />
        </div>
        <div className="space-y-2 pt-2">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-11/12" />
          <Skeleton className="h-4 w-4/5" />
        </div>
        <div className="pt-2 flex gap-2">
          <Skeleton className="h-8 w-28 rounded-lg" />
          <Skeleton className="h-8 w-32 rounded-lg" />
        </div>
      </Card>

      <p className="text-xs text-center text-zinc-500 dark:text-zinc-400">
        InsightForge runs multi-stage inference locally with pgvector similarity gating. Execution typically completes in 60–180 seconds.
      </p>
    </div>
  );
};
