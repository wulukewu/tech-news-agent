// Generated from analytics.py
// Generated at: 2026-04-11T22:10:26.237220

/**
 * Request model for logging analytics events
 *
 * Used by POST /api/analytics/event endpoint.
 */
export interface LogAnalyticsEventRequest {
  /** Type of event (onboarding_started, step_completed, etc.) */
  event_type: string;
  /** Additional event metadata */
  event_data: Record<string, any>;
}

/**
 * Analytics event model
 *
 * Represents a single analytics event record.
 */
export interface AnalyticsEvent {
  /** Event UUID */
  id: string;
  /** User UUID */
  user_id: string;
  /** Event type */
  event_type: string;
  /** Event metadata */
  event_data: Record<string, any>;
  /** Event timestamp */
  created_at: string;
}

/**
 * Response model for onboarding completion rate
 *
 * Used by GET /api/analytics/onboarding/completion-rate endpoint.
 */
export interface OnboardingCompletionRateResponse {
  /** Completion rate as percentage (0-100) */
  completion_rate: number;
  /** Total number of users who started onboarding */
  total_users: number;
  /** Number of users who completed onboarding */
  completed_users: number;
  /** Number of users who skipped onboarding */
  skipped_users: number;
  /** Start date of the analysis period */
  start_date: string;
  /** End date of the analysis period */
  end_date: string;
}

/**
 * Response model for drop-off rates at each onboarding step
 *
 * Used by GET /api/analytics/onboarding/drop-off endpoint.
 */
export interface DropOffRatesResponse {
  /** Drop-off rate for each step as percentage (0-100) */
  drop_off_by_step: Record<string, any>;
  /** Total number of users who started onboarding */
  total_started: number;
}

/**
 * Response model for average time spent per onboarding step
 *
 * Used by GET /api/analytics/onboarding/average-time endpoint.
 */
export interface AverageTimePerStepResponse {
  /** Average time in seconds for each step */
  average_time_by_step: Record<string, any>;
  /** Total number of completed onboarding flows */
  total_completions: number;
}
