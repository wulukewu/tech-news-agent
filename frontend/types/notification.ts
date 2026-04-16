/**
 * Notification-related type definitions
 *
 * This file defines the core types for notification settings,
 * preferences, and notification history.
 */

/**
 * Notification frequency options
 */
export type NotificationFrequency = 'immediate' | 'daily' | 'weekly';

/**
 * Notification channel types
 */
export type NotificationChannel = 'dm' | 'email' | 'push' | 'in-app';

/**
 * Notification settings for a specific feed or category
 */
export interface FeedNotificationSettings {
  feedId?: string;
  category?: string;
  enabled: boolean;
  minTinkeringIndex?: number;
}

/**
 * User notification preferences
 */
export interface NotificationSettings {
  // Global notification toggle
  enabled: boolean;

  // DM notifications toggle
  dmEnabled: boolean;

  // Email notifications toggle (if backend supports)
  emailEnabled: boolean;

  // Notification frequency
  frequency: NotificationFrequency;

  // Quiet hours (preferred delivery hours)
  quietHours: {
    enabled: boolean;
    start: string; // HH:mm format
    end: string; // HH:mm format
  };

  // Minimum tinkering index threshold for notifications
  minTinkeringIndex: number;

  // Per-feed or per-category notification settings
  feedSettings: FeedNotificationSettings[];

  // Enabled notification channels
  channels: NotificationChannel[];
}

/**
 * Notification history entry
 */
export interface NotificationHistoryEntry {
  id: string;
  articleId: string;
  articleTitle: string;
  sentAt: Date;
  channel: NotificationChannel;
  status: 'sent' | 'failed' | 'pending';
  errorMessage?: string;
}

/**
 * Notification delivery status
 */
export interface NotificationDeliveryStatus {
  totalSent: number;
  totalFailed: number;
  lastSentAt?: Date;
  recentHistory: NotificationHistoryEntry[];
}

/**
 * Default notification settings
 */
export const DEFAULT_NOTIFICATION_SETTINGS: NotificationSettings = {
  enabled: true,
  dmEnabled: true,
  emailEnabled: false,
  frequency: 'immediate',
  quietHours: {
    enabled: false,
    start: '22:00',
    end: '08:00',
  },
  minTinkeringIndex: 3,
  feedSettings: [],
  channels: ['dm', 'in-app'],
};
