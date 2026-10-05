import React, { useState } from 'react';
import { Database, ChevronDown, ChevronUp } from 'lucide-react';
import { CitationCard } from './CitationCard';
import type { SentenceCitation } from '../../api/types';

interface EvidenceDrawerProps {
  citations: SentenceCitation[];
  highlightedIndex?: number | null;
  onSelectCitation?: (index: number) => void;
}

export const EvidenceDrawer: React.FC<EvidenceDrawerProps> = ({
  citations,
  highlightedIndex,
  onSelectCitation,
}) => {
  const [isOpen, setIsOpen] = useState<boolean>(true);

  if (!citations || citations.length === 0) {
    return null;
  }

  return (
    <div className="mt-4 border border-zinc-200 dark:border-zinc-800 rounded-xl overflow-hidden bg-zinc-50/40 dark:bg-zinc-900/30">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-4 py-3 flex items-center justify-between gap-3 text-left hover:bg-zinc-100/50 dark:hover:bg-zinc-800/40 transition-colors"
      >
        <div className="flex items-center gap-2 text-xs font-semibold text-zinc-800 dark:text-zinc-200">
          <Database className="w-3.5 h-3.5 text-indigo-500" />
          <span>Grounded Evidence & Source Citations</span>
          <span className="px-2 py-0.5 rounded-full bg-zinc-200/80 dark:bg-zinc-800 text-[11px] font-mono text-zinc-600 dark:text-zinc-400">
            {citations.length} chunk{citations.length === 1 ? '' : 's'}
          </span>
        </div>

        <div className="flex items-center gap-1 text-xs text-zinc-500">
          <span>{isOpen ? 'Collapse' : 'Expand'}</span>
          {isOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </div>
      </button>

      {isOpen && (
        <div className="p-4 pt-1 border-t border-zinc-200 dark:border-zinc-800 space-y-2.5">
          <p className="text-[11px] text-zinc-500 dark:text-zinc-400 pb-1">
            Every sentence in the synthesis pass is matched verbatim against retrieved knowledge base chunks.
          </p>
          <div className="grid grid-cols-1 gap-2.5">
            {citations.map((item, idx) => (
              <CitationCard
                key={`${item.citation}-${idx}`}
                index={idx + 1}
                citation={item}
                isActive={highlightedIndex === idx}
                onClick={() => onSelectCitation && onSelectCitation(idx)}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
