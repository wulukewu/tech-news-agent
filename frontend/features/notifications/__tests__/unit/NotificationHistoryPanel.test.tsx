import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi } from 'vitest';
import { NotificationHistoryPanel } from '../../components/NotificationHistoryPanel';

// Mock the API
vi.mock('@/lib/api/notifications', () => ({
  getNotificationHistory: vi.fn(),
}));

// Mock date-fns
vi.mock('date-fns', () => ({
  formatDistanceToNow: vi.fn(() => '2 小時前'),
}));

vi.mock('date-fns/locale', () => ({
  zhTW: {},
}));

describe('NotificationHistoryPanel', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    });
    vi.clearAllMocks();
  });

  const renderWithQueryClient = (component: React.ReactElement) => {
    return render(<QueryClientProvider client={queryClient}>{component}</QueryClientProvider>);
  };

  it('should show loading state', () => {
    const { getNotificationHistory } = require('@/lib/api/notifications');
    getNotificationHistory.mockImplementation(() => new Promise(() => {})); // Never resolves

    renderWithQueryClient(<NotificationHistoryPanel />);

    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  });

  it('should show error state', async () => {
    const { getNotificationHistory } = require('@/lib/api/notifications');
    getNotificationHistory.mockRejectedValue(new Error('API Error'));

    renderWithQueryClient(<NotificationHistoryPanel />);

    await waitFor(() => {
      expect(screen.getByText('API Error')).toBeInTheDocument();
    });
  });

  it('should show empty state when no data', async () => {
    const { getNotificationHistory } = require('@/lib/api/notifications');
    getNotificationHistory.mockResolvedValue(null);

    renderWithQueryClient(<NotificationHistoryPanel />);

    await waitFor(() => {
      expect(screen.getByText('尚無通知記錄')).toBeInTheDocument();
    });
  });

  it('should show empty state when recentHistory is undefined', async () => {
    const { getNotificationHistory } = require('@/lib/api/notifications');
    getNotificationHistory.mockResolvedValue({
      totalSent: 0,
      totalFailed: 0,
      lastSentAt: null,
      // recentHistory is undefined
    });

    renderWithQueryClient(<NotificationHistoryPanel />);

    await waitFor(() => {
      expect(screen.getByText('尚無通知記錄')).toBeInTheDocument();
    });
  });

  it('should show empty state when recentHistory is empty array', async () => {
    const { getNotificationHistory } = require('@/lib/api/notifications');
    getNotificationHistory.mockResolvedValue({
      totalSent: 0,
      totalFailed: 0,
      lastSentAt: null,
      recentHistory: [],
    });

    renderWithQueryClient(<NotificationHistoryPanel />);

    await waitFor(() => {
      expect(screen.getByText('尚無通知記錄')).toBeInTheDocument();
    });
  });

  it('should render notification history', async () => {
    const { getNotificationHistory } = require('@/lib/api/notifications');
    getNotificationHistory.mockResolvedValue({
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
      expect(screen.getByText('通知歷史記錄')).toBeInTheDocument();
      expect(screen.getByText('10')).toBeInTheDocument(); // totalSent
      expect(screen.getByText('2')).toBeInTheDocument(); // totalFailed
      expect(screen.getByText('Test Article')).toBeInTheDocument();
    });
  });

  it('should render different status badges', async () => {
    const { getNotificationHistory } = require('@/lib/api/notifications');
    getNotificationHistory.mockResolvedValue({
      totalSent: 3,
      totalFailed: 1,
      lastSentAt: new Date().toISOString(),
      recentHistory: [
        {
          id: '1',
          articleId: 'article1',
          articleTitle: 'Sent Article',
          sentAt: new Date().toISOString(),
          channel: 'dm',
          status: 'sent',
        },
        {
          id: '2',
          articleId: 'article2',
          articleTitle: 'Failed Article',
          sentAt: new Date().toISOString(),
          channel: 'email',
          status: 'failed',
          errorMessage: 'Send failed',
        },
        {
          id: '3',
          articleId: 'article3',
          articleTitle: 'Pending Article',
          sentAt: new Date().toISOString(),
          channel: 'dm',
          status: 'pending',
        },
      ],
    });

    renderWithQueryClient(<NotificationHistoryPanel />);

    await waitFor(() => {
      expect(screen.getByText('已發送')).toBeInTheDocument();
      expect(screen.getByText('失敗')).toBeInTheDocument();
      expect(screen.getByText('待發送')).toBeInTheDocument();
      expect(screen.getByText('Send failed')).toBeInTheDocument();
    });
  });
});
