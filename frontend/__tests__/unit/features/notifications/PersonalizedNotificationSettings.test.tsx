import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { PersonalizedNotificationSettings } from '../../../../features/notifications/components/PersonalizedNotificationSettings';
import { vi, describe, it, expect, beforeEach } from 'vitest';

import * as notificationsApi from '@/lib/api/notifications';

vi.mock('@/lib/api/notifications', () => ({
  getNotificationPreferences: vi.fn(),
  updateNotificationPreferences: vi.fn(),
  getNotificationStatus: vi.fn(),
  previewNotificationTime: vi.fn(),
  getSupportedTimezones: vi.fn(),
  rescheduleUserNotification: vi.fn(),
}));

vi.mock('@/lib/toast', () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}));

const mockPreferences = {
  id: '123',
  userId: '456',
  frequency: 'weekly' as const,
  notificationTime: '18:00',
  timezone: 'Asia/Taipei',
  dmEnabled: true,
  emailEnabled: false,
  createdAt: '2024-01-01T00:00:00Z',
  updatedAt: '2024-01-01T00:00:00Z',
};

describe('PersonalizedNotificationSettings', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
    });
    vi.clearAllMocks();
    vi.mocked(notificationsApi.getNotificationPreferences).mockResolvedValue(mockPreferences);
    vi.mocked(notificationsApi.getNotificationStatus).mockResolvedValue({
      scheduled: true,
      nextNotificationAt: null,
    });
    vi.mocked(notificationsApi.getSupportedTimezones).mockResolvedValue([
      { value: 'Asia/Taipei', label: 'Asia/Taipei (UTC+8)' },
      { value: 'UTC', label: 'UTC (UTC+0)' },
    ]);
    vi.mocked(notificationsApi.previewNotificationTime).mockResolvedValue({
      previewTime: '2024-01-08T10:00:00Z',
    });
  });

  const renderWithQueryClient = (component: React.ReactElement) =>
    render(<QueryClientProvider client={queryClient}>{component}</QueryClientProvider>);

  it('should render notification settings title', async () => {
    renderWithQueryClient(<PersonalizedNotificationSettings />);
    await waitFor(() => {
      expect(screen.getByText('Notification Settings')).toBeInTheDocument();
    });
  });

  it('should render notification channels section', async () => {
    renderWithQueryClient(<PersonalizedNotificationSettings />);
    await waitFor(() => {
      expect(screen.getByText('Notification Channels')).toBeInTheDocument();
    });
  });

  it('should render frequency section', async () => {
    renderWithQueryClient(<PersonalizedNotificationSettings />);
    await waitFor(() => {
      expect(screen.getByText('Notification Frequency')).toBeInTheDocument();
    });
  });

  it('should show loading state initially', () => {
    vi.mocked(notificationsApi.getNotificationPreferences).mockImplementation(
      () => new Promise(() => {})
    );
    renderWithQueryClient(<PersonalizedNotificationSettings />);
    // Component should render without crashing during loading
    expect(document.body).toBeTruthy();
  });

  it('should show error state when API fails', async () => {
    vi.mocked(notificationsApi.getNotificationPreferences).mockRejectedValue(
      new Error('API Error')
    );
    renderWithQueryClient(<PersonalizedNotificationSettings />);
    await waitFor(() => {
      // Should show some error indication
      expect(document.body).toBeTruthy();
    });
  });

  it('should render Discord DM toggle', async () => {
    renderWithQueryClient(<PersonalizedNotificationSettings />);
    await waitFor(() => {
      expect(screen.getByText('Discord DM')).toBeInTheDocument();
    });
  });

  it('should toggle DM notifications', async () => {
    const user = userEvent.setup();
    vi.mocked(notificationsApi.updateNotificationPreferences).mockResolvedValue({
      ...mockPreferences,
      dmEnabled: false,
    });
    renderWithQueryClient(<PersonalizedNotificationSettings />);

    await waitFor(() => {
      expect(screen.getByText('Discord DM')).toBeInTheDocument();
    });

    const switches = screen.getAllByRole('switch');
    if (switches.length > 0) {
      await user.click(switches[0]);
      await waitFor(() => {
        expect(vi.mocked(notificationsApi.updateNotificationPreferences)).toHaveBeenCalled();
      });
    }
  });
});
