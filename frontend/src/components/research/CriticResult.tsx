import React from 'react';
import { ShieldCheck, ShieldAlert, Sparkles } from 'lucide-react';
import { Card } from '../ui/Card';
import type { SectionVerdict } from '../../api/types';

interface CriticResultProps {
  verdict?: SectionVerdict | null;
  reason?: string | null;
  revisionCount: number;
}

export const CriticResult: React.FC<CriticResultProps> = ({ verdict, reason, revisionCount }) => {
  if (!verdict && !reason && revisionCount === 0) {
    return null;
  }

  const isApproved = verdict === 'approve';

  return (
    <Card className="p-4 bg-zinc-50/50 dark:bg-zinc-900/40 border-zinc-200/80 dark:border-zinc-800 space-y-2">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          {isApproved ? (
            <ShieldCheck className="w-4 h-4 text-emerald-500 shrink-0" />
          ) : (
            <ShieldAlert className="w-4 h-4 text-amber-500 shrink-0" />
          )}
          <span className="text-xs font-semibold text-zinc-800 dark:text-zinc-200">
            Critic Verification
          </span>
          <span className="text-[11px] font-mono text-zinc-400">
            (verdict: {verdict || 'evaluated'})
          </span>
        </div>

        {revisionCount > 0 && (
          <span className="text-[11px] font-medium text-amber-600 dark:text-amber-400">
            {revisionCount} revision cycle{revisionCount === 1 ? '' : 's'}
          </span>
        )}
      </div>

      {reason ? (
        <div className="flex items-start gap-2 text-xs text-zinc-600 dark:text-zinc-400 bg-white/70 dark:bg-zinc-950/40 p-2.5 rounded-lg border border-zinc-200/50 dark:border-zinc-800/50">
          <Sparkles className="w-3.5 h-3.5 text-indigo-500 shrink-0 mt-0.5" />
          <p className="leading-relaxed">{reason}</p>
        </div>
      ) : (
        <p className="text-xs text-zinc-500 dark:text-zinc-400 italic">
          Section verified against retrieved vector evidence and sub-question criteria.
        </p>
      )}
    </Card>
  );
};
