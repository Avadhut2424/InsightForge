import React, { useState } from 'react';
import { Copy, Check, Printer, FileText, ArrowLeft, Layers, ShieldCheck, AlertTriangle, HelpCircle, RotateCw } from 'lucide-react';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { ResearchStatusBadge } from './ResearchStatusBadge';
import { ReportSection } from './ReportSection';
import { formatDateTime, formatDuration } from '../../lib/formatting';
import type { ResearchRunResponse } from '../../api/types';

interface ReportViewProps {
  run: ResearchRunResponse;
  onNewResearch?: () => void;
}

export const ReportView: React.FC<ReportViewProps> = ({ run, onNewResearch }) => {
  const [copied, setCopied] = useState<boolean>(false);

  const sections = run.sections ? Object.entries(run.sections) : [];
  const summary = run.summary;

  const copyMarkdownReport = () => {
    let md = `# Research Report: ${run.topic}\n\n`;
    md += `**Run ID:** #${run.run_id}  \n`;
    md += `**Status:** ${run.status.toUpperCase()}  \n`;
    md += `**Started:** ${formatDateTime(run.started_at)}  \n`;
    md += `**Completed:** ${formatDateTime(run.completed_at)}  \n\n`;

    if (run.explanation) {
      md += `> **System Assessment:** ${run.explanation}\n\n`;
    }

    if (summary) {
      md += `## Executive Summary\n\n`;
      md += `- Sub-questions Analyzed: ${summary.total_sub_questions ?? sections.length}\n`;
      md += `- Approved Sections: ${summary.approved_sections ?? 0}\n`;
      md += `- Unverified Sections: ${summary.unverified_sections ?? 0}\n`;
      md += `- Insufficient Evidence Sections: ${summary.insufficient_evidence_sections ?? 0}\n`;
      md += `- Total Revision Loops: ${summary.total_revisions ?? 0}\n\n`;
    }

    md += `## Synthesized Findings\n\n`;

    sections.forEach(([sq, sec], idx) => {
      md += `### ${idx + 1}. ${sq}\n\n`;
      md += `*Status: ${sec.status} | Revisions: ${sec.revision_count}*\n\n`;
      md += `${sec.assembled_text || '*(No text synthesized)*'}\n\n`;

      if (sec.draft && sec.draft.length > 0) {
        md += `#### Citations & Grounded Evidence\n\n`;
        sec.draft.forEach((item, cIdx) => {
          md += `[${cIdx + 1}] "${item.sentence}" — *${item.citation}*\n\n`;
        });
      }
    });

    navigator.clipboard.writeText(md);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="max-w-4xl mx-auto space-y-7 pb-16">
      {/* Top Header Card */}
      <Card className="p-6 sm:p-7 space-y-4 border-zinc-200/90 dark:border-zinc-800">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-zinc-100 dark:border-zinc-800">
          <div className="flex items-center gap-3">
            {onNewResearch && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onNewResearch}
                leftIcon={<ArrowLeft className="w-4 h-4" />}
                className="px-2"
              >
                Back
              </Button>
            )}
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono font-medium text-zinc-500">RUN #{run.run_id}</span>
                <ResearchStatusBadge status={run.status} size="sm" />
              </div>
              <h1 className="text-xl sm:text-2xl font-bold text-zinc-900 dark:text-zinc-100 mt-1 leading-tight">
                {run.topic}
              </h1>
            </div>
          </div>

          {/* Action Toolbar */}
          <div className="flex items-center gap-2 self-start sm:self-auto shrink-0 print:hidden">
            <Button
              variant="outline"
              size="sm"
              onClick={copyMarkdownReport}
              leftIcon={copied ? <Check className="w-4 h-4 text-emerald-500" /> : <Copy className="w-4 h-4" />}
            >
              {copied ? 'Copied' : 'Copy Markdown'}
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handlePrint}
              leftIcon={<Printer className="w-4 h-4" />}
            >
              Print / PDF
            </Button>
          </div>
        </div>

        {/* Timestamp and Latency bar */}
        <div className="flex flex-wrap items-center gap-y-2 gap-x-6 text-xs text-zinc-500 dark:text-zinc-400">
          <div>
            <span className="text-zinc-400 dark:text-zinc-500 mr-1.5">Started:</span>
            <span className="text-zinc-700 dark:text-zinc-300 font-mono">{formatDateTime(run.started_at)}</span>
          </div>
          <div>
            <span className="text-zinc-400 dark:text-zinc-500 mr-1.5">Completed:</span>
            <span className="text-zinc-700 dark:text-zinc-300 font-mono">{formatDateTime(run.completed_at)}</span>
          </div>
          <div>
            <span className="text-zinc-400 dark:text-zinc-500 mr-1.5">Total Duration:</span>
            <span className="text-zinc-700 dark:text-zinc-300 font-mono">
              {formatDuration(run.started_at, run.completed_at)}
            </span>
          </div>
        </div>

        {/* Executive Metrics Overview */}
        {summary && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
            <div className="p-3 rounded-lg bg-zinc-50 dark:bg-zinc-900/60 border border-zinc-200/60 dark:border-zinc-800/60">
              <div className="flex items-center gap-1.5 text-xs text-zinc-500 mb-1">
                <Layers className="w-3.5 h-3.5 text-zinc-400" />
                <span>Sub-questions</span>
              </div>
              <span className="text-lg font-bold font-mono text-zinc-900 dark:text-zinc-100">
                {summary.total_sub_questions ?? sections.length}
              </span>
            </div>

            <div className="p-3 rounded-lg bg-emerald-50/50 dark:bg-emerald-950/20 border border-emerald-200/50 dark:border-emerald-900/40">
              <div className="flex items-center gap-1.5 text-xs text-emerald-700 dark:text-emerald-400 mb-1">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
                <span>Verified</span>
              </div>
              <span className="text-lg font-bold font-mono text-emerald-700 dark:text-emerald-400">
                {summary.approved_sections ?? 0}
              </span>
            </div>

            <div className="p-3 rounded-lg bg-amber-50/50 dark:bg-amber-950/20 border border-amber-200/50 dark:border-amber-900/40">
              <div className="flex items-center gap-1.5 text-xs text-amber-700 dark:text-amber-400 mb-1">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />
                <span>Unverified / Floor</span>
              </div>
              <span className="text-lg font-bold font-mono text-amber-700 dark:text-amber-400">
                {(summary.unverified_sections ?? 0) + (summary.insufficient_evidence_sections ?? 0)}
              </span>
            </div>

            <div className="p-3 rounded-lg bg-zinc-50 dark:bg-zinc-900/60 border border-zinc-200/60 dark:border-zinc-800/60">
              <div className="flex items-center gap-1.5 text-xs text-zinc-500 mb-1">
                <RotateCw className="w-3.5 h-3.5 text-zinc-400" />
                <span>Revision Loops</span>
              </div>
              <span className="text-lg font-bold font-mono text-zinc-900 dark:text-zinc-100">
                {summary.total_revisions ?? 0}
              </span>
            </div>
          </div>
        )}

        {/* Explanation Alert for Partial or Insufficient outcomes */}
        {run.explanation && (
          <div className={`p-4 rounded-xl border flex items-start gap-3 ${
            run.status === 'insufficient_evidence'
              ? 'bg-zinc-100/80 dark:bg-zinc-800/80 border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300'
              : 'bg-amber-50/70 dark:bg-amber-950/30 border-amber-200/70 dark:border-amber-800/60 text-amber-900 dark:text-amber-200'
          }`}>
            <HelpCircle className="w-5 h-5 shrink-0 mt-0.5 text-amber-500" />
            <div className="space-y-1 text-xs">
              <p className="font-semibold uppercase tracking-wider text-[11px]">System Disclosure</p>
              <p className="leading-relaxed">{run.explanation}</p>
            </div>
          </div>
        )}
      </Card>

      {/* Sections List */}
      {sections.length > 0 ? (
        <div className="space-y-6">
          <div className="flex items-center gap-2 px-1">
            <FileText className="w-4 h-4 text-indigo-500" />
            <h2 className="text-sm font-semibold tracking-wide uppercase text-zinc-500 dark:text-zinc-400 font-mono">
              Citation-Grounded Sections ({sections.length})
            </h2>
          </div>

          {sections.map(([title, data], idx) => (
            <ReportSection
              key={title}
              index={idx + 1}
              title={title}
              data={data}
            />
          ))}
        </div>
      ) : (
        <Card className="p-8 text-center space-y-3">
          <p className="text-sm text-zinc-500 dark:text-zinc-400">
            No synthesized sections available for this run.
          </p>
        </Card>
      )}
    </div>
  );
};
