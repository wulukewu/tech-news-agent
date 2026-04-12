import { apiClient } from './client';

/**
 * Onboarding API functions
 *
 * Provides methods for managing user onboarding flow.
 */

/**
 * Onboarding step type
 */
export type OnboardingStep =
  | 'welcome'
  | 'profile_setup'
  | 'feed_selection'
  | 'preferences'
  | 'tutorial'
  | 'complete';

/**
 * Onboarding status response
 */
export interface OnboardingStatus {
  is_completed: boolean;
  is_skipped: boolean;
  current_step?: OnboardingStep;
  completed_steps: OnboardingStep[];
  started_at?: string;
  completed_at?: string;
  skipped_at?: string;
}

/**
 * Update onboarding progress request
 */
export interface UpdateOnboardingProgressRequest {
  step: OnboardingStep;
  completed: boolean;
  metadata?: Record<string, any>;
}

/**
 * Get current onboarding status
 *
 * @returns Promise resolving to onboarding status
 */
export async function getOnboardingStatus(): Promise<OnboardingStatus> {
  return apiClient.get<OnboardingStatus>('/api/onboarding/status');
}

/**
 * Update onboarding progress
 *
 * @param step - Onboarding step to update
 * @param completed - Whether the step is completed
 * @param metadata - Optional metadata for the step
 * @returns Promise resolving to success response
 */
export async function updateOnboardingProgress(
  step: OnboardingStep,
  completed: boolean,
  metadata?: Record<string, any>
): Promise<{ message: string }> {
  return apiClient.post('/api/onboarding/progress', {
    step,
    completed,
    metadata,
  });
}

/**
 * Mark onboarding as completed
 *
 * @returns Promise resolving to success response
 */
export async function markOnboardingCompleted(): Promise<{ message: string }> {
  return apiClient.post('/api/onboarding/complete', {});
}

/**
 * Mark onboarding as skipped
 *
 * @returns Promise resolving to success response
 */
export async function markOnboardingSkipped(): Promise<{ message: string }> {
  return apiClient.post('/api/onboarding/skip', {});
}

/**
 * Reset onboarding status
 *
 * @returns Promise resolving to success response
 */
export async function resetOnboarding(): Promise<{ message: string }> {
  return apiClient.post('/api/onboarding/reset', {});
}
