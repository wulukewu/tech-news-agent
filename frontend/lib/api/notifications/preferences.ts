'use client';

import { apiClient } from '../client';

/**
 * User notification preferences for personalized scheduling
 */
export interface UserNotificationPreferences {
  id: string;
  userId: string;
  frequency: 'daily' | 'weekly' | 'monthly' | 'disabled';
  notificationTime: string; // HH:MM format
  notificationDayOfWeek: number; // 0=Sunday, 1=Monday, ..., 6=Saturday
  notificationDayOfMonth: number; // 1-31
  timezone: string;
  dmEnabled: boolean;
  emailEnabled: boolean;
  createdAt: string;
  updatedAt: string;
}

/**
 * Request model for updating user notification preferences
 */
export interface UpdateUserNotificationPreferencesRequest {
  frequency?: 'daily' | 'weekly' | 'monthly' | 'disabled';
  notificationTime?: string; // HH:MM format
  notificationDayOfWeek?: number; // 0=Sunday, 1=Monday, ..., 6=Saturday
  notificationDayOfMonth?: number; // 1-31
  timezone?: string;
  dmEnabled?: boolean;
  emailEnabled?: boolean;
}

/**
 * Timezone option for selector
 */
export interface TimezoneOption {
  value: string;
  label: string;
  offset: string;
}

/**
 * Notification preview response
 */
export interface NotificationPreviewResponse {
  nextNotificationTime: string | null;
  localTime: string | null;
  utcTime: string | null;
  message: string;
}

/**
 * Notification status response
 */
export interface NotificationStatusResponse {
  scheduled: boolean;
  jobId?: string;
  nextRunTime?: string;
  message: string;
}

/**
 * Get user's personalized notification preferences
 *
 * @returns Promise<UserNotificationPreferences> - User's notification preferences
 * @throws Error if request fails
 */
export async function getNotificationPreferences(): Promise<UserNotificationPreferences> {
  const response = await apiClient.get<{
    success: boolean;
    data: UserNotificationPreferences;
  }>('/api/notifications/preferences');
  return response.data.data;
}

/**
 * Update user's personalized notification preferences
 *
 * @param updates - Updated notification preferences
 * @returns Promise<UserNotificationPreferences> - Updated notification preferences
 * @throws Error if request fails
 */
export async function updateNotificationPreferences(
  updates: UpdateUserNotificationPreferencesRequest
): Promise<UserNotificationPreferences> {
  const response = await apiClient.put<{
    success: boolean;
    data: UserNotificationPreferences;
  }>('/api/notifications/preferences', updates);
  return response.data.data;
}

/**
 * Preview next notification time based on preferences
 *
 * @param frequency - Notification frequency
 * @param notificationTime - Time in HH:MM format
 * @param timezone - IANA timezone identifier
 * @param notificationDayOfWeek - Day of week for weekly notifications (0-6)
 * @param notificationDayOfMonth - Day of month for monthly notifications (1-31)
 * @returns Promise<NotificationPreviewResponse> - Preview information
 * @throws Error if request fails
 */
export async function previewNotificationTime(
  frequency: string,
  notificationTime: string,
  timezone: string,
  notificationDayOfWeek?: number,
  notificationDayOfMonth?: number
): Promise<NotificationPreviewResponse> {
  const params: Record<string, unknown> = {
    frequency,
    notification_time: notificationTime,
    timezone,
  };

  if (notificationDayOfWeek !== undefined) {
    params.notification_day_of_week = notificationDayOfWeek;
  }

  if (notificationDayOfMonth !== undefined) {
    params.notification_day_of_month = notificationDayOfMonth;
  }

  const response = await apiClient.get<{
    success: boolean;
    data: NotificationPreviewResponse;
  }>('/api/notifications/preferences/preview', { params });
  return response.data.data;
}

/**
 * Get list of supported timezones
 *
 * @returns Promise<TimezoneOption[]> - List of timezone options
 * @throws Error if request fails
 */
export async function getSupportedTimezones(): Promise<TimezoneOption[]> {
  const response = await apiClient.get<{
    success: boolean;
    data: { timezones: TimezoneOption[]; total: number };
  }>('/api/notifications/preferences/timezones');
  return response.data.data.timezones;
}

/**
 * Get notification scheduling status
 *
 * @returns Promise<NotificationStatusResponse> - Scheduling status
 * @throws Error if request fails
 */
export async function getNotificationStatus(): Promise<NotificationStatusResponse> {
  const response = await apiClient.get<{
    success: boolean;
    data: NotificationStatusResponse;
  }>('/api/notifications/preferences/status');
  return response.data.data;
}

/**
 * Manually trigger user notification rescheduling
 *
 * @returns Promise<{success: boolean, message: string}>
 * @throws Error if request fails
 */
export async function rescheduleUserNotification(): Promise<{ success: boolean; message: string }> {
  const response = await apiClient.post<{
    success: boolean;
    data: { success: boolean; message: string };
  }>('/api/notifications/preferences/reschedule');
  return response.data.data;
}

// Phase 1: Advanced Notification Features API
