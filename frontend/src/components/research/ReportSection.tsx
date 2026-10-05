import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { HelpCircle } from 'lucide-react';
import { Card } from '../ui/Card';
import { RevisionBadge } from './RevisionBadge';
import { CriticResult } from './CriticResult';
import { EvidenceDrawer } from './EvidenceDrawer';
import type { SectionData } from '../../api/types';

interface ReportSectionProps {
  index: number;
  title: string;
  data: SectionData;
}

export const ReportSection: React.FC<ReportSectionProps> = ({ index, title, data }) => {
  const [highlightedCitation, setHighlightedCitation] = useState<number | null>(null);

  const isInsufficient = data.status === 'insufficient_evidence';

  return (
    <Card className="p-6 sm:p-7 space-y-5 border-zinc-200/90 dark:border-zinc-800">
      {/* Section Header */}
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3 pb-3 border-b border-zinc-100 dark:border-zinc-800/80">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono font-semibold text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-950/40 px-2 py-0.5 rounded-sm">
              Section {index}
            </span>
            <RevisionBadge revisionCount={data.revision_count} status={data.status} />
          </div>
          <h3 className="text-base sm:text-lg font-semibold text-zinc-900 dark:text-zinc-100 pt-1 leading-snug">
            {title}
          </h3>
        </div>
      </div>

      {/* Insufficient Evidence Notice */}
      {isInsufficient && (
        <div className="p-4 rounded-xl bg-amber-50/60 dark:bg-amber-950/20 border border-amber-200/60 dark:border-amber-800/50 flex items-start gap-3">
          <HelpCircle className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
          <div className="space-y-1 text-xs">
            <p className="font-semibold text-amber-900 dark:text-amber-200">
              Insufficient Grounded Evidence
            </p>
            <p className="text-amber-800/80 dark:text-amber-300/80 leading-relaxed">
              No chunks in the local knowledge base met the calibrated similarity threshold (0.255 cosine distance) for this sub-question. InsightForge halts synthesis honestly rather than hallucinating an unsupported answer.
            </p>
          </div>
        </div>
      )}

      {/* Assembled Content */}
      {data.assembled_text && (
        <div className="prose prose-zinc dark:prose-invert max-w-none text-sm text-zinc-700 dark:text-zinc-300 leading-relaxed">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {data.assembled_text}
          </ReactMarkdown>
        </div>
      )}

      {/* Critic Verification Details */}
      <CriticResult
        verdict={data.verdict}
        reason={data.reason}
        revisionCount={data.revision_count}
      />

      {/* Grounded Evidence Drawer */}
      {data.draft && data.draft.length > 0 && (
        <EvidenceDrawer
          citations={data.draft}
          highlightedIndex={highlightedCitation}
          onSelectCitation={(idx) => setHighlightedCitation(idx)}
        />
      )}
    </Card>
  );
};
