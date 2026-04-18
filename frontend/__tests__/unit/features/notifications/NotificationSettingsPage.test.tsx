/**
 * Notification Settings Page Tests
 *
 * Unit tests for the notification settings page component.
 *
 * Requirements: 6.10
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import NotificationSettingsPage from '@/app/dashboard/settings/notifications/page';
import * as notificationApi from '@/lib/api/notifications';
import { DEFAULT_NOTIFICATION_SETTINGS } from '@/types/notification';

// Mock the API functions
vi.mock('@/lib/api/notifications', () => ({
  getNotificationSettings: vi.fn(),
  updateNotificationSettings: vi.fn(),
  sendTestNotification: vi.fn(),
  getAvailableFeeds: vi.fn(),
  getNotificationHistory: vi.fn(),
}));

// Mock toast
vi.mock('@/lib/toast', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

const createQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

const renderWithQueryClient = (component: React.ReactElement) => {
  const queryClient = createQueryClient();
  return render(<QueryClientProvider client={queryClient}>{component}</QueryClientProvider>);
};

describe('NotificationSettingsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    // Default API responses
    vi.mocked(notificationApi.getNotificationSettings).mockResolvedValue(
      DEFAULT_NOTIFICATION_SETTINGS
    );
    vi.mocked(notificationApi.getAvailableFeeds).mockResolvedValue([]);
    vi.mocked(notificationApi.getNotificationHistory).mockResolvedValue({
      totalSent: 0,
      totalFailed: 0,
      recentHistory: [],
    });
  });

  describe('Page Rendering', () => {
    it('should render page title and description', async () => {
      renderWithQueryClient(<NotificationSettingsPage />);

      await waitFor(() => {
        expect(screen.getByText('通知設定')).toBeInTheDocument();
        expect(screen.getByText('管理您的通知偏好和接收設定')).toBeInTheDocument();
      });
    });

    it('should show loading state initially', () => {
      renderWithQueryClient(<NotificationSettingsPage />);
      expect(screen.getByRole('status')).toBeInTheDocument();
    });

    it('should render all notification setting sections when loaded', async () => {
      renderWithQueryClient(<NotificationSettingsPage />);

      await waitFor(() => {
        expect(screen.getByText('通知總開關')).toBeInTheDocument();
        expect(screen.getByText('通知頻率')).toBeInTheDocument();
        expect(screen.getByText('勿擾時段')).toBeInTheDocument();
        expect(screen.getByText('技術深度閾值')).toBeInTheDocument();
        expect(screen.getByText('個別來源通知設定')).toBeInTheDocument();
        expect(screen.getByText('通知歷史記錄')).toBeInTheDocument();
      });
    });
  });

  describe('Global Notification Toggle', () => {
    it('should toggle global notifications', async () => {
      vi.mocked(notificationApi.updateNotificationSettings).mockResolvedValue({
        ...DEFAULT_NOTIFICATION_SETTINGS,
        enabled: false,
      });

      renderWithQueryClient(<NotificationSettingsPage />);

      await waitFor(() => {
        const globalToggle = screen.getByLabelText('啟用通知');
        expect(globalToggle).toBeChecked();
      });

      const globalToggle = screen.getByLabelText('啟用通知');
      fireEvent.click(globalToggle);

      await waitFor(() => {
        expect(notificationApi.updateNotificationSettings).toHaveBeenCalledWith(
          {
            ...DEFAULT_NOTIFICATION_SETTINGS,
            enabled: false,
          },
          expect.any(Object) // TanStack Query context parameters
        );
      });
    });

    it('should hide other settings when global notifications are disabled', async () => {
      vi.mocked(notificationApi.getNotificationSettings).mockResolvedValue({
        ...DEFAULT_NOTIFICATION_SETTINGS,
        enabled: false,
      });

      renderWithQueryClient(<NotificationSettingsPage />);

      await waitFor(() => {
        expect(screen.getByText('通知總開關')).toBeInTheDocument();
        expect(screen.queryByText('通知頻率')).not.toBeInTheDocument();
        expect(screen.queryByText('勿擾時段')).not.toBeInTheDocument();
      });
    });
  });

  describe('DM Notifications Toggle', () => {
    it('should toggle DM notifications', async () => {
      vi.mocked(notificationApi.updateNotificationSettings).mockResolvedValue({
        ...DEFAULT_NOTIFICATION_SETTINGS,
        dmEnabled: false,
      });

      renderWithQueryClient(<NotificationSettingsPage />);

      await waitFor(() => {
        const dmToggle = screen.getByLabelText('Discord 私訊通知');
        expect(dmToggle).toBeChecked();
      });

      const dmToggle = screen.getByLabelText('Discord 私訊通知');
      fireEvent.click(dmToggle);

      await waitFor(() => {
        expect(notificationApi.updateNotificationSettings).toHaveBeenCalledWith(
          {
            ...DEFAULT_NOTIFICATION_SETTINGS,
            dmEnabled: false,
          },
          expect.any(Object) // TanStack Query context parameters
        );
      });
    });
  });

  describe('Email Notifications Toggle', () => {
    it('should toggle email notifications', async () => {
      vi.mocked(notificationApi.updateNotificationSettings).mockResolvedValue({
        ...DEFAULT_NOTIFICATION_SETTINGS,
        emailEnabled: true,
      });

      renderWithQueryClient(<NotificationSettingsPage />);

      await waitFor(() => {
        const emailToggle = screen.getByLabelText('電子郵件通知');
        expect(emailToggle).not.toBeChecked();
      });

      const emailToggle = screen.getByLabelText('電子郵件通知');
      fireEvent.click(emailToggle);

      await waitFor(() => {
        expect(notificationApi.updateNotificationSettings).toHaveBeenCalledWith(
          {
            ...DEFAULT_NOTIFICATION_SETTINGS,
            emailEnabled: true,
          },
          expect.any(Object) // TanStack Query context parameters
        );
      });
    });
  });

  describe('Test Notification', () => {
    it('should send test notification when button is clicked', async () => {
      vi.mocked(notificationApi.sendTestNotification).mockResolvedValue();

      renderWithQueryClient(<NotificationSettingsPage />);

      await waitFor(() => {
        const testButton = screen.getByText('測試通知');
        expect(testButton).toBeInTheDocument();
      });

      const testButton = screen.getByText('測試通知');
      fireEvent.click(testButton);

      await waitFor(() => {
        expect(notificationApi.sendTestNotification).toHaveBeenCalled();
      });
    });

    it('should disable test button when notifications are disabled', async () => {
      vi.mocked(notificationApi.getNotificationSettings).mockResolvedValue({
        ...DEFAULT_NOTIFICATION_SETTINGS,
        enabled: false,
      });

      renderWithQueryClient(<NotificationSettingsPage />);

      await waitFor(() => {
        const testButton = screen.getByText('測試通知');
        expect(testButton).toBeDisabled();
      });
    });
  });

  describe('Auto-save Functionality', () => {
    it('should show unsaved changes indicator', async () => {
      renderWithQueryClient(<NotificationSettingsPage />);

      await waitFor(() => {
        const globalToggle = screen.getByLabelText('啟用通知');
        expect(globalToggle).toBeInTheDocument();
      });

      const globalToggle = screen.getByLabelText('啟用通知');
      fireEvent.click(globalToggle);

      await waitFor(() => {
        expect(screen.getByText('設定將自動儲存...')).toBeInTheDocument();
      });
    });

    it('should show manual save button when there are unsaved changes', async () => {
      renderWithQueryClient(<NotificationSettingsPage />);

      await waitFor(() => {
        const globalToggle = screen.getByLabelText('啟用通知');
        expect(globalToggle).toBeInTheDocument();
      });

      const globalToggle = screen.getByLabelText('啟用通知');
      fireEvent.click(globalToggle);

      await waitFor(() => {
        expect(screen.getByText('儲存')).toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    it('should display error message when settings fail to load', async () => {
      vi.mocked(notificationApi.getNotificationSettings).mockRejectedValue(
        new Error('Failed to load settings')
      );

      renderWithQueryClient(<NotificationSettingsPage />);

      await waitFor(() => {
        expect(screen.getByText('Failed to load settings')).toBeInTheDocument();
      });
    });

    it('should handle update errors gracefully', async () => {
      vi.mocked(notificationApi.updateNotificationSettings).mockRejectedValue(
        new Error('Update failed')
      );

      renderWithQueryClient(<NotificationSettingsPage />);

      await waitFor(() => {
        const globalToggle = screen.getByLabelText('啟用通知');
        expect(globalToggle).toBeInTheDocument();
      });

      const globalToggle = screen.getByLabelText('啟用通知');
      fireEvent.click(globalToggle);

      // The error should be handled by the mutation's onError callback
      // which shows a toast (mocked in this test)
    });
  });

  describe('Accessibility', () => {
    it('should have proper labels for all form controls', async () => {
      renderWithQueryClient(<NotificationSettingsPage />);

      await waitFor(() => {
        expect(screen.getByLabelText('啟用通知')).toBeInTheDocument();
        expect(screen.getByLabelText('Discord 私訊通知')).toBeInTheDocument();
        expect(screen.getByLabelText('電子郵件通知')).toBeInTheDocument();
      });
    });

    it('should have proper heading structure', async () => {
      renderWithQueryClient(<NotificationSettingsPage />);

      await waitFor(() => {
        const mainHeading = screen.getByRole('heading', { level: 1 });
        expect(mainHeading).toHaveTextContent('通知設定');
      });
    });
  });
});
