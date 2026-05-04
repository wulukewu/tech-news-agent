import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { NotificationHistoryPanel } from '../../components/NotificationHistoryPanel';

import * as notificationsApi from '@/lib/api/notifications';

vi.mock('@/lib/api/notifications', () => ({
  getNotificationHistory: vi.fn(),
  getQuietHours: vi.fn().mockResolvedValue(null),
  getQuietHoursStatus: vi.fn().mockResolvedValue(null),
  getSupportedTimezones: vi.fn().mockResolvedValue([]),
  updateQuietHours: vi.fn(),
}));

vi.mock('date-fns', () => ({
  formatDistanceToNow: vi.fn(() => '2 hours ago'),
}));

vi.mock('date-fns/locale', () => ({
  zhTW: {},
}));

describe('NotificationHistoryPanel', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    vi.clearAllMocks();
  });

  const renderWithQueryClient = (component: React.ReactElement) =>
    render(<QueryClientProvider client={queryClient}>{component}</QueryClientProvider>);

  it.skip('should show loading state', () => {
    vi.mocked(notificationsApi.getNotificationHistory).mockImplementation(
      () => new Promise(() => {})
    );
    renderWithQueryClient(<NotificationHistoryPanel />);
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  });

  it('should show error state', async () => {
    vi.mocked(notificationsApi.getNotificationHistory).mockRejectedValue(new Error('API Error'));
    renderWithQueryClient(<NotificationHistoryPanel />);
    await waitFor(() => {
      expect(screen.getByText('API Error')).toBeInTheDocument();
    });
  });

  it('should show empty state when no data', async () => {
    vi.mocked(notificationsApi.getNotificationHistory).mockResolvedValue(null);
    renderWithQueryClient(<NotificationHistoryPanel />);
    await waitFor(() => {
      expect(screen.getByText(/no notification|尚無通知/i)).toBeInTheDocument();
    });
  });

  it('should show empty state when recentHistory is empty array', async () => {
    vi.mocked(notificationsApi.getNotificationHistory).mockResolvedValue({
      totalSent: 0,
      totalFailed: 0,
      lastSentAt: null,
      recentHistory: [],
    });
    renderWithQueryClient(<NotificationHistoryPanel />);
    await waitFor(() => {
      expect(screen.getByText(/no notification|尚無通知/i)).toBeInTheDocument();
    });
  });

  it('should render notification history', async () => {
    vi.mocked(notificationsApi.getNotificationHistory).mockResolvedValue({
      totalSent: 10,
      totalFailed: 2,
      lastSentAt: new Date().toISOString(),
      recentHistory: [
        {
          id: '1',
          articleId: 'article1',
          articleTitle: 'Test Article',
          sentAt: new Date().toISOString(),
          channel: 'dm',
          status: 'sent',
        },
      ],
    });
    renderWithQueryClient(<NotificationHistoryPanel />);
    await waitFor(() => {
      expect(screen.getByText('Test Article')).toBeInTheDocument();
    });
  });
});
