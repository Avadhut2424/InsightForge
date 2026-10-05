import { describe, it, expect } from 'vitest';
import { validateTopic } from '../lib/utils';

describe('validateTopic', () => {
  it('should reject empty strings', () => {
    const res = validateTopic('');
    expect(res.isValid).toBe(false);
    expect(res.error).toContain('cannot be empty');
  });

  it('should reject whitespace-only strings', () => {
    const res = validateTopic('    \t\n   ');
    expect(res.isValid).toBe(false);
    expect(res.error).toContain('cannot be empty');
  });

  it('should reject topics shorter than 3 characters', () => {
    const res1 = validateTopic('a');
    expect(res1.isValid).toBe(false);
    expect(res1.error).toContain('too short');

    const res2 = validateTopic('ab');
    expect(res2.isValid).toBe(false);
    expect(res2.error).toContain('too short');
  });

  it('should reject topics longer than 500 characters', () => {
    const longTopic = 'a'.repeat(501);
    const res = validateTopic(longTopic);
    expect(res.isValid).toBe(false);
    expect(res.error).toContain('too long');
  });

  it('should accept valid topics between 3 and 500 characters', () => {
    const valid = 'How does retrieval-augmented generation reduce hallucinations?';
    const res = validateTopic(valid);
    expect(res.isValid).toBe(true);
    expect(res.error).toBeNull();
  });
});
