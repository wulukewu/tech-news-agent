import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { FeedNotificationSettings } from '@/features/notifications/components/FeedNotificationSettings';
import * as notificationsApi from '@/lib/api/notifications';

vi.mock('@/lib/api/notifications', () => ({
  getAvailableFeeds: vi.fn(),
}));

const mockAvailableFeeds = [
  { id: 'feed-1', name: 'TechCrunch', category: 'Tech News' },
  { id: 'feed-2', name: 'Hacker News', category: 'Tech Discussion' },
];

describe('FeedNotificationSettings', () => {
  let queryClient: QueryClient;
  const mockOnFeedSettingsChange = vi.fn();

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
    });
    vi.clearAllMocks();
    vi.mocked(notificationsApi.getAvailableFeeds).mockResolvedValue(mockAvailableFeeds);
  });

  const renderWithQueryClient = (component: React.ReactElement) =>
    render(<QueryClientProvider client={queryClient}>{component}</QueryClientProvider>);

  it('should render component title', () => {
    renderWithQueryClient(
      <FeedNotificationSettings feedSettings={[]} onFeedSettingsChange={mockOnFeedSettingsChange} />
    );
    expect(screen.getByText('Individual Feed Notification Settings')).toBeInTheDocument();
  });

  it('should show empty state when no feed settings are configured', () => {
    renderWithQueryClient(
      <FeedNotificationSettings feedSettings={[]} onFeedSettingsChange={mockOnFeedSettingsChange} />
    );
    expect(
      screen.getByText('No individual feed notification settings configured')
    ).toBeInTheDocument();
  });

  it('should render add feed button', () => {
    renderWithQueryClient(
      <FeedNotificationSettings feedSettings={[]} onFeedSettingsChange={mockOnFeedSettingsChange} />
    );
    expect(screen.getByText('Add Feed Notification Setting')).toBeInTheDocument();
  });

  it('should display configured feed settings', async () => {
    const feedSettings = [{ feedId: 'feed-1', enabled: true, minTinkeringIndex: 3 }];
    renderWithQueryClient(
      <FeedNotificationSettings
        feedSettings={feedSettings}
        onFeedSettingsChange={mockOnFeedSettingsChange}
      />
    );
    await waitFor(() => {
      expect(screen.getByText('TechCrunch')).toBeInTheDocument();
    });
  });

  it('should toggle feed enabled state when switch is clicked', async () => {
    const user = userEvent.setup();
    const feedSettings = [{ feedId: 'feed-1', enabled: true, minTinkeringIndex: 3 }];
    renderWithQueryClient(
      <FeedNotificationSettings
        feedSettings={feedSettings}
        onFeedSettingsChange={mockOnFeedSettingsChange}
      />
    );
    await waitFor(() => expect(screen.getByText('TechCrunch')).toBeInTheDocument());
    const feedSwitch = screen.getByRole('switch');
    await user.click(feedSwitch);
    expect(mockOnFeedSettingsChange).toHaveBeenCalledWith([
      { feedId: 'feed-1', enabled: false, minTinkeringIndex: 3 },
    ]);
  });

  it('should remove feed setting when remove button is clicked', async () => {
    const user = userEvent.setup();
    const feedSettings = [{ feedId: 'feed-1', enabled: true, minTinkeringIndex: 3 }];
    renderWithQueryClient(
      <FeedNotificationSettings
        feedSettings={feedSettings}
        onFeedSettingsChange={mockOnFeedSettingsChange}
      />
    );
    await waitFor(() => expect(screen.getByText('TechCrunch')).toBeInTheDocument());
    const removeButton = screen.getByTitle('Remove this feed setting');
    await user.click(removeButton);
    expect(mockOnFeedSettingsChange).toHaveBeenCalledWith([]);
  });

  it('should open dialog when add feed button is clicked', async () => {
    const user = userEvent.setup();
    renderWithQueryClient(
      <FeedNotificationSettings feedSettings={[]} onFeedSettingsChange={mockOnFeedSettingsChange} />
    );
    await user.click(screen.getByText('Add Feed Notification Setting'));
    await waitFor(() => {
      expect(screen.getByText('TechCrunch')).toBeInTheDocument();
    });
  });

  it('should add new feed setting when add button is clicked in dialog', async () => {
    const user = userEvent.setup();
    renderWithQueryClient(
      <FeedNotificationSettings feedSettings={[]} onFeedSettingsChange={mockOnFeedSettingsChange} />
    );
    await user.click(screen.getByText('Add Feed Notification Setting'));
    await waitFor(() => expect(screen.getByText('TechCrunch')).toBeInTheDocument());
    const addButtons = screen.getAllByText('Add');
    await user.click(addButtons[0]);
    expect(mockOnFeedSettingsChange).toHaveBeenCalledWith([
      { feedId: 'feed-1', enabled: true, minTinkeringIndex: 3 },
    ]);
  });

  it('should disable all controls when disabled prop is true', async () => {
    const feedSettings = [{ feedId: 'feed-1', enabled: true, minTinkeringIndex: 3 }];
    renderWithQueryClient(
      <FeedNotificationSettings
        feedSettings={feedSettings}
        onFeedSettingsChange={mockOnFeedSettingsChange}
        disabled={true}
      />
    );
    await waitFor(() => expect(screen.getByText('TechCrunch')).toBeInTheDocument());
    expect(screen.getByRole('switch')).toBeDisabled();
    expect(screen.getByText('Add Feed Notification Setting').closest('button')).toBeDisabled();
  });

  it('should handle undefined feedSettings gracefully', () => {
    renderWithQueryClient(
      <FeedNotificationSettings
        feedSettings={undefined}
        onFeedSettingsChange={mockOnFeedSettingsChange}
      />
    );
    expect(
      screen.getByText('No individual feed notification settings configured')
    ).toBeInTheDocument();
  });
});
