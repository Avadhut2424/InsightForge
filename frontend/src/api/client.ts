/**
 * Typed API Client for InsightForge AI
 * Gracefully handles network failures, validation messages, and sanitizes backend errors.
 */

import type { ApiErrorResponse } from './types';

export class ApiError extends Error {
  public statusCode: number;
  public detail: string;

  constructor(statusCode: number, detail: string) {
    super(detail);
    this.name = 'ApiError';
    this.statusCode = statusCode;
    this.detail = detail;
  }
}

// In Vite dev, empty string or undefined will default to relative URLs which Vite proxies.
// In direct mode or custom deployment, VITE_API_BASE_URL can point to http://localhost:8000.
const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '');

export async function apiClient<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;

  const defaultHeaders: Record<string, string> = {
    'Accept': 'application/json',
  };

  if (options.body && typeof options.body === 'string') {
    defaultHeaders['Content-Type'] = 'application/json';
  }

  let response: Response;
  try {
    response = await fetch(url, {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers,
      },
    });
  } catch {
    throw new ApiError(0, 'Unable to connect to InsightForge. Please ensure the backend server is running.');
  }

  if (!response.ok) {
    let errorDetail = 'An unexpected error occurred during research execution.';

    try {
      const errorJson = (await response.json()) as ApiErrorResponse;
      if (errorJson && typeof errorJson.detail === 'string') {
        errorDetail = errorJson.detail;
      }
    } catch {
      // Fallback for non-JSON or proxy error responses
      if (response.status === 404) {
        errorDetail = 'Research run not found.';
      } else if (response.status === 500) {
        errorDetail = 'InsightForge could not complete this research run.';
      } else if (response.status === 502 || response.status === 503) {
        errorDetail = 'Research service is currently unavailable.';
      }
    }

    throw new ApiError(response.status, errorDetail);
  }

  return response.json() as Promise<T>;
}

export function getApiBaseUrl(): string {
  return API_BASE_URL || (typeof window !== 'undefined' ? `${window.location.origin} (Vite Proxy -> http://localhost:8000)` : 'http://localhost:8000');
}
