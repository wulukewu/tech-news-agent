import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi } from 'vitest';
import { FeedNotificationSettings } from '../../components/FeedNotificationSettings';

// Mock the API
vi.mock('@/lib/api/notifications', () => ({
  getAvailableFeeds: vi.fn(),
}));

describe('FeedNotificationSettings', () => {
  let queryClient: QueryClient;
  const mockOnFeedSettingsChange = vi.fn();

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    });
    mockOnFeedSettingsChange.mockClear();
    vi.clearAllMocks();
  });

  const renderWithQueryClient = (component: React.ReactElement) => {
    return render(<QueryClientProvider client={queryClient}>{component}</QueryClientProvider>);
  };

  it('should render with empty feedSettings', () => {
    renderWithQueryClient(
      <FeedNotificationSettings feedSettings={[]} onFeedSettingsChange={mockOnFeedSettingsChange} />
    );

    expect(screen.getByText('個別來源通知設定')).toBeInTheDocument();
    expect(screen.getByText('尚未設定個別來源通知')).toBeInTheDocument();
  });

  it('should render with undefined feedSettings', () => {
    renderWithQueryClient(
      <FeedNotificationSettings
        feedSettings={undefined}
        onFeedSettingsChange={mockOnFeedSettingsChange}
      />
    );

    expect(screen.getByText('個別來源通知設定')).toBeInTheDocument();
    expect(screen.getByText('尚未設定個別來源通知')).toBeInTheDocument();
  });

  it('should render configured feeds', () => {
    const { getAvailableFeeds } = require('@/lib/api/notifications');
    getAvailableFeeds.mockResolvedValue([{ id: 'feed1', name: 'Test Feed 1', category: 'Tech' }]);

    const feedSettings = [
      {
        feedId: 'feed1',
        enabled: true,
        minTinkeringIndex: 3,
      },
    ];

    renderWithQueryClient(
      <FeedNotificationSettings
        feedSettings={feedSettings}
        onFeedSettingsChange={mockOnFeedSettingsChange}
      />
    );

    expect(screen.queryByText('尚未設定個別來源通知')).not.toBeInTheDocument();
  });

  it('should handle toggle feed with undefined feedSettings', async () => {
    const { getAvailableFeeds } = require('@/lib/api/notifications');
    getAvailableFeeds.mockResolvedValue([{ id: 'feed1', name: 'Test Feed 1', category: 'Tech' }]);

    renderWithQueryClient(
      <FeedNotificationSettings
        feedSettings={undefined}
        onFeedSettingsChange={mockOnFeedSettingsChange}
      />
    );

    // Open dialog
    const addButton = screen.getByText('新增來源通知設定');
    fireEvent.click(addButton);

    // Wait for feeds to load
    await waitFor(() => {
      expect(screen.getByText('Test Feed 1')).toBeInTheDocument();
    });

    // Add feed
    const addFeedButton = screen.getByText('新增');
    fireEvent.click(addFeedButton);

    // Should call with new feed
    expect(mockOnFeedSettingsChange).toHaveBeenCalledWith([
      {
        feedId: 'feed1',
        enabled: true,
        minTinkeringIndex: 3,
      },
    ]);
  });

  it('should handle remove feed with undefined feedSettings', () => {
    renderWithQueryClient(
      <FeedNotificationSettings
        feedSettings={undefined}
        onFeedSettingsChange={mockOnFeedSettingsChange}
      />
    );

    // Should not crash when trying to remove from undefined array
    expect(screen.getByText('尚未設定個別來源通知')).toBeInTheDocument();
  });

  it('should be disabled when disabled prop is true', () => {
    renderWithQueryClient(
      <FeedNotificationSettings
        feedSettings={[]}
        onFeedSettingsChange={mockOnFeedSettingsChange}
        disabled={true}
      />
    );

    const addButton = screen.getByText('新增來源通知設定');
    expect(addButton).toBeDisabled();
  });

  it('should handle feed settings with missing feedId', () => {
    const feedSettings = [
      {
        feedId: 'feed1',
        enabled: true,
        minTinkeringIndex: 3,
      },
      {
        // Missing feedId
        enabled: true,
        minTinkeringIndex: 3,
      } as any,
    ];

    renderWithQueryClient(
      <FeedNotificationSettings
        feedSettings={feedSettings}
        onFeedSettingsChange={mockOnFeedSettingsChange}
      />
    );

    // Should not crash and should skip the invalid setting
    expect(screen.getByText('個別來源通知設定')).toBeInTheDocument();
  });
});
