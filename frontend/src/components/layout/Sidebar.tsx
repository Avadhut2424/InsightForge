import React, { useState } from 'react';
import { PlusCircle, History, Search, Trash2, ArrowUpRight, Database } from 'lucide-react';
import { Button } from '../ui/Button';
import { ResearchStatusBadge } from '../research/ResearchStatusBadge';
import { formatRelativeTime } from '../../lib/formatting';
import type { RunHistoryItem } from '../../api/types';

interface SidebarProps {
  runs: RunHistoryItem[];
  currentRunId: number | null;
  onSelectRun: (runId: number) => void;
  onNewResearch: () => void;
  onClearHistory: () => void;
  isOpen?: boolean;
  onClose?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  runs,
  currentRunId,
  onSelectRun,
  onNewResearch,
  onClearHistory,
  isOpen = false,
  onClose,
}) => {
  const [lookupId, setLookupId] = useState<string>('');

  const handleLookup = (e: React.FormEvent) => {
    e.preventDefault();
    const id = parseInt(lookupId.trim(), 10);
    if (!isNaN(id) && id > 0) {
      onSelectRun(id);
      setLookupId('');
      if (onClose) onClose();
    }
  };

  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div
          onClick={onClose}
          className="fixed inset-0 bg-zinc-950/40 backdrop-blur-xs z-40 md:hidden"
        />
      )}

      {/* Sidebar Panel */}
      <aside
        className={`fixed md:sticky top-14 left-0 z-40 h-[calc(100vh-3.5rem)] w-72 shrink-0 border-r border-zinc-200 dark:border-zinc-800 bg-zinc-50/60 dark:bg-zinc-950/60 backdrop-blur-md flex flex-col transition-transform duration-200 ease-in-out md:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Top Action: New Research */}
        <div className="p-3.5 border-b border-zinc-200/80 dark:border-zinc-800 space-y-3">
          <Button
            variant="primary"
            size="md"
            onClick={() => {
              onNewResearch();
              if (onClose) onClose();
            }}
            leftIcon={<PlusCircle className="w-4 h-4" />}
            className="w-full justify-center shadow-xs"
          >
            New Research
          </Button>

          {/* Quick Run ID Search */}
          <form onSubmit={handleLookup} className="relative">
            <input
              type="number"
              min="1"
              value={lookupId}
              onChange={(e) => setLookupId(e.target.value)}
              placeholder="Jump to Run #..."
              className="w-full text-xs py-1.5 pl-7 pr-7 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 focus:outline-none focus:ring-1 focus:ring-indigo-500 font-mono"
            />
            <Search className="w-3.5 h-3.5 text-zinc-400 absolute left-2 top-2.5 pointer-events-none" />
            {lookupId && (
              <button
                type="submit"
                className="absolute right-1.5 top-1.5 p-0.5 rounded text-zinc-400 hover:text-indigo-600 dark:hover:text-indigo-400"
              >
                <ArrowUpRight className="w-3.5 h-3.5" />
              </button>
            )}
          </form>
        </div>

        {/* Section: Recent Runs */}
        <div className="flex-1 overflow-y-auto p-3 space-y-1">
          <div className="flex items-center justify-between px-2 py-1 text-xs font-mono uppercase tracking-wider text-zinc-400 dark:text-zinc-500">
            <div className="flex items-center gap-1.5">
              <History className="w-3.5 h-3.5" />
              <span>Recent Runs</span>
            </div>
            {runs.length > 0 && (
              <button
                type="button"
                onClick={onClearHistory}
                title="Clear local run history"
                className="p-1 hover:text-rose-600 dark:hover:text-rose-400 rounded transition-colors"
              >
                <Trash2 className="w-3 h-3" />
              </button>
            )}
          </div>

          {runs.length === 0 ? (
            <div className="p-4 text-center space-y-1 text-xs text-zinc-400 dark:text-zinc-500">
              <p>No recent runs recorded.</p>
              <p className="text-[11px] text-zinc-400/80">Submit a topic or search an existing run ID above.</p>
            </div>
          ) : (
            <div className="space-y-1 pt-1">
              {runs.map((item) => {
                const isSelected = currentRunId === item.runId;
                return (
                  <button
                    key={item.runId}
                    type="button"
                    onClick={() => {
                      onSelectRun(item.runId);
                      if (onClose) onClose();
                    }}
                    className={`w-full text-left p-2.5 rounded-lg border transition-all duration-150 ${
                      isSelected
                        ? 'bg-indigo-50/70 dark:bg-indigo-950/40 border-indigo-200 dark:border-indigo-800 shadow-xs'
                        : 'border-transparent hover:bg-zinc-100/70 dark:hover:bg-zinc-900/60'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-1.5 mb-1">
                      <span className="text-[11px] font-mono font-medium text-zinc-500">
                        #{item.runId}
                      </span>
                      <ResearchStatusBadge status={item.status} size="sm" />
                    </div>
                    <p className="text-xs font-medium text-zinc-800 dark:text-zinc-200 line-clamp-2 leading-snug">
                      {item.topic}
                    </p>
                    <span className="block text-[10px] text-zinc-400 dark:text-zinc-500 mt-1 font-mono">
                      {formatRelativeTime(item.startedAt)}
                    </span>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Bottom Client Storage Notice */}
        <div className="p-3 border-t border-zinc-200/80 dark:border-zinc-800 bg-zinc-100/40 dark:bg-zinc-900/40 text-[11px] text-zinc-500 dark:text-zinc-400 flex items-start gap-2">
          <Database className="w-3.5 h-3.5 text-zinc-400 shrink-0 mt-0.5" />
          <p className="leading-tight">
            Single-run queries supported. Recent runs persist in browser local storage.
          </p>
        </div>
      </aside>
    </>
  );
};
