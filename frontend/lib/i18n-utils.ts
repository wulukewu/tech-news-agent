/**
 * I18n Utility Functions
 *
 * Helper functions for working with the i18n context.
 */

import type { TranslationFunction } from '@/types/i18n';

/**
 * Scheduler issue object structure
 */
export interface SchedulerIssue {
  type: string;
  message: string;
  hours?: number;
  threshold?: number;
  rate?: number;
}

/**
 * Type-safe translation helper that bypasses TypeScript strict checking
 * for dynamic translation keys.
 *
 * @param t - Translation function from useI18n()
 * @param key - Translation key (can be dynamic)
 * @param params - Optional parameters for interpolation
 * @returns Translated string
 *
 * @example
 * const { t } = useI18n();
 * const message = tr(t, 'pages.system-status.scheduler-stale', { hours: 17, threshold: 12 });
 */
export function tr(t: TranslationFunction, key: string, params?: Record<string, any>): string {
  return t(key as any, params);
}

/**
 * Format scheduler issue message based on type and parameters
 *
 * @param t - Translation function from useI18n()
 * @param issue - Issue object or string
 * @returns Formatted issue message string
 *
 * @example
 * const { t } = useI18n();
 * const message = formatSchedulerIssue(t, { type: 'stale', hours: 17, threshold: 12 });
 */
export function formatSchedulerIssue(
  t: TranslationFunction,
  issue: string | SchedulerIssue
): string {
  // Always return a string, never an object
  if (typeof issue === 'string') return issue;
  if (!issue || typeof issue !== 'object') return String(issue);

  let result: string;
  switch (issue.type) {
    case 'disabled':
      result = tr(t, 'pages.system-status.scheduler-disabled-desc');
      break;
    case 'waiting':
      result = tr(t, 'pages.system-status.scheduler-waiting');
      break;
    case 'never_executed':
      result = tr(t, 'pages.system-status.scheduler-never-executed');
      break;
    case 'stale':
      result = tr(t, 'pages.system-status.scheduler-stale', {
        hours: issue.hours,
        threshold: issue.threshold,
      });
      break;
    case 'high_failure_rate':
      result = tr(t, 'pages.system-status.scheduler-high-failure', {
        rate: issue.rate,
        threshold: issue.threshold,
      });
      break;
    default:
      result = issue.message || JSON.stringify(issue);
  }

  // Ensure we always return a string
  return typeof result === 'string' ? result : String(result);
}
