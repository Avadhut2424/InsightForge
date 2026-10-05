/**
 * General UI and validation utilities
 */

export function cn(...classes: (string | boolean | undefined | null)[]): string {
  return classes.filter(Boolean).join(' ');
}

export interface TopicValidationResult {
  isValid: boolean;
  error: string | null;
}

/**
 * Validates topic input in strict accordance with the FastAPI backend:
 * - Must not be empty or whitespace only
 * - Length between 3 and 500 characters
 */
export function validateTopic(topic: string): TopicValidationResult {
  const trimmed = topic.trim();
  if (!trimmed) {
    return {
      isValid: false,
      error: 'Topic cannot be empty or whitespace only.',
    };
  }

  if (trimmed.length < 3) {
    return {
      isValid: false,
      error: 'Topic is too short. Minimum length is 3 characters.',
    };
  }

  if (trimmed.length > 500) {
    return {
      isValid: false,
      error: 'Topic is too long. Maximum allowed length is 500 characters.',
    };
  }

  return {
    isValid: true,
    error: null,
  };
}
