/**
 * Strict TypeScript types for InsightForge AI
 * Grounded in FastAPI backend schemas from app/api/research.py and app/agents/graph/state.py
 */

export type ResearchRunStatus = 
  | 'running'
  | 'approved'
  | 'partial'
  | 'insufficient_evidence'
  | 'failed';

export type SectionStatus = 
  | 'pending'
  | 'synthesized'
  | 'approved'
  | 'unverified'
  | 'insufficient_evidence';

export type SectionVerdict = 'approve' | 'revise';

export interface SentenceCitation {
  sentence: string;
  citation: string;
}

export interface SectionData {
  draft?: SentenceCitation[];
  assembled_text?: string;
  verdict?: SectionVerdict | null;
  reason?: string | null;
  revision_count: number;
  status: SectionStatus;
}

export interface ResearchRunSummary {
  // Present during 'running'
  steps_completed?: number;
  revision_count?: number;

  // Present on terminal completion
  total_sub_questions?: number;
  approved_sections?: number;
  unverified_sections?: number;
  insufficient_evidence_sections?: number;
  total_revisions?: number;
}

export interface ResearchRunResponse {
  run_id: number;
  topic: string;
  status: ResearchRunStatus;
  started_at: string | null;
  completed_at?: string | null;
  summary?: ResearchRunSummary;
  sections?: Record<string, SectionData>;
  explanation?: string;
  report?: null; // Present as null during 'running'
}

export interface ResearchCreateRequest {
  topic: string;
}

export interface ResearchCreateResponse {
  run_id: number;
  status: 'running';
}

export interface ApiErrorResponse {
  detail: string;
}

export interface HealthResponse {
  status: string;
  env: string;
}

export interface RunHistoryItem {
  runId: number;
  topic: string;
  status: ResearchRunStatus;
  startedAt: string;
  completedAt?: string | null;
}
