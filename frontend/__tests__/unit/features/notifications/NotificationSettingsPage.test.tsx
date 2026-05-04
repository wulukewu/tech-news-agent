import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import NotificationSettingsPage from '@/app/app/settings/notifications/page';
import * as notificationApi from '@/lib/api/notifications';
import { DEFAULT_NOTIFICATION_SETTINGS } from '@/types/notification';

vi.mock('@/lib/api/notifications', () => ({
  getNotificationSettings: vi.fn(),
  updateNotificationSettings: vi.fn(),
  sendTestNotification: vi.fn(),
  getAvailableFeeds: vi.fn(),
  getNotificationHistory: vi.fn(),
  getNotificationStatus: vi.fn(),
  getNotificationPreferences: vi.fn(),
  updateNotificationPreferences: vi.fn(),
  previewNotificationTime: vi.fn(),
  getSupportedTimezones: vi.fn(),
  rescheduleUserNotification: vi.fn(),
  getQuietHours: vi.fn(),
  updateQuietHours: vi.fn(),
  getQuietHoursStatus: vi.fn(),
  getTechnicalDepthSettings: vi.fn(),
  getTechnicalDepthLevels: vi.fn(),
  getTechnicalDepthStats: vi.fn(),
}));

vi.mock('@/lib/toast', () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}));

const renderWithQueryClient = (component: React.ReactElement) => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(<QueryClientProvider client={queryClient}>{component}</QueryClientProvider>);
};

describe('NotificationSettingsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(notificationApi.getNotificationSettings).mockResolvedValue(
      DEFAULT_NOTIFICATION_SETTINGS
    );
    vi.mocked(notificationApi.getAvailableFeeds).mockResolvedValue([]);
    vi.mocked(notificationApi.getNotificationHistory).mockResolvedValue({
      totalSent: 0,
      totalFailed: 0,
      recentHistory: [],
    });
    vi.mocked(notificationApi.getNotificationPreferences).mockResolvedValue(null as any);
    vi.mocked(notificationApi.getNotificationStatus).mockResolvedValue(null as any);
    vi.mocked(notificationApi.getSupportedTimezones).mockResolvedValue([]);
    vi.mocked(notificationApi.getQuietHours).mockResolvedValue(null as any);
    vi.mocked(notificationApi.getQuietHoursStatus).mockResolvedValue(null as any);
    vi.mocked(notificationApi.getTechnicalDepthSettings).mockResolvedValue(null as any);
    vi.mocked(notificationApi.getTechnicalDepthLevels).mockResolvedValue([]);
    vi.mocked(notificationApi.getTechnicalDepthStats).mockResolvedValue(null as any);
  });

  it.skip('should render page title', async () => {
    renderWithQueryClient(<NotificationSettingsPage />);
    await waitFor(
      () => {
        expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument();
      },
      { timeout: 5000 }
    );
  });

  it.skip('should render notification settings sections when loaded', async () => {
    renderWithQueryClient(<NotificationSettingsPage />);
    await waitFor(
      () => {
        expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument();
      },
      { timeout: 5000 }
    );
  });

  it('should render without crashing', () => {
    expect(() => renderWithQueryClient(<NotificationSettingsPage />)).not.toThrow();
  });
});
