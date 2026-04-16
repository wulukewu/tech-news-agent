/**
 * Notification Settings Hooks
 *
 * React Query hooks for managing notification settings.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getNotificationSettings,
  updateNotificationSettings,
  sendTestNotification,
} from '@/lib/api/notifications';
import { NotificationSettings } from '@/types/notification';
import { toast } from '@/lib/toast';

/**
 * Query keys for notification settings
 */
export const notificationKeys = {
  all: ['notifications'] as const,
  settings: () => [...notificationKeys.all, 'settings'] as const,
  history: () => [...notificationKeys.all, 'history'] as const,
};

/**
 * Hook to fetch notification settings
 *
 * Requirements: 6.1, 6.2
 */
export function useNotificationSettings() {
  return useQuery({
    queryKey: notificationKeys.settings(),
    queryFn: getNotificationSettings,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Hook to update notification settings
 *
 * Requirements: 6.10
 */
export function useUpdateNotificationSettings() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: updateNotificationSettings,
    onSuccess: (updatedSettings) => {
      queryClient.setQueryData(notificationKeys.settings(), updatedSettings);
      toast.success('通知設定已儲存');
    },
    onError: (error: Error) => {
      toast.error(`儲存失敗: ${error.message}`);
    },
  });
}

/**
 * Hook to send test notification
 *
 * Requirements: 6.10
 */
export function useTestNotification() {
  return useMutation({
    mutationFn: sendTestNotification,
    onSuccess: () => {
      toast.success('測試通知已發送');
    },
    onError: (error: Error) => {
      toast.error(`測試通知失敗: ${error.message}`);
    },
  });
}
