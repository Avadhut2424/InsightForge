import React from 'react';
import { AlertCircle, RotateCcw, ArrowLeft } from 'lucide-react';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';

interface FailedStateProps {
  topic?: string;
  onRetry?: () => void;
  onBackToNew?: () => void;
}

export const FailedState: React.FC<FailedStateProps> = ({ topic, onRetry, onBackToNew }) => {
  return (
    <Card className="max-w-2xl mx-auto p-8 border-rose-200/60 dark:border-rose-900/40 bg-rose-50/10 dark:bg-rose-950/10 text-center space-y-5">
      <div className="w-12 h-12 rounded-full bg-rose-500/10 text-rose-600 dark:text-rose-400 mx-auto flex items-center justify-center">
        <AlertCircle className="w-6 h-6 stroke-[2.2]" />
      </div>

      <div className="space-y-2">
        <h3 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
          Research Execution Failed
        </h3>
        <p className="text-sm text-zinc-600 dark:text-zinc-400 max-w-md mx-auto leading-relaxed">
          InsightForge could not complete this research run. The orchestrator halted gracefully to protect state integrity.
        </p>
        {topic && (
          <p className="text-xs font-mono text-zinc-500 dark:text-zinc-400 bg-zinc-100 dark:bg-zinc-800/80 py-1.5 px-3 rounded-md max-w-lg mx-auto truncate">
            Topic: {topic}
          </p>
        )}
      </div>

      <div className="flex items-center justify-center gap-3 pt-2">
        {onBackToNew && (
          <Button variant="outline" size="sm" onClick={onBackToNew} leftIcon={<ArrowLeft className="w-4 h-4" />}>
            New Research
          </Button>
        )}
        {onRetry && (
          <Button variant="primary" size="sm" onClick={onRetry} leftIcon={<RotateCcw className="w-4 h-4" />}>
            Try Again
          </Button>
        )}
      </div>
    </Card>
  );
};
