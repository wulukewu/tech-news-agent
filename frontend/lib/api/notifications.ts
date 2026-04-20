/**
 * Notification API functions
 *
 * This module provides functions for notification-related API calls:
 * - getNotificationSettings: Get user's notification preferences
 * - updateNotificationSettings: Update user's notification preferences
 * - getNotificationHistory: Get notification delivery history
 * - testNotification: Send a test notification
 */

import { apiClient } from './client';
import {
  NotificationSettings,
  NotificationDeliveryStatus,
  NotificationHistoryEntry,
} from '@/types/notification';

/**
 * Get user's notification settings
 *
 * @returns Promise<NotificationSettings> - User's notification preferences
 * @throws Error if request fails
 */
export async function getNotificationSettings(): Promise<NotificationSettings> {
  const response = await apiClient.get<NotificationSettings>('/api/notifications/settings');
  return response.data;
}

/**
 * Update user's notification settings
 *
 * @param settings - Updated notification settings
 * @param context - TanStack Query mutation context (optional)
 * @returns Promise<NotificationSettings> - Updated notification settings
 * @throws Error if request fails
 */
export async function updateNotificationSettings(
  settings: Partial<NotificationSettings>,
  context?: any
): Promise<NotificationSettings> {
  const response = await apiClient.patch<NotificationSettings>(
    '/api/notifications/settings',
    settings
  );
  return response.data;
}

/**
 * Get notification delivery history
 *
 * @param limit - Maximum number of history entries to return
 * @returns Promise<NotificationDeliveryStatus> - Notification delivery status and history
 * @throws Error if request fails
 */
export async function getNotificationHistory(
  limit: number = 50
): Promise<NotificationDeliveryStatus> {
  const response = await apiClient.get<NotificationDeliveryStatus>('/api/notifications/history', {
    params: { limit },
  });
  return response.data;
}

/**
 * Send a test notification
 *
 * @returns Promise<void>
 * @throws Error if request fails
 */
export async function sendTestNotification(): Promise<void> {
  await apiClient.post('/api/notifications/test');
}

/**
 * Get available feeds for notification settings
 *
 * @returns Promise<Array<{ id: string; name: string; category: string }>>
 * @throws Error if request fails
 */
export async function getAvailableFeeds(): Promise<
  Array<{ id: string; name: string; category: string }>
> {
  const response = await apiClient.get<{
    success: boolean;
    data: Array<{ id: string; name: string; category: string }>;
  }>('/api/feeds');
  return response.data.data; // Extract data from SuccessResponse wrapper
}

// Personalized Notification Preferences API

/**
 * User notification preferences for personalized scheduling
 */
