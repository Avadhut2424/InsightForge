import React from 'react';
import { BookOpen, Quote } from 'lucide-react';
import { Card } from '../ui/Card';
import type { SentenceCitation } from '../../api/types';

interface CitationCardProps {
  index: number;
  citation: SentenceCitation;
  isActive?: boolean;
  onClick?: () => void;
}

export const CitationCard: React.FC<CitationCardProps> = ({
  index,
  citation,
  isActive = false,
  onClick,
}) => {
  return (
    <Card
      onClick={onClick}
      variant={isActive ? 'default' : 'muted'}
      className={`p-3.5 transition-all cursor-pointer border ${
        isActive
          ? 'border-indigo-500/50 bg-indigo-50/20 dark:bg-indigo-950/20 shadow-xs ring-1 ring-indigo-500/30'
          : 'hover:border-zinc-300 dark:hover:border-zinc-700'
      }`}
    >
      <div className="flex items-start gap-2.5">
        <span className="shrink-0 inline-flex items-center justify-center w-5 h-5 rounded-sm bg-zinc-200/80 dark:bg-zinc-800 text-[11px] font-mono font-medium text-zinc-700 dark:text-zinc-300">
          [{index}]
        </span>

        <div className="flex-1 min-w-0 space-y-1.5">
          <div className="flex items-center gap-1.5 text-xs font-medium text-zinc-800 dark:text-zinc-200">
            <BookOpen className="w-3.5 h-3.5 text-indigo-500 shrink-0" />
            <span className="truncate">{citation.citation || 'Knowledge Base Document'}</span>
          </div>

          <div className="flex items-start gap-1.5 text-xs text-zinc-600 dark:text-zinc-400 italic bg-white/60 dark:bg-zinc-950/40 p-2 rounded-md border border-zinc-200/50 dark:border-zinc-800/50">
            <Quote className="w-3 h-3 text-zinc-400 shrink-0 mt-0.5" />
            <span className="line-clamp-3 font-serif leading-relaxed">
              "{citation.sentence}"
            </span>
          </div>
        </div>
      </div>
    </Card>
  );
};
