import { apiClient } from './client';

/**
 * Analytics API functions
 *
 * Provides methods for logging analytics events and retrieving onboarding metrics.
 */

/**
 * Analytics event types
 */
export type AnalyticsEventType =
  | 'page_view'
  | 'button_click'
  | 'form_submit'
  | 'error'
  | 'feature_usage'
  | 'onboarding_step';

/**
 * Analytics event payload
 */
export interface AnalyticsEvent {
  event_type: AnalyticsEventType;
  event_name: string;
  properties?: Record<string, any>;
  timestamp?: string;
}

/**
 * Onboarding completion rate response
 */
export interface OnboardingCompletionRateResponse {
  total_users: number;
  completed_users: number;
  completion_rate: number;
  period_days: number;
}

/**
 * Drop-off rates response
 */
export interface DropOffRatesResponse {
  total_started: number;
  drop_off_by_step: Record<string, number>;
  completion_rate: number;
}

/**
 * Average time per step response
 */
export interface AverageTimePerStepResponse {
  average_time_by_step: Record<string, number>;
  total_average_time: number;
}

/**
 * Log an analytics event
 *
 * @param event - Analytics event to log
 * @returns Promise resolving to success response
 */
export async function logAnalyticsEvent(event: AnalyticsEvent): Promise<{ message: string }> {
  return apiClient.post('/api/analytics/event', event);
}

/**
 * Get onboarding completion rate
 *
 * @param days - Number of days to analyze (default: 30)
 * @returns Promise resolving to completion rate data
 */
export async function getOnboardingCompletionRate(
  days: number = 30
): Promise<OnboardingCompletionRateResponse> {
  const response = await apiClient.get<OnboardingCompletionRateResponse>(
    `/api/analytics/onboarding/completion-rate?days=${days}`
  );
  return response.data;
}

/**
 * Get onboarding drop-off rates
 *
 * @returns Promise resolving to drop-off rates data
 */
export async function getDropOffRates(): Promise<DropOffRatesResponse> {
  const response = await apiClient.get<DropOffRatesResponse>('/api/analytics/onboarding/drop-off');
  return response.data;
}

/**
 * Get average time per onboarding step
 *
 * @returns Promise resolving to average time data
 */
export async function getAverageTimePerStep(): Promise<AverageTimePerStepResponse> {
  const response = await apiClient.get<AverageTimePerStepResponse>(
    '/api/analytics/onboarding/average-time'
  );
  return response.data;
}