export interface UserNotificationPreferences {
  id: string;
  userId: string;
  frequency: 'daily' | 'weekly' | 'monthly' | 'disabled';
  notificationTime: string; // HH:MM format
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
 * @returns Promise<NotificationPreviewResponse> - Preview information
 * @throws Error if request fails
 */
export async function previewNotificationTime(
  frequency: string,
  notificationTime: string,
  timezone: string
): Promise<NotificationPreviewResponse> {
  const response = await apiClient.get<{
    success: boolean;
    data: NotificationPreviewResponse;
  }>('/api/notifications/preferences/preview', {
    params: { frequency, notification_time: notificationTime, timezone },
  });
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

/**
 * Quiet Hours Settings
 */
export interface QuietHoursSettings {
  id?: string;
  user_id?: string;
  start_time: string;
  end_time: string;
  timezone: string;
  weekdays: number[];
  enabled: boolean;
  created_at?: string;
  updated_at?: string;
}

/**
 * Quiet Hours Status
 */
export interface QuietHoursStatus {
  is_in_quiet_hours: boolean;
  quiet_hours: QuietHoursSettings | null;
  next_notification_time: string | null;
  current_time: string;
  message: string;
}

/**
 * Technical Depth Settings
 */
export interface TechnicalDepthSettings {
  user_id: string;
  threshold: 'basic' | 'intermediate' | 'advanced' | 'expert';
  enabled: boolean;
  threshold_description?: string;
  threshold_numeric?: number;
}

/**
 * Technical Depth Level
 */
export interface TechnicalDepthLevel {
  value: string;
  label: string;
  description: string;
  numeric_value: number;
}

/**
 * Technical Depth Stats
 */
export interface TechnicalDepthStats {
  enabled: boolean;
  threshold?: string;
  threshold_description?: string;
  threshold_numeric?: number;
  message: string;
  error?: string;
}

/**
 * Notification History Record
 */
export interface NotificationHistoryRecord {
  id?: string;
  user_id?: string;
  sent_at?: string;
  channel: string;
  status: string;
  content?: string;
  feed_source?: string;
  error_message?: string;
  retry_count?: number;
  created_at?: string;
  updated_at?: string;
}

/**
 * Notification History Response
 */
export interface NotificationHistoryResponse {
  records: NotificationHistoryRecord[];
  total_count: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

/**
 * Notification Stats Response
 */
export interface NotificationStatsResponse {
  period_days: number;
  total_notifications: number;
  sent_count: number;
  failed_count: number;
  queued_count: number;
  cancelled_count: number;
  success_rate: number;
  channel_breakdown: {
    discord: number;
    email: number;
  };
  last_notification?: string;
}

// Quiet Hours API Functions

/**
 * Get user's quiet hours settings
 *
 * @returns Promise<QuietHoursSettings> - Quiet hours settings
 * @throws Error if request fails
 */
export async function getQuietHours(): Promise<QuietHoursSettings> {
  const response = await apiClient.get<{
    success: boolean;
    data: QuietHoursSettings;
  }>('/api/notifications/quiet-hours');
  return response.data.data;
}

/**
 * Update user's quiet hours settings
 *
 * @param updates - Updated quiet hours settings
 * @returns Promise<QuietHoursSettings> - Updated quiet hours settings
 * @throws Error if request fails
 */
export async function updateQuietHours(
  updates: Partial<QuietHoursSettings>
): Promise<QuietHoursSettings> {
  const response = await apiClient.put<{
    success: boolean;
    data: QuietHoursSettings;
  }>('/api/notifications/quiet-hours', updates);
  return response.data.data;
}

/**
 * Get quiet hours status
 *
 * @returns Promise<QuietHoursStatus> - Current quiet hours status
 * @throws Error if request fails
 */
export async function getQuietHoursStatus(): Promise<QuietHoursStatus> {
  const response = await apiClient.get<{
    success: boolean;
    data: QuietHoursStatus;
  }>('/api/notifications/quiet-hours/status');
  return response.data.data;
}

/**
 * Create default quiet hours settings
 *
 * @param timezone - IANA timezone identifier
 * @returns Promise<QuietHoursSettings> - Created quiet hours settings
 * @throws Error if request fails
 */
export async function createDefaultQuietHours(
  timezone: string = 'UTC'
): Promise<QuietHoursSettings> {
  const response = await apiClient.post<{
    success: boolean;
    data: QuietHoursSettings;
  }>('/api/notifications/quiet-hours/default', { timezone });
  return response.data.data;
}

/**
 * Delete quiet hours settings
 *
 * @returns Promise<void>
 * @throws Error if request fails
 */
export async function deleteQuietHours(): Promise<void> {
  await apiClient.delete('/api/notifications/quiet-hours');
}

// Technical Depth API Functions

/**
 * Get user's technical depth settings
 *
 * @returns Promise<TechnicalDepthSettings> - Technical depth settings
 * @throws Error if request fails
 */
export async function getTechnicalDepthSettings(): Promise<TechnicalDepthSettings> {
  const response = await apiClient.get<{
    success: boolean;
    data: TechnicalDepthSettings;
  }>('/api/notifications/tech-depth');
  return response.data.data;
}

/**
 * Update user's technical depth settings
 *
 * @param updates - Updated technical depth settings
 * @returns Promise<TechnicalDepthSettings> - Updated technical depth settings
 * @throws Error if request fails
 */
export async function updateTechnicalDepthSettings(
  updates: Partial<TechnicalDepthSettings>
): Promise<TechnicalDepthSettings> {
  const response = await apiClient.put<{
    success: boolean;
    data: TechnicalDepthSettings;
  }>('/api/notifications/tech-depth', updates);
  return response.data.data;
}

/**
 * Get available technical depth levels
 *
 * @returns Promise<TechnicalDepthLevel[]> - List of available levels
 * @throws Error if request fails
 */
export async function getTechnicalDepthLevels(): Promise<TechnicalDepthLevel[]> {
  const response = await apiClient.get<{
    success: boolean;
    data: { levels: TechnicalDepthLevel[] };
  }>('/api/notifications/tech-depth/levels');
  return response.data.data.levels;
}

/**
 * Get technical depth filtering statistics
 *
 * @returns Promise<TechnicalDepthStats> - Filtering statistics
 * @throws Error if request fails
 */
export async function getTechnicalDepthStats(): Promise<TechnicalDepthStats> {
  const response = await apiClient.get<{
    success: boolean;
    data: TechnicalDepthStats;
  }>('/api/notifications/tech-depth/stats');
  return response.data.data;
}

// Notification History API Functions

/**
 * Get notification history with pagination
 *
 * @param page - Page number (1-indexed)
 * @param pageSize - Number of records per page
 * @param channel - Filter by channel (optional)
 * @param status - Filter by status (optional)
 * @param daysBack - Only include last N days (optional)
 * @returns Promise<NotificationHistoryResponse> - Notification history
 * @throws Error if request fails
 */
export async function getNotificationHistoryPaginated(
  page: number = 1,
  pageSize: number = 20,
  channel?: string,
  status?: string,
  daysBack?: number
): Promise<NotificationHistoryResponse> {
  const params: any = { page, page_size: pageSize };
  if (channel) params.channel = channel;
  if (status) params.status = status;
  if (daysBack) params.days_back = daysBack;

  const response = await apiClient.get<{
    success: boolean;
    data: NotificationHistoryResponse;
  }>('/api/notifications/history', { params });
  return response.data.data;
}

/**
 * Get notification statistics
 *
 * @param daysBack - Number of days to include in statistics
 * @returns Promise<NotificationStatsResponse> - Notification statistics
 * @throws Error if request fails
 */
export async function getNotificationStats(
  daysBack: number = 30
): Promise<NotificationStatsResponse> {
  const response = await apiClient.get<{
    success: boolean;
    data: NotificationStatsResponse;
  }>('/api/notifications/history/stats', {
    params: { days_back: daysBack },
  });
  return response.data.data;
}
