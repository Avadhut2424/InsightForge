import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import { ResearchStatusBadge } from '../components/research/ResearchStatusBadge';
import { RevisionBadge } from '../components/research/RevisionBadge';
import { CitationCard } from '../components/research/CitationCard';
import { ReportSection } from '../components/research/ReportSection';

describe('UI & Research Components', () => {
  describe('ResearchStatusBadge', () => {
    it('renders Approved status with emerald badge', () => {
      render(<ResearchStatusBadge status="approved" />);
      expect(screen.getByText('Approved')).toBeInTheDocument();
    });

    it('renders Partial status with amber badge', () => {
      render(<ResearchStatusBadge status="partial" />);
      expect(screen.getByText('Partial')).toBeInTheDocument();
    });

    it('renders Insufficient Evidence status', () => {
      render(<ResearchStatusBadge status="insufficient_evidence" />);
      expect(screen.getByText('Insufficient Evidence')).toBeInTheDocument();
    });

    it('renders Failed status with rose badge', () => {
      render(<ResearchStatusBadge status="failed" />);
      expect(screen.getByText('Failed')).toBeInTheDocument();
    });

    it('renders Running status with spinner', () => {
      render(<ResearchStatusBadge status="running" />);
      expect(screen.getByText('Running')).toBeInTheDocument();
    });
  });

  describe('RevisionBadge', () => {
    it('shows verified on first pass when revision count is 0', () => {
      render(<RevisionBadge revisionCount={0} status="approved" />);
      expect(screen.getByText('Verified on first pass')).toBeInTheDocument();
    });

    it('shows verified after revision when count > 0', () => {
      render(<RevisionBadge revisionCount={2} status="approved" />);
      expect(screen.getByText('Verified after revision (2)')).toBeInTheDocument();
    });

    it('shows cap reached when unverified', () => {
      render(<RevisionBadge revisionCount={1} status="unverified" />);
      expect(screen.getByText(/Revision cap reached/)).toBeInTheDocument();
    });

    it('shows evidence insufficient when status is insufficient_evidence', () => {
      render(<RevisionBadge revisionCount={0} status="insufficient_evidence" />);
      expect(screen.getByText('Evidence insufficient')).toBeInTheDocument();
    });
  });

  describe('CitationCard', () => {
    it('renders citation index, title, and verbatim sentence quote', () => {
      render(
        <CitationCard
          index={1}
          citation={{
            citation: 'ArXiv:2305.12345 - Patterson et al.',
            sentence: 'Data center electricity consumption reached 415 TWh.',
          }}
        />
      );

      expect(screen.getByText('[1]')).toBeInTheDocument();
      expect(screen.getByText('ArXiv:2305.12345 - Patterson et al.')).toBeInTheDocument();
      expect(screen.getByText(/"Data center electricity consumption reached 415 TWh."/)).toBeInTheDocument();
    });
  });

  describe('ReportSection', () => {
    it('renders section title, assembled text, and critic verification', () => {
      render(
        <ReportSection
          index={1}
          title="What are the power requirements of large LLMs?"
          data={{
            assembled_text: 'Training modern LLMs demands gigawatt-scale infrastructure.',
            revision_count: 0,
            status: 'approved',
            verdict: 'approve',
            reason: 'Section covers all prompt criteria.',
            draft: [
              {
                citation: 'Wikipedia - Supercomputing',
                sentence: 'Training modern LLMs demands gigawatt-scale infrastructure.',
              },
            ],
          }}
        />
      );

      expect(screen.getByText('Section 1')).toBeInTheDocument();
      expect(screen.getByText('What are the power requirements of large LLMs?')).toBeInTheDocument();
      expect(screen.getByText('Training modern LLMs demands gigawatt-scale infrastructure.')).toBeInTheDocument();
      expect(screen.getByText('Critic Verification')).toBeInTheDocument();
      expect(screen.getByText('Section covers all prompt criteria.')).toBeInTheDocument();
    });
  });
});
