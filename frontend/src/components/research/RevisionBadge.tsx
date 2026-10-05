import React from 'react';
import { RefreshCw, Check, AlertCircle } from 'lucide-react';
import type { SectionStatus } from '../../api/types';

interface RevisionBadgeProps {
  revisionCount: number;
  status: SectionStatus;
  className?: string;
}

export const RevisionBadge: React.FC<RevisionBadgeProps> = ({ revisionCount, status, className = '' }) => {
  if (status === 'insufficient_evidence') {
    return (
      <span className={`inline-flex items-center gap-1 text-xs font-medium text-zinc-500 dark:text-zinc-400 bg-zinc-100 dark:bg-zinc-800 px-2 py-0.5 rounded-full ${className}`}>
        <AlertCircle className="w-3 h-3 text-zinc-400" />
        Evidence insufficient
      </span>
    );
  }

  if (status === 'unverified') {
    return (
      <span className={`inline-flex items-center gap-1 text-xs font-medium text-amber-600 dark:text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded-full border border-amber-500/20 ${className}`}>
        <RefreshCw className="w-3 h-3 text-amber-500" />
        Revision cap reached ({revisionCount} rev{revisionCount === 1 ? '' : 's'})
      </span>
    );
  }

  if (revisionCount > 0) {
    return (
      <span className={`inline-flex items-center gap-1 text-xs font-medium text-amber-700 dark:text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded-full border border-amber-500/20 ${className}`}>
        <RefreshCw className="w-3 h-3 text-amber-500" />
        Verified after revision ({revisionCount})
      </span>
    );
  }

  return (
    <span className={`inline-flex items-center gap-1 text-xs font-medium text-emerald-700 dark:text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20 ${className}`}>
      <Check className="w-3 h-3 text-emerald-500" />
      Verified on first pass
    </span>
  );
};
