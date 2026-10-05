import React from 'react';
import { Terminal, Shield, Zap } from 'lucide-react';
import { getApiBaseUrl } from '../../api/client';
import { useHealthQuery } from '../../hooks/useResearch';

export const StatusBar: React.FC = () => {
  const { data: health, isSuccess } = useHealthQuery();

  return (
    <footer className="h-7 border-t border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-950 px-4 flex items-center justify-between text-[11px] text-zinc-500 dark:text-zinc-400 font-mono select-none">
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1.5">
          <Terminal className="w-3 h-3 text-zinc-400" />
          <span>API:</span>
          <span className="text-zinc-700 dark:text-zinc-300 truncate max-w-[200px] sm:max-w-xs">
            {getApiBaseUrl()}
          </span>
        </div>
        {isSuccess && (
          <span className="hidden sm:inline-flex items-center gap-1 px-1.5 py-0.2 rounded-sm bg-zinc-200/60 dark:bg-zinc-800 text-[10px] text-zinc-600 dark:text-zinc-300">
            env: {health.env}
          </span>
        )}
      </div>

      <div className="flex items-center gap-4">
        <div className="hidden md:flex items-center gap-1">
          <Zap className="w-3 h-3 text-indigo-500" />
          <span>bge-small-en-v1.5 + Llama-3.1-8k</span>
        </div>
        <div className="flex items-center gap-1">
          <Shield className="w-3 h-3 text-emerald-500" />
          <span>Calibrated 0.255 Cutoff</span>
        </div>
      </div>
    </footer>
  );
};
