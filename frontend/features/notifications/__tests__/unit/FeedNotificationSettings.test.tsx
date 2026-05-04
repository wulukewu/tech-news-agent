import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { FeedNotificationSettings } from '../../components/FeedNotificationSettings';

import * as notificationsApi from '@/lib/api/notifications';

vi.mock('@/lib/api/notifications', () => ({
  getAvailableFeeds: vi.fn(),
}));

describe('FeedNotificationSettings', () => {
  let queryClient: QueryClient;
  const mockOnFeedSettingsChange = vi.fn();

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    vi.clearAllMocks();
    vi.mocked(notificationsApi.getAvailableFeeds).mockResolvedValue([]);
  });

  const renderWithQueryClient = (component: React.ReactElement) =>
    render(<QueryClientProvider client={queryClient}>{component}</QueryClientProvider>);

  it('should render with empty feedSettings', () => {
    renderWithQueryClient(
      <FeedNotificationSettings feedSettings={[]} onFeedSettingsChange={mockOnFeedSettingsChange} />
    );
    expect(screen.getByText('Individual Feed Notification Settings')).toBeInTheDocument();
    expect(
      screen.getByText('No individual feed notification settings configured')
    ).toBeInTheDocument();
  });

  it('should render with undefined feedSettings', () => {
    renderWithQueryClient(
      <FeedNotificationSettings
        feedSettings={undefined}
        onFeedSettingsChange={mockOnFeedSettingsChange}
      />
    );
    expect(screen.getByText('Individual Feed Notification Settings')).toBeInTheDocument();
    expect(
      screen.getByText('No individual feed notification settings configured')
    ).toBeInTheDocument();
  });

  it('should render configured feeds', async () => {
    vi.mocked(notificationsApi.getAvailableFeeds).mockResolvedValue([
      { id: 'feed1', name: 'Test Feed 1', category: 'Tech' },
    ]);
    const feedSettings = [{ feedId: 'feed1', enabled: true, minTinkeringIndex: 3 }];

    renderWithQueryClient(
      <FeedNotificationSettings
        feedSettings={feedSettings}
        onFeedSettingsChange={mockOnFeedSettingsChange}
      />
    );
    expect(
      screen.queryByText('No individual feed notification settings configured')
    ).not.toBeInTheDocument();
  });

  it('should be disabled when disabled prop is true', () => {
    renderWithQueryClient(
      <FeedNotificationSettings
        feedSettings={[]}
        onFeedSettingsChange={mockOnFeedSettingsChange}
        disabled={true}
      />
    );
    const addButton = screen.getByText('Add Feed Notification Setting');
    expect(addButton).toBeDisabled();
  });

  it('should open dialog when add button is clicked', async () => {
    vi.mocked(notificationsApi.getAvailableFeeds).mockResolvedValue([
      { id: 'feed1', name: 'Test Feed 1', category: 'Tech' },
    ]);

    renderWithQueryClient(
      <FeedNotificationSettings feedSettings={[]} onFeedSettingsChange={mockOnFeedSettingsChange} />
    );

    const addButton = screen.getByText('Add Feed Notification Setting');
    fireEvent.click(addButton);

    await waitFor(() => {
      expect(screen.getByText('Test Feed 1')).toBeInTheDocument();
    });
  });
});
