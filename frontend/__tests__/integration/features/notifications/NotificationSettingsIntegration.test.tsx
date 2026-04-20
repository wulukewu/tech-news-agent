import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { I18nProvider } from '@/contexts/I18nContext';
import { PersonalizedNotificationSettings } from '@/features/notifications/components/PersonalizedNotificationSettings';
import { NotificationFrequencySelector } from '@/features/notifications/components/NotificationFrequencySelector';
import { NotificationPreview } from '@/features/notifications/components/NotificationPreview';
import * as notificationsApi from '@/lib/api/notifications';
import { NotificationSettings } from '@/types/notification';

// Mock the API functions
vi.mock('@/lib/api/notifications');
const mockNotificationsApi = notificationsApi as any;

// Mock toast
vi.mock('@/lib/toast', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

// Mock i18n context
const mockI18n = {
  t: (key: string) => {
    const translations: Record<string, string> = {
      'notification-frequency.title': 'Notification Frequency',
      'notification-frequency.description': 'Choose how often you want to receive notifications',
      'notification-frequency.immediate': 'Immediate',
      'notification-frequency.immediate-desc': 'Notify immediately when new articles are published',
      'notification-frequency.daily': 'Daily',
      'notification-frequency.daily-desc': 'Send daily digest at your preferred time',
      'notification-frequency.weekly': 'Weekly',
      'notification-frequency.weekly-desc': 'Send weekly digest at your preferred time',
      'notification-frequency.disabled': 'Disabled',
      'notification-frequency.disabled-desc': 'Do not receive any notifications',
      'settings.notifications.preview-title': 'Notification Preview',
      'settings.notifications.preview-desc': 'See how notifications will appear',
      'settings.notifications.will-trigger': 'Will send notification',
      'settings.notifications.will-not-trigger': 'Will not send notification',
      'settings.notifications.channel-discord': 'Discord DM',
      'settings.notifications.channel-email': 'Email',
      'settings.notifications.frequency-immediate': 'Immediate',
      'settings.notifications.frequency-daily': 'Daily',
      'settings.notifications.frequency-weekly': 'Weekly',
      'settings.notifications.new-article': 'New Article',
      'settings.notifications.immediate-send':
        'Notifications sent immediately when articles are published',
      'settings.notifications.daily-digest': 'Daily digest sent at your preferred time',
      'settings.notifications.weekly-digest': 'Weekly digest sent at your preferred time',
    };
    return translations[key] || key;
  },
  locale: 'en-US',
  setLocale: vi.fn(),
};

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <I18nProvider value={mockI18n}>{children}</I18nProvider>
    </QueryClientProvider>
  );
};

const mockPreferences = {
  id: '123e4567-e89b-12d3-a456-426614174000',
  userId: '123e4567-e89b-12d3-a456-426614174001',
  frequency: 'weekly' as const,
  notificationTime: '18:00',
  timezone: 'Asia/Taipei',
  dmEnabled: true,
  emailEnabled: false,
  createdAt: '2024-01-01T00:00:00Z',
  updatedAt: '2024-01-01T00:00:00Z',
};

const mockTimezones = [
  { value: 'Asia/Taipei', label: '台北 (Asia/Taipei)', offset: '+08:00' },
  { value: 'UTC', label: 'UTC', offset: '+00:00' },
  { value: 'America/New_York', label: '紐約 (America/New_York)', offset: '-05:00' },
];

const mockStatus = {
  scheduled: true,
  jobId: 'job-123',
  nextRunTime: '2024-01-05T18:00:00Z',
  message: '通知已排程',
};

const mockPreviewResponse = {
  nextNotificationTime: '2024-01-05T18:00:00Z',
  localTime: '2024-01-05T18:00:00+08:00',
  utcTime: '2024-01-05T10:00:00Z',
  message: '下次通知時間：2024-01-05 18:00 (Asia/Taipei)',
};

