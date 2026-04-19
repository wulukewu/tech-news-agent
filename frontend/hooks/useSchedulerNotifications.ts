import { useEffect, useRef } from 'react';
import { toast } from '@/lib/toast';
import { useI18n } from '@/contexts/I18nContext';

/**
 * Scheduler status for notifications
 */
export interface SchedulerStatus {
  isRunning: boolean;
  lastExecutionArticleCount: number;
}

/**
 * Hook to manage scheduler completion notifications
 *
 * Automatically shows toast notifications when:
 * - Scheduler starts running (progress notification)
 * - Scheduler completes (success notification with article count)
 *
 * Requirements: 5.4, 5.5, 5.7
 *
 * @example
 * ```tsx
 * const { status } = useSchedulerStatus();
 * useSchedulerNotifications(status);
 * ```
 */
export function useSchedulerNotifications(status: SchedulerStatus | null) {
  const previousRunningRef = useRef<boolean>(false);
  const toastIdRef = useRef<string | number | null>(null);
  const { t } = useI18n();

  useEffect(() => {
    if (!status) return;

    const { isRunning, lastExecutionArticleCount } = status;
    const wasRunning = previousRunningRef.current;

    // Scheduler just started
    if (isRunning && !wasRunning) {
      toast
        .loading(t('messages.fetching-articles'), {
          description: t('messages.scheduler-running'),
        })
        .then((toastId) => {
          toastIdRef.current = toastId;
        });
    }

    // Scheduler just completed
    if (!isRunning && wasRunning) {
      // Dismiss the loading toast
      if (toastIdRef.current) {
        toast.dismiss(toastIdRef.current);
        toastIdRef.current = null;
      }

      // Show success notification
      if (lastExecutionArticleCount > 0) {
        toast.success(t('messages.fetch-complete'), {
          description: t('messages.article-count', { count: lastExecutionArticleCount }),
          duration: 5000,
        });
      } else {
        toast.info(t('messages.fetch-complete'), {
          description: t('messages.no-articles'),
          duration: 3000,
        });
      }
    }

    previousRunningRef.current = isRunning;
  }, [status, t]);

  return null;
}
