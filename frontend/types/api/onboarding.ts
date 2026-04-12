// Generated from onboarding.py
// Generated at: 2026-04-11T22:10:26.235169

/**
 * Onboarding status response model
 *
 * Used by GET /api/onboarding/status endpoint to return the user's
 * current onboarding progress and state.
 */
export interface OnboardingStatus {
  /** Whether user has completed the onboarding flow */
  onboarding_completed: boolean;
  /** Current step in onboarding flow (welcome, recommendations, complete) */
  onboarding_step?: string | null;
  /** Whether user skipped the onboarding flow */
  onboarding_skipped: boolean;
  /** Whether user has completed the tooltip tour */
  tooltip_tour_completed: boolean;
  /** Whether the onboarding modal should be displayed to the user */
  should_show_onboarding: boolean;
}

/**
 * Request model for updating onboarding progress
 *
 * Used by POST /api/onboarding/progress endpoint.
 */
export interface UpdateOnboardingProgressRequest {
  /** Onboarding step (welcome, recommendations, complete) */
  step: string;
  /** Whether the step is completed */
  completed: boolean;
}

/**
 * Complete user preferences model
 *
 * Represents the full user_preferences table record.
 */
export interface UserPreferences {
  /** Preference record UUID */
  id: string;
  /** User UUID */
  user_id: string;
  /** Whether user has completed the onboarding flow */
  onboarding_completed: boolean;
  /** Current step in onboarding flow */
  onboarding_step?: string | null;
  /** Whether user skipped the onboarding flow */
  onboarding_skipped: boolean;
  /** Timestamp when user started onboarding */
  onboarding_started_at?: string | null;
  /** Timestamp when user completed onboarding */
  onboarding_completed_at?: string | null;
  /** Whether user has completed the tooltip tour */
  tooltip_tour_completed: boolean;
  /** Whether user skipped the tooltip tour */
  tooltip_tour_skipped: boolean;
  /** User preferred language code */
  preferred_language: string;
  /** Record creation timestamp */
  created_at: string;
  /** Record last update timestamp */
  updated_at: string;
}
