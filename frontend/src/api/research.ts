/**
 * Research API methods corresponding to the FastAPI backend endpoints
 */

import { apiClient } from './client';
import type { 
  ResearchCreateRequest, 
  ResearchCreateResponse, 
  ResearchRunResponse,
  HealthResponse 
} from './types';

export const researchApi = {
  /**
   * Health check endpoint: GET /health
   */
  async getHealth(): Promise<HealthResponse> {
    return apiClient<HealthResponse>('/health', { method: 'GET' });
  },

  /**
   * Initiates a new research run: POST /research
   * Topic must be 3-500 characters
   */
  async createRun(topic: string): Promise<ResearchCreateResponse> {
    const payload: ResearchCreateRequest = { topic: topic.trim() };
    return apiClient<ResearchCreateResponse>('/research', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  /**
   * Polls or fetches a research run: GET /research/{run_id}
   */
  async getRun(runId: number): Promise<ResearchRunResponse> {
    return apiClient<ResearchRunResponse>(`/research/${runId}`, {
      method: 'GET',
    });
  },
};
