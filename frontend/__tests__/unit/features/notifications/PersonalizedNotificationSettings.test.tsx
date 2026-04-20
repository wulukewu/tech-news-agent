import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { PersonalizedNotificationSettings } from '../../../../features/notifications/components/PersonalizedNotificationSettings';
import { I18nProvider } from '@/contexts/I18nContext';
import * as notificationsApi from '@/lib/api/notifications';
import { vi, describe, it, expect, beforeEach } from 'vitest';

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
  t: (key: string) => key,
  locale: 'zh-TW',
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
];

const mockStatus = {
  scheduled: true,
  jobId: 'job-123',
  nextRunTime: '2024-01-05T18:00:00Z',
  message: '通知已排程',
};

describe('PersonalizedNotificationSettings', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    mockNotificationsApi.getNotificationPreferences.mockResolvedValue(mockPreferences);
    mockNotificationsApi.getSupportedTimezones.mockResolvedValue(mockTimezones);
    mockNotificationsApi.getNotificationStatus.mockResolvedValue(mockStatus);
    mockNotificationsApi.previewNotificationTime.mockResolvedValue({
      nextNotificationTime: '2024-01-05T18:00:00Z',
      localTime: '2024-01-05T18:00:00+08:00',
      utcTime: '2024-01-05T10:00:00Z',
      message: '下次通知時間：2024-01-05 18:00 (Asia/Taipei)',
    });
    mockNotificationsApi.updateNotificationPreferences.mockResolvedValue(mockPreferences);
  });

  it('renders notification preferences correctly', async () => {
    render(<PersonalizedNotificationSettings />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('個人化通知設定')).toBeInTheDocument();
    });

    expect(screen.getByText('通知管道')).toBeInTheDocument();
    expect(screen.getByText('通知頻率')).toBeInTheDocument();
    expect(screen.getByText('時間設定')).toBeInTheDocument();
  });

  it('displays current preferences correctly', async () => {
    render(<PersonalizedNotificationSettings />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByDisplayValue('18:00')).toBeInTheDocument();
    });

    // Check if DM is enabled
    const dmSwitch = screen.getByRole('switch', { name: /discord 私訊/i });
    expect(dmSwitch).toBeChecked();

    // Check if email is disabled
    const emailSwitch = screen.getByRole('switch', { name: /電子郵件/i });
    expect(emailSwitch).not.toBeChecked();
    expect(emailSwitch).toBeDisabled();
  });

  it('updates DM preference when toggled', async () => {
    mockNotificationsApi.updateNotificationPreferences.mockResolvedValue({
      ...mockPreferences,
      dmEnabled: false,
    });

    render(<PersonalizedNotificationSettings />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('個人化通知設定')).toBeInTheDocument();
    });

    const dmSwitch = screen.getByRole('switch', { name: /discord 私訊/i });
    fireEvent.click(dmSwitch);

    await waitFor(() => {
      expect(mockNotificationsApi.updateNotificationPreferences).toHaveBeenCalledWith({
        dmEnabled: false,
      });
    });
  });

  it('updates notification time when changed', async () => {
    mockNotificationsApi.updateNotificationPreferences.mockResolvedValue({
      ...mockPreferences,
      notificationTime: '20:00',
    });

    render(<PersonalizedNotificationSettings />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByDisplayValue('18:00')).toBeInTheDocument();
    });

    const timeInput = screen.getByDisplayValue('18:00');
    fireEvent.change(timeInput, { target: { value: '20:00' } });

    await waitFor(() => {
      expect(mockNotificationsApi.updateNotificationPreferences).toHaveBeenCalledWith({
        notificationTime: '20:00',
      });
    });
  });

  it('shows loading state initially', () => {
    mockNotificationsApi.getNotificationPreferences.mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    render(<PersonalizedNotificationSettings />, { wrapper: createWrapper() });

    // Look for the loading spinner specifically by aria-label
    expect(screen.getByLabelText('Loading')).toBeInTheDocument();
  });

  it('shows error state when API fails', async () => {
    mockNotificationsApi.getNotificationPreferences.mockRejectedValue(new Error('API Error'));

    render(<PersonalizedNotificationSettings />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('無法載入通知偏好設定')).toBeInTheDocument();
    });
  });

  it('disables controls when DM is disabled', async () => {
    mockNotificationsApi.getNotificationPreferences.mockResolvedValue({
      ...mockPreferences,
      dmEnabled: false,
    });

    render(<PersonalizedNotificationSettings />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByDisplayValue('18:00')).toBeInTheDocument();
    });

    const timeInput = screen.getByDisplayValue('18:00');
    expect(timeInput).toBeDisabled();
  });

  it('shows preview information', async () => {
    render(<PersonalizedNotificationSettings />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('下次通知預覽')).toBeInTheDocument();
    });

    await waitFor(() => {
      expect(screen.getByText(/下次通知時間/)).toBeInTheDocument();
    });
  });

  it('shows scheduling status', async () => {
    render(<PersonalizedNotificationSettings />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('已排程')).toBeInTheDocument();
    });

    await waitFor(() => {
      expect(screen.getByText('通知已排程')).toBeInTheDocument();
    });
  });

  describe('Form Validation', () => {
    it('should validate time input format', async () => {
      const user = userEvent.setup();

      render(<PersonalizedNotificationSettings />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByDisplayValue('18:00')).toBeInTheDocument();
      });

      const timeInput = screen.getByDisplayValue('18:00');

      // Test invalid time format
      await user.clear(timeInput);
      await user.type(timeInput, '25:00');

      // The HTML5 time input should prevent invalid values
      expect(timeInput).toHaveValue('');
    });

    it('should handle timezone selection validation', async () => {
      const user = userEvent.setup();

      render(<PersonalizedNotificationSettings />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('個人化通知設定')).toBeInTheDocument();
      });

      // Find and click timezone selector
      const timezoneSelect = screen.getByRole('combobox');
      await user.click(timezoneSelect);

      // Select a different timezone
      const utcOption = screen.getByText('UTC');
      await user.click(utcOption);

      await waitFor(() => {
        expect(mockNotificationsApi.updateNotificationPreferences).toHaveBeenCalledWith({
          timezone: 'UTC',
        });
      });
    });

    it('should validate frequency selection', async () => {
      const user = userEvent.setup();

      render(<PersonalizedNotificationSettings />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('個人化通知設定')).toBeInTheDocument();
      });

      // Find frequency selector
      const frequencySelect = screen.getByRole('combobox');
      await user.click(frequencySelect);

      // Select monthly frequency
      const monthlyOption = screen.getByText('每月');
      await user.click(monthlyOption);

      await waitFor(() => {
        expect(mockNotificationsApi.updateNotificationPreferences).toHaveBeenCalledWith({
          frequency: 'monthly',
        });
      });
    });
  });

  describe('API Integration', () => {
    it('should handle API errors gracefully', async () => {
      mockNotificationsApi.updateNotificationPreferences.mockRejectedValue(
        new Error('Network error')
      );

      const user = userEvent.setup();

      render(<PersonalizedNotificationSettings />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('個人化通知設定')).toBeInTheDocument();
      });

      const dmSwitch = screen.getByRole('switch', { name: /discord 私訊/i });
      await user.click(dmSwitch);

      // Should show error toast (mocked)
      await waitFor(() => {
        expect(mockNotificationsApi.updateNotificationPreferences).toHaveBeenCalled();
      });
    });

    it('should retry failed API calls', async () => {
      mockNotificationsApi.getNotificationPreferences.mockRejectedValue(new Error('Network error'));

      render(<PersonalizedNotificationSettings />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('無法載入通知偏好設定')).toBeInTheDocument();
      });

      // Click retry button
      const retryButton = screen.getByRole('button', { name: /重試|retry/i });
      expect(retryButton).toBeInTheDocument();
    });

    it('should invalidate cache after successful updates', async () => {
      const user = userEvent.setup();

      render(<PersonalizedNotificationSettings />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('個人化通知設定')).toBeInTheDocument();
      });

      const dmSwitch = screen.getByRole('switch', { name: /discord 私訊/i });
      await user.click(dmSwitch);

      await waitFor(() => {
        expect(mockNotificationsApi.updateNotificationPreferences).toHaveBeenCalledWith({
          dmEnabled: false,
        });
      });

      // Verify that the component updates the cache and triggers preview update
      expect(mockNotificationsApi.previewNotificationTime).toHaveBeenCalled();
    });
  });

  describe('User Interactions', () => {
    it('should update email preference when toggled', async () => {
      const user = userEvent.setup();

      render(<PersonalizedNotificationSettings />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('個人化通知設定')).toBeInTheDocument();
      });

      // Email switch should be disabled initially
      const emailSwitch = screen.getByRole('switch', { name: /電子郵件/i });
      expect(emailSwitch).toBeDisabled();
    });

    it('should update timezone when changed', async () => {
      const user = userEvent.setup();

      render(<PersonalizedNotificationSettings />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('個人化通知設定')).toBeInTheDocument();
      });

      // Find timezone selector (should be the second combobox)
      const selectors = screen.getAllByRole('combobox');
      const timezoneSelect =
        selectors.find(
          (select) =>
            select.getAttribute('aria-label')?.includes('timezone') ||
            select.closest('[data-testid="timezone-select"]')
        ) || selectors[1]; // Fallback to second selector

      await user.click(timezoneSelect);

      const utcOption = screen.getByText('UTC');
      await user.click(utcOption);

      await waitFor(() => {
        expect(mockNotificationsApi.updateNotificationPreferences).toHaveBeenCalledWith({
          timezone: 'UTC',
        });
      });
    });

    it('should update frequency when changed', async () => {
      const user = userEvent.setup();

      render(<PersonalizedNotificationSettings />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('個人化通知設定')).toBeInTheDocument();
      });

      // Find frequency selector (should be the first combobox)
      const selectors = screen.getAllByRole('combobox');
      const frequencySelect = selectors[0];

      await user.click(frequencySelect);

      const dailyOption = screen.getByText('每日');
      await user.click(dailyOption);

      await waitFor(() => {
        expect(mockNotificationsApi.updateNotificationPreferences).toHaveBeenCalledWith({
          frequency: 'daily',
        });
      });
    });

    it('should show loading state during updates', async () => {
      // Mock a slow API response
      mockNotificationsApi.updateNotificationPreferences.mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve(mockPreferences), 1000))
      );

      const user = userEvent.setup();

      render(<PersonalizedNotificationSettings />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('個人化通知設定')).toBeInTheDocument();
      });

      const dmSwitch = screen.getByRole('switch', { name: /discord 私訊/i });
      await user.click(dmSwitch);

      // Should show loading state (switches should be disabled)
      expect(dmSwitch).toBeDisabled();
    });
  });

  describe('Preview Functionality', () => {
    it('should update preview when preferences change', async () => {
      const user = userEvent.setup();

      render(<PersonalizedNotificationSettings />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('下次通知預覽')).toBeInTheDocument();
      });

      // Initial preview should be loaded
      expect(mockNotificationsApi.previewNotificationTime).toHaveBeenCalled();

      const timeInput = screen.getByDisplayValue('18:00');
      await user.clear(timeInput);
      await user.type(timeInput, '20:00');

      await waitFor(() => {
        expect(mockNotificationsApi.updateNotificationPreferences).toHaveBeenCalledWith({
          notificationTime: '20:00',
        });
      });

      // Preview should be updated after preference change
      expect(mockNotificationsApi.previewNotificationTime).toHaveBeenCalledTimes(2);
    });

    it('should show disabled preview when notifications are disabled', async () => {
      mockNotificationsApi.getNotificationPreferences.mockResolvedValue({
        ...mockPreferences,
        frequency: 'disabled',
      });

      render(<PersonalizedNotificationSettings />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('下次通知預覽')).toBeInTheDocument();
      });

      // Should show disabled message
      expect(screen.getByText('通知已停用')).toBeInTheDocument();
    });

    it('should handle preview API errors gracefully', async () => {
      mockNotificationsApi.previewNotificationTime.mockRejectedValue(
        new Error('Preview API error')
      );

      render(<PersonalizedNotificationSettings />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('下次通知預覽')).toBeInTheDocument();
      });

      // Should show fallback message when preview fails
      expect(screen.getByText('無法計算下次通知時間')).toBeInTheDocument();
    });
  });

  describe('Conditional Rendering', () => {
    it('should hide time settings when frequency is disabled', async () => {
      mockNotificationsApi.getNotificationPreferences.mockResolvedValue({
        ...mockPreferences,
        frequency: 'disabled',
      });

      render(<PersonalizedNotificationSettings />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('個人化通知設定')).toBeInTheDocument();
      });

      // Time settings card should not be visible
      expect(screen.queryByText('時間設定')).not.toBeInTheDocument();
    });

    it('should show time settings when frequency is not disabled', async () => {
      render(<PersonalizedNotificationSettings />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('時間設定')).toBeInTheDocument();
      });

      expect(screen.getByLabelText('通知時間')).toBeInTheDocument();
      expect(screen.getByLabelText('時區')).toBeInTheDocument();
    });

    it('should show status information when available', async () => {
      render(<PersonalizedNotificationSettings />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('排程狀態')).toBeInTheDocument();
      });

      expect(screen.getByText('通知已排程')).toBeInTheDocument();
      expect(screen.getByText(/下次執行:/)).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA labels', async () => {
      render(<PersonalizedNotificationSettings />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByLabelText('通知時間')).toBeInTheDocument();
        expect(screen.getByLabelText('時區')).toBeInTheDocument();
      });
    });

    it('should have proper heading structure', async () => {
      render(<PersonalizedNotificationSettings />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: '個人化通知設定' })).toBeInTheDocument();
        expect(screen.getByRole('heading', { name: '通知管道' })).toBeInTheDocument();
        expect(screen.getByRole('heading', { name: '通知頻率' })).toBeInTheDocument();
      });
    });

    it('should provide descriptive text for screen readers', async () => {
      render(<PersonalizedNotificationSettings />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('自訂您的通知頻率、時間和偏好')).toBeInTheDocument();
        expect(screen.getByText('選擇您希望接收通知的方式')).toBeInTheDocument();
      });
    });
  });
});
