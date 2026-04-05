import { useEffect, useRef } from 'react';
import { toast } from 'sonner';

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

  useEffect(() => {
    if (!status) return;

    const { isRunning, lastExecutionArticleCount } = status;
    const wasRunning = previousRunningRef.current;

    // Scheduler just started
    if (isRunning && !wasRunning) {
      toastIdRef.current = toast.loading('正在抓取文章...', {
        description: '排程器執行中，請稍候',
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
        toast.success('文章抓取完成', {
          description: `成功抓取 ${lastExecutionArticleCount} 篇新文章`,
          duration: 5000,
        });
      } else {
        toast.info('文章抓取完成', {
          description: '沒有發現新文章',
          duration: 3000,
        });
      }
    }

    previousRunningRef.current = isRunning;
  }, [status]);

  return null;
}