describe('Notification Settings Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockNotificationsApi.getNotificationPreferences.mockResolvedValue(mockPreferences);
    mockNotificationsApi.getSupportedTimezones.mockResolvedValue(mockTimezones);
    mockNotificationsApi.getNotificationStatus.mockResolvedValue(mockStatus);
    mockNotificationsApi.previewNotificationTime.mockResolvedValue(mockPreviewResponse);
    mockNotificationsApi.updateNotificationPreferences.mockResolvedValue(mockPreferences);
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('Complete User Workflow', () => {
    it('should handle complete notification preference setup workflow', async () => {
      const user = userEvent.setup();

      render(<PersonalizedNotificationSettings />, { wrapper: createWrapper() });

      // Wait for initial load
      await waitFor(() => {
        expect(screen.getByText('個人化通知設定')).toBeInTheDocument();
      });

      // Step 1: Enable Discord notifications
      const dmSwitch = screen.getByRole('switch', { name: /discord 私訊/i });
      expect(dmSwitch).toBeChecked();

      // Step 2: Change frequency to daily
      const frequencySelect = screen.getAllByRole('combobox')[0];
      await user.click(frequencySelect);

      const dailyOption = screen.getByText('每日');
      await user.click(dailyOption);

      await waitFor(() => {
        expect(mockNotificationsApi.updateNotificationPreferences).toHaveBeenCalledWith({
          frequency: 'daily',
        });
      });

      // Step 3: Change notification time
      const timeInput = screen.getByDisplayValue('18:00');
      await user.clear(timeInput);
      await user.type(timeInput, '09:00');

      await waitFor(() => {
        expect(mockNotificationsApi.updateNotificationPreferences).toHaveBeenCalledWith({
          notificationTime: '09:00',
        });
      });

      // Step 4: Change timezone
      const timezoneSelect = screen.getAllByRole('combobox')[1];
      await user.click(timezoneSelect);

      const utcOption = screen.getByText('UTC');
      await user.click(utcOption);

      await waitFor(() => {
        expect(mockNotificationsApi.updateNotificationPreferences).toHaveBeenCalledWith({
          timezone: 'UTC',
        });
      });

      // Verify preview updates were called
      expect(mockNotificationsApi.previewNotificationTime).toHaveBeenCalled();
    });

    it('should handle error recovery workflow', async () => {
      const user = userEvent.setup();

      // Mock initial API failure
      mockNotificationsApi.getNotificationPreferences.mockRejectedValueOnce(
        new Error('Network error')
      );

      render(<PersonalizedNotificationSettings />, { wrapper: createWrapper() });

      // Should show error state
      await waitFor(() => {
        expect(screen.getByText('無法載入通知偏好設定')).toBeInTheDocument();
      });

      // Mock successful retry
      mockNotificationsApi.getNotificationPreferences.mockResolvedValueOnce(mockPreferences);

      // Click retry button
      const retryButton = screen.getByRole('button', { name: /重試|retry/i });
      await user.click(retryButton);

      // Should load successfully after retry
      await waitFor(() => {
        expect(screen.getByText('個人化通知設定')).toBeInTheDocument();
      });
    });

    it('should handle partial update failures gracefully', async () => {
      const user = userEvent.setup();

      render(<PersonalizedNotificationSettings />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('個人化通知設定')).toBeInTheDocument();
      });

      // Mock update failure
      mockNotificationsApi.updateNotificationPreferences.mockRejectedValueOnce(
        new Error('Update failed')
      );

      const dmSwitch = screen.getByRole('switch', { name: /discord 私訊/i });
      await user.click(dmSwitch);

      // Should handle error gracefully (error toast would be shown)
      await waitFor(() => {
        expect(mockNotificationsApi.updateNotificationPreferences).toHaveBeenCalled();
      });

      // Switch should return to original state
      expect(dmSwitch).toBeChecked();
    });
  });

  describe('Cross-Component Integration', () => {
    it('should integrate frequency selector with preview component', async () => {
      const user = userEvent.setup();
      const mockSettings: NotificationSettings = {
        dmEnabled: true,
        emailEnabled: false,
        frequency: 'immediate',
        minTinkeringIndex: 3,
        quietHours: { enabled: false, start: '22:00', end: '08:00' },
      };

      // Render both components
      const { rerender } = render(
        <div>
          <NotificationFrequencySelector
            frequency="immediate"
            onFrequencyChange={(freq) => {
              mockSettings.frequency = freq;
              rerender(
                <div>
                  <NotificationFrequencySelector frequency={freq} onFrequencyChange={() => {}} />
                  <NotificationPreview settings={mockSettings} />
                </div>
              );
            }}
          />
          <NotificationPreview settings={mockSettings} />
        </div>,
        { wrapper: createWrapper() }
      );

      // Wait for components to load
      await waitFor(() => {
        expect(screen.getByText('Notification Frequency')).toBeInTheDocument();
        expect(screen.getByText('Notification Preview')).toBeInTheDocument();
      });

      // Change frequency and verify preview updates
      const weeklyRadio = screen.getByRole('radio', { name: /weekly/i });
      await user.click(weeklyRadio);

      // Preview should show weekly frequency
      expect(screen.getByText('Weekly')).toBeInTheDocument();
    });

    it('should handle timezone changes affecting preview', async () => {
      const user = userEvent.setup();

      render(<PersonalizedNotificationSettings />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('個人化通知設定')).toBeInTheDocument();
      });

      // Change timezone
      const timezoneSelect = screen.getAllByRole('combobox')[1];
      await user.click(timezoneSelect);

      const nyOption = screen.getByText(/New_York/);
      await user.click(nyOption);

      await waitFor(() => {
        expect(mockNotificationsApi.updateNotificationPreferences).toHaveBeenCalledWith({
          timezone: 'America/New_York',
        });
      });

      // Preview should be updated with new timezone
      expect(mockNotificationsApi.previewNotificationTime).toHaveBeenCalledWith(
        mockPreferences.frequency,
        mockPreferences.notificationTime,
        'America/New_York'
      );
    });
  });

  describe('Real-time Updates', () => {
    it('should handle real-time status updates', async () => {
      vi.useFakeTimers();

      render(<PersonalizedNotificationSettings />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('個人化通知設定')).toBeInTheDocument();
      });

      // Initial status should be loaded
      expect(screen.getByText('已排程')).toBeInTheDocument();

      // Mock status change
      const updatedStatus = {
        ...mockStatus,
        scheduled: false,
        message: '通知未排程',
      };
      mockNotificationsApi.getNotificationStatus.mockResolvedValue(updatedStatus);

      // Fast-forward to trigger refetch (30 seconds interval)
      vi.advanceTimersByTime(30000);

      await waitFor(() => {
        expect(screen.getByText('未排程')).toBeInTheDocument();
      });

      vi.useRealTimers();
    });

    it('should handle concurrent updates correctly', async () => {
      const user = userEvent.setup();

      render(<PersonalizedNotificationSettings />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('個人化通知設定')).toBeInTheDocument();
      });

      // Simulate concurrent updates
      const dmSwitch = screen.getByRole('switch', { name: /discord 私訊/i });
      const timeInput = screen.getByDisplayValue('18:00');

      // Start both updates simultaneously
      const dmPromise = user.click(dmSwitch);
      const timePromise = user.clear(timeInput).then(() => user.type(timeInput, '20:00'));

      await Promise.all([dmPromise, timePromise]);

      // Both updates should be called
      await waitFor(() => {
        expect(mockNotificationsApi.updateNotificationPreferences).toHaveBeenCalledTimes(2);
      });
    });
  });

  describe('Performance and Optimization', () => {
    it('should debounce rapid preference changes', async () => {
      const user = userEvent.setup();
      vi.useFakeTimers();

      render(<PersonalizedNotificationSettings />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('個人化通知設定')).toBeInTheDocument();
      });

      const timeInput = screen.getByDisplayValue('18:00');

      // Simulate rapid typing
      await user.clear(timeInput);
      await user.type(timeInput, '1');
      vi.advanceTimersByTime(100);
      await user.type(timeInput, '9');
      vi.advanceTimersByTime(100);
      await user.type(timeInput, ':');
      vi.advanceTimersByTime(100);
      await user.type(timeInput, '0');
      vi.advanceTimersByTime(100);
      await user.type(timeInput, '0');

      // Should only trigger one API call after debounce
      vi.advanceTimersByTime(1000);

      await waitFor(() => {
        expect(mockNotificationsApi.updateNotificationPreferences).toHaveBeenCalledWith({
          notificationTime: '19:00',
        });
      });

      vi.useRealTimers();
    });

    it('should cache timezone data appropriately', async () => {
      const { rerender } = render(<PersonalizedNotificationSettings />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(screen.getByText('個人化通知設定')).toBeInTheDocument();
      });

      // First render should fetch timezones
      expect(mockNotificationsApi.getSupportedTimezones).toHaveBeenCalledTimes(1);

      // Re-render component
      rerender(<PersonalizedNotificationSettings />);

      // Should not fetch timezones again (cached for 5 minutes)
      expect(mockNotificationsApi.getSupportedTimezones).toHaveBeenCalledTimes(1);
    });
  });

  describe('Edge Cases and Error Handling', () => {
    it('should handle malformed API responses', async () => {
      mockNotificationsApi.getNotificationPreferences.mockResolvedValue({
        ...mockPreferences,
        frequency: 'invalid-frequency' as any,
        notificationTime: 'invalid-time',
      });

      render(<PersonalizedNotificationSettings />, { wrapper: createWrapper() });

      // Should handle gracefully and show error state or fallback
      await waitFor(() => {
        expect(screen.getByText('個人化通知設定')).toBeInTheDocument();
      });
    });

    it('should handle network timeouts', async () => {
      mockNotificationsApi.getNotificationPreferences.mockImplementation(
        () => new Promise((_, reject) => setTimeout(() => reject(new Error('Timeout')), 5000))
      );

      render(<PersonalizedNotificationSettings />, { wrapper: createWrapper() });

      // Should show loading state initially
      expect(screen.getByLabelText('Loading')).toBeInTheDocument();

      // After timeout, should show error state
      await waitFor(
        () => {
          expect(screen.getByText('無法載入通知偏好設定')).toBeInTheDocument();
        },
        { timeout: 6000 }
      );
    });

    it('should handle partial data scenarios', async () => {
      mockNotificationsApi.getSupportedTimezones.mockResolvedValue([]);
      mockNotificationsApi.getNotificationStatus.mockResolvedValue(null);

      render(<PersonalizedNotificationSettings />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('個人化通知設定')).toBeInTheDocument();
      });

      // Should handle empty timezones gracefully
      const timezoneSelect = screen.getAllByRole('combobox')[1];
      expect(timezoneSelect).toBeInTheDocument();

      // Should handle missing status gracefully
      expect(screen.queryByText('排程狀態')).not.toBeInTheDocument();
    });
  });

  describe('Accessibility Integration', () => {
    it('should maintain focus management during updates', async () => {
      const user = userEvent.setup();

      render(<PersonalizedNotificationSettings />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('個人化通知設定')).toBeInTheDocument();
      });

      const dmSwitch = screen.getByRole('switch', { name: /discord 私訊/i });
      dmSwitch.focus();

      await user.click(dmSwitch);

      // Focus should be maintained after update
      await waitFor(() => {
        expect(dmSwitch).toHaveFocus();
      });
    });

    it('should provide proper ARIA live regions for status updates', async () => {
      render(<PersonalizedNotificationSettings />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('個人化通知設定')).toBeInTheDocument();
      });

      // Status updates should be announced to screen readers
      const statusRegion = screen.getByText('已排程').closest('[role="status"]');
      expect(statusRegion).toBeInTheDocument();
    });

    it('should handle keyboard navigation correctly', async () => {
      const user = userEvent.setup();

      render(<PersonalizedNotificationSettings />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('個人化通知設定')).toBeInTheDocument();
      });

      // Tab through interactive elements
      await user.tab();
      expect(screen.getByRole('switch', { name: /discord 私訊/i })).toHaveFocus();

      await user.tab();
      expect(screen.getAllByRole('combobox')[0]).toHaveFocus();

      await user.tab();
      expect(screen.getByDisplayValue('18:00')).toHaveFocus();
    });
  });
});
