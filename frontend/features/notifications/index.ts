/**
 * Notifications Feature Module Exports
 *
 * Centralized exports for the notifications feature module.
 */

// Components
export * from './components';

// Hooks
export * from './hooks/useNotificationSettings';

// Types (re-export from global types)
export type {
  NotificationSettings,
  NotificationFrequency,
  NotificationChannel,
  FeedNotificationSettings,
  NotificationHistoryEntry,
  NotificationDeliveryStatus,
} from '@/types/notification';
