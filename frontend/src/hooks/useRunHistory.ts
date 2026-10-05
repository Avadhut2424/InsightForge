import { useState, useEffect, useCallback } from 'react';
import type { RunHistoryItem, ResearchRunStatus } from '../api/types';

const STORAGE_KEY = 'insightforge_recent_runs';
const MAX_HISTORY_ITEMS = 25;

export function useRunHistory() {
  const [runs, setRuns] = useState<RunHistoryItem[]>(() => {
    if (typeof window === 'undefined') return [];
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      return stored ? JSON.parse(stored) : [];
    } catch {
      return [];
    }
  });

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(runs));
    } catch {
      // Ignore local storage quota limits
    }
  }, [runs]);

  const addOrUpdateRun = useCallback((item: Partial<RunHistoryItem> & { runId: number }) => {
    setRuns((prev) => {
      const existingIndex = prev.findIndex((r) => r.runId === item.runId);
      if (existingIndex >= 0) {
        const updated = [...prev];
        updated[existingIndex] = {
          ...updated[existingIndex],
          ...item,
        } as RunHistoryItem;
        return updated;
      }

      const newItem: RunHistoryItem = {
        runId: item.runId,
        topic: item.topic || 'Untitled Research',
        status: item.status || 'running',
        startedAt: item.startedAt || new Date().toISOString(),
        completedAt: item.completedAt || null,
      };

      return [newItem, ...prev].slice(0, MAX_HISTORY_ITEMS);
    });
  }, []);

  const updateRunStatus = useCallback((runId: number, status: ResearchRunStatus, completedAt?: string | null) => {
    setRuns((prev) =>
      prev.map((r) =>
        r.runId === runId
          ? { ...r, status, completedAt: completedAt ?? (status !== 'running' ? new Date().toISOString() : r.completedAt) }
          : r
      )
    );
  }, []);

  const removeRun = useCallback((runId: number) => {
    setRuns((prev) => prev.filter((r) => r.runId !== runId));
  }, []);

  const clearHistory = useCallback(() => {
    setRuns([]);
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch {
      // Ignore
    }
  }, []);

  return {
    runs,
    addOrUpdateRun,
    updateRunStatus,
    removeRun,
    clearHistory,
  };
}
