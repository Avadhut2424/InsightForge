import React, { useState, useRef, useEffect } from 'react';
import { Sparkles, ArrowRight, AlertCircle } from 'lucide-react';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { validateTopic } from '../../lib/utils';

interface ResearchInputProps {
  onSubmit: (topic: string) => void;
  isLoading?: boolean;
}

const PRESET_TOPICS = [
  'The environmental impact of AI computing hardware and energy consumption',
  'Superconducting qubit coherence times and error mitigation strategies',
  'Solid-state lithium battery degradation mechanisms and interfacial stability',
  'Autonomous multi-agent orchestration patterns in retrieval-augmented workflows',
];

export const ResearchInput: React.FC<ResearchInputProps> = ({ onSubmit, isLoading = false }) => {
  const [topic, setTopic] = useState<string>('');
  const [touched, setTouched] = useState<boolean>(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const validation = validateTopic(topic);
  const charCount = topic.trim().length;

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.focus();
    }
  }, []);

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setTouched(true);

    if (validation.isValid && !isLoading) {
      onSubmit(topic.trim());
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handlePresetClick = (preset: string) => {
    setTopic(preset);
    setTouched(true);
    if (textareaRef.current) {
      textareaRef.current.focus();
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-7 py-6">
      {/* Hero Intro */}
      <div className="text-center space-y-2.5">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-50 dark:bg-indigo-950/40 border border-indigo-200/60 dark:border-indigo-800/60 text-indigo-700 dark:text-indigo-300 text-xs font-medium mb-1">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Autonomous Retrieval & Verification</span>
        </div>
        <h1 className="text-2xl sm:text-4xl font-bold tracking-tight text-zinc-900 dark:text-zinc-100">
          Research anything in your knowledge base.
        </h1>
        <p className="text-sm sm:text-base text-zinc-600 dark:text-zinc-400 max-w-xl mx-auto leading-relaxed">
          InsightForge decomposes complex topics, retrieves grounded evidence from pgvector, synthesizes verbatim citations, and verifies every section.
        </p>
      </div>

      {/* Input Card */}
      <Card className="p-4 sm:p-5 shadow-sm border-zinc-200 dark:border-zinc-800 focus-within:ring-2 focus-within:ring-indigo-500/30 focus-within:border-indigo-500 transition-all">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="relative">
            <textarea
              ref={textareaRef}
              value={topic}
              onChange={(e) => {
                setTopic(e.target.value);
                if (!touched) setTouched(true);
              }}
              onKeyDown={handleKeyDown}
              disabled={isLoading}
              rows={4}
              placeholder="How does retrieval-augmented generation reduce hallucinations in technical research?"
              className="w-full resize-none bg-transparent text-sm sm:text-base text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 dark:placeholder:text-zinc-600 focus:outline-none disabled:opacity-50 leading-relaxed"
            />
          </div>

          {/* Validation Error Message */}
          {touched && !validation.isValid && topic.length > 0 && (
            <div className="flex items-center gap-1.5 text-xs text-rose-600 dark:text-rose-400">
              <AlertCircle className="w-3.5 h-3.5 shrink-0" />
              <span>{validation.error}</span>
            </div>
          )}

          {/* Bottom Bar: Character count + Submit */}
          <div className="flex items-center justify-between gap-3 pt-3 border-t border-zinc-100 dark:border-zinc-800/80">
            <div className="flex items-center gap-2 text-xs text-zinc-400 dark:text-zinc-500 font-mono">
              <span className={charCount > 500 ? 'text-rose-500 font-semibold' : ''}>
                {charCount}/500 chars
              </span>
              <span className="hidden sm:inline-block text-zinc-300 dark:text-zinc-700">•</span>
              <span className="hidden sm:inline-flex items-center gap-1">
                Press <kbd className="px-1.5 py-0.5 rounded-sm bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 text-[10px]">Ctrl+Enter</kbd>
              </span>
            </div>

            <Button
              type="submit"
              disabled={!validation.isValid || isLoading}
              isLoading={isLoading}
              variant="primary"
              size="md"
              rightIcon={!isLoading ? <ArrowRight className="w-4 h-4" /> : undefined}
            >
              {isLoading ? 'Starting research...' : 'Start Research'}
            </Button>
          </div>
        </form>
      </Card>

      {/* Suggested Topic Chips */}
      <div className="space-y-2.5">
        <span className="text-xs font-semibold uppercase tracking-wider text-zinc-400 dark:text-zinc-500 font-mono">
          Knowledge Base Samples
        </span>
        <div className="flex flex-wrap gap-2">
          {PRESET_TOPICS.map((preset) => (
            <button
              key={preset}
              type="button"
              onClick={() => handlePresetClick(preset)}
              disabled={isLoading}
              className="text-xs text-left px-3 py-1.5 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900/60 hover:border-indigo-300 dark:hover:border-indigo-800/80 hover:bg-zinc-50 dark:hover:bg-zinc-850 text-zinc-700 dark:text-zinc-300 transition-colors disabled:opacity-50"
            >
              {preset}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
