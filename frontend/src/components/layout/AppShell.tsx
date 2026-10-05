import React, { useState } from 'react';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { StatusBar } from './StatusBar';
import type { RunHistoryItem } from '../../api/types';

interface AppShellProps {
  runs: RunHistoryItem[];
  currentRunId: number | null;
  onSelectRun: (runId: number) => void;
  onNewResearch: () => void;
  onClearHistory: () => void;
  children: React.ReactNode;
}

export const AppShell: React.FC<AppShellProps> = ({
  runs,
  currentRunId,
  onSelectRun,
  onNewResearch,
  onClearHistory,
  children,
}) => {
  const [isSidebarOpen, setIsSidebarOpen] = useState<boolean>(false);

  return (
    <div className="min-h-screen flex flex-col bg-white dark:bg-zinc-950 text-zinc-900 dark:text-zinc-100 font-sans selection:bg-indigo-500/20 selection:text-indigo-600">
      <Header
        onToggleSidebar={() => setIsSidebarOpen((prev) => !prev)}
        isSidebarOpen={isSidebarOpen}
      />

      <div className="flex-1 flex overflow-hidden">
        <Sidebar
          runs={runs}
          currentRunId={currentRunId}
          onSelectRun={onSelectRun}
          onNewResearch={onNewResearch}
          onClearHistory={onClearHistory}
          isOpen={isSidebarOpen}
          onClose={() => setIsSidebarOpen(false)}
        />

        <main className="flex-1 overflow-y-auto px-4 sm:px-6 py-6 sm:py-8">
          {children}
        </main>
      </div>

      <StatusBar />
    </div>
  );
};
