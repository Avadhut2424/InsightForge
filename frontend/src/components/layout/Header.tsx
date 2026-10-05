import React from 'react';
import { Sun, Moon, Menu, X, Cpu } from 'lucide-react';
import { useTheme } from '../../context/useTheme';
import { useHealthQuery } from '../../hooks/useResearch';
import { Button } from '../ui/Button';

interface HeaderProps {
  onToggleSidebar?: () => void;
  isSidebarOpen?: boolean;
}

export const Header: React.FC<HeaderProps> = ({ onToggleSidebar, isSidebarOpen = false }) => {
  const { theme, toggleTheme } = useTheme();
  const { data: health, isSuccess, isLoading } = useHealthQuery();

  const isOnline = isSuccess && health?.status === 'ok';

  return (
    <header className="h-14 border-b border-zinc-200 dark:border-zinc-800 bg-white/80 dark:bg-zinc-950/80 backdrop-blur-md sticky top-0 z-30 px-4 flex items-center justify-between">
      {/* Left: Mobile menu toggle + Logo */}
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onToggleSidebar}
          className="md:hidden p-1.5 rounded-lg text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
          aria-label="Toggle Navigation Sidebar"
        >
          {isSidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>

        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-indigo-600 text-white flex items-center justify-center shadow-xs shadow-indigo-500/20">
            <Cpu className="w-4 h-4 stroke-[2.2]" />
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="font-semibold text-zinc-900 dark:text-zinc-100 tracking-tight text-sm sm:text-base">
              InsightForge
            </span>
            <span className="text-[11px] font-mono text-indigo-600 dark:text-indigo-400 font-medium">
              AI
            </span>
          </div>
        </div>
      </div>

      {/* Right: API Health Status + Theme Switcher */}
      <div className="flex items-center gap-2 sm:gap-3">
        {/* API Health Pill */}
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono border border-zinc-200 dark:border-zinc-800 bg-zinc-50/70 dark:bg-zinc-900/60">
          <span
            className={`w-2 h-2 rounded-full shrink-0 ${
              isLoading
                ? 'bg-amber-400 animate-pulse'
                : isOnline
                ? 'bg-emerald-500'
                : 'bg-rose-500'
            }`}
          />
          <span className="text-zinc-600 dark:text-zinc-300 text-[11px] font-medium hidden sm:inline">
            {isLoading ? 'Checking' : isOnline ? 'Backend Online' : 'Backend Offline'}
          </span>
        </div>

        {/* Theme Toggle */}
        <Button
          variant="ghost"
          size="sm"
          onClick={toggleTheme}
          aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
          className="p-2 text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100"
        >
          {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
        </Button>
      </div>
    </header>
  );
};
