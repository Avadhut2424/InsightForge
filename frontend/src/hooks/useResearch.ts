import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { researchApi } from '../api/research';
import { ApiError } from '../api/client';
import type { ResearchRunResponse, HealthResponse, ResearchCreateResponse } from '../api/types';

/**
 * Hook to monitor backend health
 */
export function useHealthQuery() {
  return useQuery<HealthResponse, ApiError>({
    queryKey: ['health'],
    queryFn: () => researchApi.getHealth(),
    refetchInterval: 25000,
    retry: 1,
    staleTime: 10000,
  });
}

/**
 * Hook to poll and fetch a specific research run
 * Automatically polls every 3 seconds only while run is 'running'
 * Stops immediately upon reaching terminal state (approved, partial, insufficient_evidence, failed)
 */
export function useResearchRunQuery(runId: number | null, onRunUpdated?: (run: ResearchRunResponse) => void) {
  return useQuery<ResearchRunResponse, ApiError>({
    queryKey: ['researchRun', runId],
    queryFn: async () => {
      if (runId === null) {
        throw new Error('Run ID is null');
      }
      const data = await researchApi.getRun(runId);
      if (onRunUpdated) {
        onRunUpdated(data);
      }
      return data;
    },
    enabled: typeof runId === 'number' && runId > 0,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (!data) return 3000;
      // Stop polling on terminal states
      return data.status === 'running' ? 3000 : false;
    },
    refetchIntervalInBackground: false,
    retry: (failureCount, error) => {
      if (error instanceof ApiError && (error.statusCode === 404 || error.statusCode === 500)) {
        return false;
      }
      return failureCount < 2;
    },
  });
}

/**
 * Hook to initiate research runs
 */
export function useCreateResearchMutation() {
  const queryClient = useQueryClient();

  return useMutation<ResearchCreateResponse, ApiError, string>({
    mutationFn: (topic: string) => researchApi.createRun(topic),
    onSuccess: (data) => {
      // Invalidate or pre-populate the run query
      queryClient.invalidateQueries({ queryKey: ['researchRun', data.run_id] });
    },
  });
}
