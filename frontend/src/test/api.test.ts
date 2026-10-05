import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { researchApi } from '../api/research';
import { ApiError } from '../api/client';
import type { ResearchRunResponse } from '../api/types';

describe('Research API client', () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    global.fetch = originalFetch;
  });

  it('creates research run successfully on 202 Accepted', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 202,
      json: async () => ({ run_id: 42, status: 'running' }),
    });

    const res = await researchApi.createRun('Valid topic test query');
    expect(res.run_id).toBe(42);
    expect(res.status).toBe('running');
  });

  it('handles 400 Bad Request with backend validation message', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 400,
      json: async () => ({ detail: 'Topic is too short. Minimum length is 3 characters.' }),
    });

    await expect(researchApi.createRun('ab')).rejects.toThrow(ApiError);
    try {
      await researchApi.createRun('ab');
    } catch (e: unknown) {
      const err = e as ApiError;
      expect(err.statusCode).toBe(400);
      expect(err.detail).toContain('too short');
    }
  });

  it('handles 404 Not Found error gracefully', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      json: async () => ({ detail: 'Research run 999 not found.' }),
    });

    await expect(researchApi.getRun(999)).rejects.toThrow(ApiError);
    try {
      await researchApi.getRun(999);
    } catch (e: unknown) {
      const err = e as ApiError;
      expect(err.statusCode).toBe(404);
      expect(err.detail).toContain('not found');
    }
  });

  it('handles 500 Internal Service Error without exposing stack trace', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      json: async () => ({ detail: 'Research execution failed due to an internal service error.' }),
    });

    try {
      await researchApi.getRun(5);
    } catch (e: unknown) {
      const err = e as ApiError;
      expect(err.statusCode).toBe(500);
      expect(err.detail).toContain('internal service error');
    }
  });

  it('handles network failure when backend is down', async () => {
    global.fetch = vi.fn().mockRejectedValue(new TypeError('Failed to fetch'));

    try {
      await researchApi.getRun(1);
    } catch (e: unknown) {
      const err = e as ApiError;
      expect(err.statusCode).toBe(0);
      expect(err.detail).toContain('Unable to connect to InsightForge');
    }
  });

  it('fetches completed approved run payload correctly', async () => {
    const mockApproved: ResearchRunResponse = {
      run_id: 1,
      topic: 'AI computing energy consumption',
      status: 'approved',
      started_at: '2026-10-04T10:00:00Z',
      completed_at: '2026-10-04T10:02:00Z',
      summary: {
        total_sub_questions: 1,
        approved_sections: 1,
        unverified_sections: 0,
        insufficient_evidence_sections: 0,
        total_revisions: 0,
      },
      sections: {
        'What is data center power use?': {
          draft: [{ citation: 'ArXiv', sentence: 'Consumes 415 TWh.' }],
          assembled_text: 'Data centers consume 415 TWh electricity.',
          verdict: 'approve',
          reason: 'Fully supported.',
          revision_count: 0,
          status: 'approved',
        },
      },
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockApproved,
    });

    const res = await researchApi.getRun(1);
    expect(res.status).toBe('approved');
    expect(res.sections?.['What is data center power use?'].verdict).toBe('approve');
  });
});
