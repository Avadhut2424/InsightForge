import React, { useState, useEffect } from 'react';
import { AppShell } from '../components/layout/AppShell';
import { ResearchInput } from '../components/research/ResearchInput';
import { ResearchProgress } from '../components/research/ResearchProgress';
import { ReportView } from '../components/research/ReportView';
import { FailedState } from '../components/research/FailedState';
import { Card } from '../components/ui/Card';
import { Skeleton } from '../components/ui/Skeleton';
import { Button } from '../components/ui/Button';
import { AlertCircle, ArrowLeft } from 'lucide-react';
import { useCreateResearchMutation, useResearchRunQuery } from '../hooks/useResearch';
import { useRunHistory } from '../hooks/useRunHistory';
import type { ResearchRunResponse } from '../api/types';

export const WorkspacePage: React.FC = () => {
  const [currentRunId, setCurrentRunId] = useState<number | null>(() => {
    if (typeof window !== 'undefined') {
      const hashMatch = window.location.hash.match(/#run=(\d+)/);
      if (hashMatch) {
        return parseInt(hashMatch[1], 10);
      }
    }
    return null;
  });

  const { runs, addOrUpdateRun, updateRunStatus, clearHistory } = useRunHistory();
  const createMutation = useCreateResearchMutation();

  // Sync run ID to URL hash
  useEffect(() => {
    if (currentRunId) {
      window.location.hash = `run=${currentRunId}`;
    } else {
      window.history.replaceState(null, '', window.location.pathname);
    }
  }, [currentRunId]);

  // Polling query for the active run
  const handleRunUpdated = (data: ResearchRunResponse) => {
    updateRunStatus(data.run_id, data.status, data.completed_at);
  };

  const {
    data: runData,
    isLoading: isRunLoading,
    isError: isRunError,
    error: runError,
  } = useResearchRunQuery(currentRunId, handleRunUpdated);

  const handleStartResearch = (topic: string) => {
    createMutation.mutate(topic, {
      onSuccess: (data) => {
        addOrUpdateRun({
          runId: data.run_id,
          topic,
          status: 'running',
          startedAt: new Date().toISOString(),
          completedAt: null,
        });
        setCurrentRunId(data.run_id);
      },
    });
  };

  const handleNewResearch = () => {
    setCurrentRunId(null);
  };

  return (
    <AppShell
      runs={runs}
      currentRunId={currentRunId}
      onSelectRun={(id) => setCurrentRunId(id)}
      onNewResearch={handleNewResearch}
      onClearHistory={clearHistory}
    >
      {/* View 1: New Research Prompt */}
      {currentRunId === null && (
        <div className="py-4">
          <ResearchInput
            onSubmit={handleStartResearch}
            isLoading={createMutation.isPending}
          />
        </div>
      )}

      {/* View 2: Active Run Loading Initial State */}
      {currentRunId !== null && isRunLoading && !runData && (
        <div className="max-w-4xl mx-auto space-y-6 py-4">
          <Card className="p-6 space-y-4">
            <Skeleton className="h-6 w-32" />
            <Skeleton className="h-8 w-3/4" />
            <div className="space-y-3 pt-4">
              <Skeleton className="h-16 w-full rounded-xl" />
              <Skeleton className="h-16 w-full rounded-xl" />
            </div>
          </Card>
        </div>
      )}

      {/* View 3: Query Error (404, Network, or Server Error) */}
      {currentRunId !== null && isRunError && (
        <div className="max-w-2xl mx-auto py-12">
          {runError?.statusCode === 404 ? (
            <Card className="p-8 text-center space-y-4 border-zinc-200 dark:border-zinc-800">
              <div className="w-12 h-12 rounded-full bg-zinc-100 dark:bg-zinc-800 text-zinc-500 mx-auto flex items-center justify-center">
                <AlertCircle className="w-6 h-6" />
              </div>
              <div className="space-y-1">
                <h3 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
                  Research Run #{currentRunId} Not Found
                </h3>
                <p className="text-sm text-zinc-500 max-w-sm mx-auto">
                  The requested run does not exist or has expired. You can start a new research session.
                </p>
              </div>
              <Button
                variant="primary"
                size="sm"
                onClick={handleNewResearch}
                leftIcon={<ArrowLeft className="w-4 h-4" />}
              >
                Back to Workspace
              </Button>
            </Card>
          ) : (
            <FailedState
              onRetry={() => setCurrentRunId(currentRunId)}
              onBackToNew={handleNewResearch}
            />
          )}
        </div>
      )}

      {/* View 4: Run Active / In Progress */}
      {currentRunId !== null && runData && runData.status === 'running' && (
        <ResearchProgress run={runData} />
      )}

      {/* View 5: Terminal Finished States (Approved, Partial, Insufficient Evidence) */}
      {currentRunId !== null && runData && (runData.status === 'approved' || runData.status === 'partial' || runData.status === 'insufficient_evidence') && (
        <ReportView run={runData} onNewResearch={handleNewResearch} />
      )}

      {/* View 6: Run Failed State */}
      {currentRunId !== null && runData && runData.status === 'failed' && (
        <FailedState
          topic={runData.topic}
          onRetry={() => handleStartResearch(runData.topic)}
          onBackToNew={handleNewResearch}
        />
      )}
    </AppShell>
  );
};
