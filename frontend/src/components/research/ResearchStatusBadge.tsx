import React from 'react';
import { CheckCircle2, AlertTriangle, HelpCircle, XCircle, Loader2 } from 'lucide-react';
import { Badge } from '../ui/Badge';
import type { ResearchRunStatus } from '../../api/types';

interface ResearchStatusBadgeProps {
  status: ResearchRunStatus;
  size?: 'sm' | 'md';
}

export const ResearchStatusBadge: React.FC<ResearchStatusBadgeProps> = ({ status, size = 'md' }) => {
  switch (status) {
    case 'approved':
      return (
        <Badge variant="emerald" size={size} dot>
          <CheckCircle2 className="w-3.5 h-3.5 mr-0.5 shrink-0" />
          <span>Approved</span>
        </Badge>
      );
    case 'partial':
      return (
        <Badge variant="amber" size={size} dot>
          <AlertTriangle className="w-3.5 h-3.5 mr-0.5 shrink-0" />
          <span>Partial</span>
        </Badge>
      );
    case 'insufficient_evidence':
      return (
        <Badge variant="neutral" size={size} dot>
          <HelpCircle className="w-3.5 h-3.5 mr-0.5 shrink-0" />
          <span>Insufficient Evidence</span>
        </Badge>
      );
    case 'failed':
      return (
        <Badge variant="rose" size={size} dot>
          <XCircle className="w-3.5 h-3.5 mr-0.5 shrink-0" />
          <span>Failed</span>
        </Badge>
      );
    case 'running':
    default:
      return (
        <Badge variant="indigo" size={size}>
          <Loader2 className="w-3.5 h-3.5 animate-spin mr-0.5 shrink-0" />
          <span>Running</span>
        </Badge>
      );
  }
};
