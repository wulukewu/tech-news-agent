import { renderHook } from '@testing-library/react';
import { useSchedulerNotifications } from '../useSchedulerNotifications';
import { toast } from '@/lib/toast';

// Mock the toast wrapper
jest.mock('@/lib/toast', () => ({
  toast: {
    loading: jest.fn(() => 'toast-id-123'),
    dismiss: jest.fn(),
    success: jest.fn(),
    info: jest.fn(),
  },
}));

describe('useSchedulerNotifications Hook', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Property 13: Scheduler Completion Notification', () => {
    it('should show loading toast when scheduler starts', () => {
      const { rerender } = renderHook(
        ({ status }) => useSchedulerNotifications(status),
        {
          initialProps: {
            status: { isRunning: false, lastExecutionArticleCount: 0 },
          },
        },
      );

      // Scheduler starts running
      rerender({ status: { isRunning: true, lastExecutionArticleCount: 0 } });

      expect(toast.loading).toHaveBeenCalledWith('正在抓取文章...', {
        description: '排程器執行中，請稍候',
      });
    });

    it('should show success notification when scheduler completes with articles', () => {
      const { rerender } = renderHook(
        ({ status }) => useSchedulerNotifications(status),
        {
          initialProps: {
            status: { isRunning: true, lastExecutionArticleCount: 0 },
          },
        },
      );

      // Scheduler completes with 15 articles
      rerender({ status: { isRunning: false, lastExecutionArticleCount: 15 } });

      expect(toast.dismiss).toHaveBeenCalled();
      expect(toast.success).toHaveBeenCalledWith('文章抓取完成', {
        description: '成功抓取 15 篇新文章',
        duration: 5000,
      });
    });

    it('should show info notification when scheduler completes with no articles', () => {
      const { rerender } = renderHook(
        ({ status }) => useSchedulerNotifications(status),
        {
          initialProps: {
            status: { isRunning: true, lastExecutionArticleCount: 0 },
          },
        },
      );

      // Scheduler completes with 0 articles
      rerender({ status: { isRunning: false, lastExecutionArticleCount: 0 } });

      expect(toast.dismiss).toHaveBeenCalled();
      expect(toast.info).toHaveBeenCalledWith('文章抓取完成', {
        description: '沒有發現新文章',
        duration: 3000,
      });
    });

    it('should dismiss loading toast before showing completion notification', () => {
      const { rerender } = renderHook(
        ({ status }) => useSchedulerNotifications(status),
        {
          initialProps: {
            status: { isRunning: true, lastExecutionArticleCount: 0 },
          },
        },
      );

      // Scheduler completes
      rerender({ status: { isRunning: false, lastExecutionArticleCount: 10 } });

      // Verify dismiss is called before success
      const dismissCall = (toast.dismiss as jest.Mock).mock
        .invocationCallOrder[0];
      const successCall = (toast.success as jest.Mock).mock
        .invocationCallOrder[0];

      expect(dismissCall).toBeLessThan(successCall);
    });

    it('should display article count in success notification', () => {
      const { rerender } = renderHook(
        ({ status }) => useSchedulerNotifications(status),
        {
          initialProps: {
            status: { isRunning: true, lastExecutionArticleCount: 0 },
          },
        },
      );

      // Test with different article counts
      rerender({ status: { isRunning: false, lastExecutionArticleCount: 25 } });

      expect(toast.success).toHaveBeenCalledWith(
        '文章抓取完成',
        expect.objectContaining({
          description: '成功抓取 25 篇新文章',
        }),
      );
    });

    it('should not show notifications when status is null', () => {
      renderHook(() => useSchedulerNotifications(null));

      expect(toast.loading).not.toHaveBeenCalled();
      expect(toast.success).not.toHaveBeenCalled();
      expect(toast.info).not.toHaveBeenCalled();
    });

    it('should not show notifications when status does not change', () => {
      const { rerender } = renderHook(
        ({ status }) => useSchedulerNotifications(status),
        {
          initialProps: {
            status: { isRunning: false, lastExecutionArticleCount: 10 },
          },
        },
      );

      // Re-render with same status
      rerender({ status: { isRunning: false, lastExecutionArticleCount: 10 } });

      expect(toast.loading).not.toHaveBeenCalled();
      expect(toast.success).not.toHaveBeenCalled();
    });

    it('should handle multiple start-stop cycles correctly', () => {
      const { rerender } = renderHook(
        ({ status }) => useSchedulerNotifications(status),
        {
          initialProps: {
            status: { isRunning: false, lastExecutionArticleCount: 0 },
          },
        },
      );

      // First cycle
      rerender({ status: { isRunning: true, lastExecutionArticleCount: 0 } });
      rerender({ status: { isRunning: false, lastExecutionArticleCount: 5 } });

      // Second cycle
      rerender({ status: { isRunning: true, lastExecutionArticleCount: 5 } });
      rerender({ status: { isRunning: false, lastExecutionArticleCount: 10 } });

      expect(toast.loading).toHaveBeenCalledTimes(2);
      expect(toast.success).toHaveBeenCalledTimes(2);
    });
  });

  describe('Toast Duration', () => {
    it('should use 5 second duration for success notifications', () => {
      const { rerender } = renderHook(
        ({ status }) => useSchedulerNotifications(status),
        {
          initialProps: {
            status: { isRunning: true, lastExecutionArticleCount: 0 },
          },
        },
      );

      rerender({ status: { isRunning: false, lastExecutionArticleCount: 10 } });

      expect(toast.success).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({ duration: 5000 }),
      );
    });

    it('should use 3 second duration for info notifications', () => {
      const { rerender } = renderHook(
        ({ status }) => useSchedulerNotifications(status),
        {
          initialProps: {
            status: { isRunning: true, lastExecutionArticleCount: 0 },
          },
        },
      );

      rerender({ status: { isRunning: false, lastExecutionArticleCount: 0 } });

      expect(toast.info).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({ duration: 3000 }),
      );
    });
  });
});
