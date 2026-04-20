import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { FeedNotificationSettings } from '@/features/notifications/components/FeedNotificationSettings';
import { FeedNotificationSettings as FeedSettings } from '@/types/notification';
import { I18nProvider } from '@/contexts/I18nContext';
import * as notificationsApi from '@/lib/api/notifications';

// Mock the API functions
vi.mock('@/lib/api/notifications');
const mockNotificationsApi = notificationsApi as any;

// Mock i18n context
const mockI18n = {
  t: (key: string) => {
    const translations: Record<string, string> = {
      'settings.notifications.feed-settings-title': 'Feed Notification Settings',
      'settings.notifications.feed-settings-desc': 'Configure notifications for specific RSS feeds',
      'settings.notifications.no-feed-settings-title': 'No feed settings configured',
      'settings.notifications.no-feed-settings-desc':
        'Add RSS feeds to customize notification preferences',
      'settings.notifications.add-feed-setting': 'Add Feed Setting',
      'settings.notifications.remove-feed-setting': 'Remove feed setting',
      'settings.notifications.min-technical-depth': 'Minimum technical depth:',
      'settings.notifications.select-rss-source': 'Select RSS Source',
      'settings.notifications.select-source-desc':
        'Choose which RSS feeds to configure for notifications',
      'settings.notifications.configured': 'Configured',
      'settings.notifications.add': 'Add',
      'settings.notifications.no-available-sources': 'No RSS sources available',
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

const mockAvailableFeeds = [
  { id: 'feed-1', name: 'TechCrunch', category: 'Tech News' },
  { id: 'feed-2', name: 'Hacker News', category: 'Tech Discussion' },
  { id: 'feed-3', name: 'Dev.to', category: 'Development' },
];

describe('FeedNotificationSettings', () => {
  const mockOnFeedSettingsChange = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    mockNotificationsApi.getAvailableFeeds.mockResolvedValue(mockAvailableFeeds);
  });

  describe('Initial Rendering', () => {
    it('should render component title and description', async () => {
      render(
        <FeedNotificationSettings
          feedSettings={[]}
          onFeedSettingsChange={mockOnFeedSettingsChange}
        />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('Feed Notification Settings')).toBeInTheDocument();
      expect(
        screen.getByText('Configure notifications for specific RSS feeds')
      ).toBeInTheDocument();
    });

    it('should show empty state when no feed settings are configured', async () => {
      render(
        <FeedNotificationSettings
          feedSettings={[]}
          onFeedSettingsChange={mockOnFeedSettingsChange}
        />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('No feed settings configured')).toBeInTheDocument();
      expect(
        screen.getByText('Add RSS feeds to customize notification preferences')
      ).toBeInTheDocument();
    });

    it('should render add feed button', async () => {
      render(
        <FeedNotificationSettings
          feedSettings={[]}
          onFeedSettingsChange={mockOnFeedSettingsChange}
        />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByRole('button', { name: 'Add Feed Setting' })).toBeInTheDocument();
    });
  });

  describe('Feed Settings Display', () => {
    const mockFeedSettings: FeedSettings[] = [
      { feedId: 'feed-1', enabled: true, minTinkeringIndex: 3 },
      { feedId: 'feed-2', enabled: false, minTinkeringIndex: 4 },
    ];

    it('should display configured feed settings', async () => {
      render(
        <FeedNotificationSettings
          feedSettings={mockFeedSettings}
          onFeedSettingsChange={mockOnFeedSettingsChange}
        />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(screen.getByText('TechCrunch')).toBeInTheDocument();
        expect(screen.getByText('Hacker News')).toBeInTheDocument();
      });

      expect(screen.getByText('Tech News')).toBeInTheDocument();
      expect(screen.getByText('Tech Discussion')).toBeInTheDocument();
    });

    it('should show correct switch states for enabled/disabled feeds', async () => {
      render(
        <FeedNotificationSettings
          feedSettings={mockFeedSettings}
          onFeedSettingsChange={mockOnFeedSettingsChange}
        />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        const switches = screen.getAllByRole('switch');
        expect(switches[0]).toBeChecked(); // TechCrunch enabled
        expect(switches[1]).not.toBeChecked(); // Hacker News disabled
      });
    });

    it('should display technical depth slider for enabled feeds', async () => {
      render(
        <FeedNotificationSettings
          feedSettings={mockFeedSettings}
          onFeedSettingsChange={mockOnFeedSettingsChange}
        />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(screen.getByText('Minimum technical depth:')).toBeInTheDocument();
      });

      // Should show stars for the technical depth
      const stars = screen.getAllByTestId(/star-/);
      expect(stars.length).toBeGreaterThan(0);
    });

    it('should show remove buttons for each feed setting', async () => {
      render(
        <FeedNotificationSettings
          feedSettings={mockFeedSettings}
          onFeedSettingsChange={mockOnFeedSettingsChange}
        />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        const removeButtons = screen.getAllByTitle('Remove feed setting');
        expect(removeButtons).toHaveLength(2);
      });
    });
  });

  describe('User Interactions', () => {
    const mockFeedSettings: FeedSettings[] = [
      { feedId: 'feed-1', enabled: true, minTinkeringIndex: 3 },
    ];

    it('should toggle feed enabled state when switch is clicked', async () => {
      const user = userEvent.setup();

      render(
        <FeedNotificationSettings
          feedSettings={mockFeedSettings}
          onFeedSettingsChange={mockOnFeedSettingsChange}
        />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(screen.getByText('TechCrunch')).toBeInTheDocument();
      });

      const feedSwitch = screen.getByRole('switch');
      await user.click(feedSwitch);

      expect(mockOnFeedSettingsChange).toHaveBeenCalledWith([
        { feedId: 'feed-1', enabled: false, minTinkeringIndex: 3 },
      ]);
    });

    it('should remove feed setting when remove button is clicked', async () => {
      const user = userEvent.setup();

      render(
        <FeedNotificationSettings
          feedSettings={mockFeedSettings}
          onFeedSettingsChange={mockOnFeedSettingsChange}
        />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(screen.getByText('TechCrunch')).toBeInTheDocument();
      });

      const removeButton = screen.getByTitle('Remove feed setting');
      await user.click(removeButton);

      expect(mockOnFeedSettingsChange).toHaveBeenCalledWith([]);
    });

    it('should update technical depth when slider is changed', async () => {
      render(
        <FeedNotificationSettings
          feedSettings={mockFeedSettings}
          onFeedSettingsChange={mockOnFeedSettingsChange}
        />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(screen.getByText('TechCrunch')).toBeInTheDocument();
      });

      // Find the slider input
      const slider = screen.getByRole('slider');
      fireEvent.change(slider, { target: { value: '4' } });

      expect(mockOnFeedSettingsChange).toHaveBeenCalledWith([
        { feedId: 'feed-1', enabled: true, minTinkeringIndex: 4 },
      ]);
    });
  });

  describe('Add Feed Dialog', () => {
    it('should open dialog when add feed button is clicked', async () => {
      const user = userEvent.setup();

      render(
        <FeedNotificationSettings
          feedSettings={[]}
          onFeedSettingsChange={mockOnFeedSettingsChange}
        />,
        { wrapper: createWrapper() }
      );

      const addButton = screen.getByRole('button', { name: 'Add Feed Setting' });
      await user.click(addButton);

      await waitFor(() => {
        expect(screen.getByText('Select RSS Source')).toBeInTheDocument();
        expect(
          screen.getByText('Choose which RSS feeds to configure for notifications')
        ).toBeInTheDocument();
      });
    });

    it('should display available feeds in dialog', async () => {
      const user = userEvent.setup();

      render(
        <FeedNotificationSettings
          feedSettings={[]}
          onFeedSettingsChange={mockOnFeedSettingsChange}
        />,
        { wrapper: createWrapper() }
      );

      const addButton = screen.getByRole('button', { name: 'Add Feed Setting' });
      await user.click(addButton);

      await waitFor(() => {
        expect(screen.getByText('TechCrunch')).toBeInTheDocument();
        expect(screen.getByText('Hacker News')).toBeInTheDocument();
        expect(screen.getByText('Dev.to')).toBeInTheDocument();
      });
    });

    it('should show configured status for already configured feeds', async () => {
      const user = userEvent.setup();
      const existingSettings: FeedSettings[] = [
        { feedId: 'feed-1', enabled: true, minTinkeringIndex: 3 },
      ];

      render(
        <FeedNotificationSettings
          feedSettings={existingSettings}
          onFeedSettingsChange={mockOnFeedSettingsChange}
        />,
        { wrapper: createWrapper() }
      );

      const addButton = screen.getByRole('button', { name: 'Add Feed Setting' });
      await user.click(addButton);

      await waitFor(() => {
        expect(screen.getByText('Configured')).toBeInTheDocument();
      });

      // The configured feed button should be disabled
      const configuredButton = screen.getByText('Configured').closest('button');
      expect(configuredButton).toBeDisabled();
    });

    it('should add new feed setting when add button is clicked', async () => {
      const user = userEvent.setup();

      render(
        <FeedNotificationSettings
          feedSettings={[]}
          onFeedSettingsChange={mockOnFeedSettingsChange}
        />,
        { wrapper: createWrapper() }
      );

      const addButton = screen.getByRole('button', { name: 'Add Feed Setting' });
      await user.click(addButton);

      await waitFor(() => {
        expect(screen.getByText('TechCrunch')).toBeInTheDocument();
      });

      const feedAddButton = screen.getAllByText('Add')[0].closest('button');
      await user.click(feedAddButton!);

      expect(mockOnFeedSettingsChange).toHaveBeenCalledWith([
        { feedId: 'feed-1', enabled: true, minTinkeringIndex: 3 },
      ]);
    });

    it('should show loading state while fetching available feeds', async () => {
      mockNotificationsApi.getAvailableFeeds.mockImplementation(
        () => new Promise(() => {}) // Never resolves
      );

      const user = userEvent.setup();

      render(
        <FeedNotificationSettings
          feedSettings={[]}
          onFeedSettingsChange={mockOnFeedSettingsChange}
        />,
        { wrapper: createWrapper() }
      );

      const addButton = screen.getByRole('button', { name: 'Add Feed Setting' });
      await user.click(addButton);

      await waitFor(() => {
        expect(screen.getByLabelText('Loading')).toBeInTheDocument();
      });
    });

    it('should show empty state when no feeds are available', async () => {
      mockNotificationsApi.getAvailableFeeds.mockResolvedValue([]);

      const user = userEvent.setup();

      render(
        <FeedNotificationSettings
          feedSettings={[]}
          onFeedSettingsChange={mockOnFeedSettingsChange}
        />,
        { wrapper: createWrapper() }
      );

      const addButton = screen.getByRole('button', { name: 'Add Feed Setting' });
      await user.click(addButton);

      await waitFor(() => {
        expect(screen.getByText('No RSS sources available')).toBeInTheDocument();
      });
    });
  });

  describe('Disabled State', () => {
    const mockFeedSettings: FeedSettings[] = [
      { feedId: 'feed-1', enabled: true, minTinkeringIndex: 3 },
    ];

    it('should disable all controls when disabled prop is true', async () => {
      render(
        <FeedNotificationSettings
          feedSettings={mockFeedSettings}
          onFeedSettingsChange={mockOnFeedSettingsChange}
          disabled={true}
        />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(screen.getByText('TechCrunch')).toBeInTheDocument();
      });

      // Check that controls are disabled
      expect(screen.getByRole('switch')).toBeDisabled();
      expect(screen.getByRole('slider')).toBeDisabled();
      expect(screen.getByTitle('Remove feed setting')).toBeDisabled();
      expect(screen.getByRole('button', { name: 'Add Feed Setting' })).toBeDisabled();
    });
  });

  describe('Edge Cases', () => {
    it('should handle undefined feedSettings gracefully', async () => {
      render(
        <FeedNotificationSettings
          feedSettings={undefined}
          onFeedSettingsChange={mockOnFeedSettingsChange}
        />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('No feed settings configured')).toBeInTheDocument();
    });

    it('should handle feed settings with missing feedId', async () => {
      const invalidSettings: FeedSettings[] = [
        { feedId: '', enabled: true, minTinkeringIndex: 3 },
        { feedId: 'feed-1', enabled: true, minTinkeringIndex: 3 },
      ];

      render(
        <FeedNotificationSettings
          feedSettings={invalidSettings}
          onFeedSettingsChange={mockOnFeedSettingsChange}
        />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        // Should only render the valid feed setting
        expect(screen.getByText('TechCrunch')).toBeInTheDocument();
      });

      // Should not render the invalid setting
      expect(screen.queryByText('')).not.toBeInTheDocument();
    });

    it('should handle API errors gracefully', async () => {
      mockNotificationsApi.getAvailableFeeds.mockRejectedValue(new Error('API Error'));

      const user = userEvent.setup();

      render(
        <FeedNotificationSettings
          feedSettings={[]}
          onFeedSettingsChange={mockOnFeedSettingsChange}
        />,
        { wrapper: createWrapper() }
      );

      const addButton = screen.getByRole('button', { name: 'Add Feed Setting' });
      await user.click(addButton);

      // Should show empty state when API fails
      await waitFor(() => {
        expect(screen.getByText('No RSS sources available')).toBeInTheDocument();
      });
    });
  });

  describe('Accessibility', () => {
    const mockFeedSettings: FeedSettings[] = [
      { feedId: 'feed-1', enabled: true, minTinkeringIndex: 3 },
    ];

    it('should have proper ARIA labels and roles', async () => {
      render(
        <FeedNotificationSettings
          feedSettings={mockFeedSettings}
          onFeedSettingsChange={mockOnFeedSettingsChange}
        />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(screen.getByRole('switch')).toBeInTheDocument();
        expect(screen.getByRole('slider')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Add Feed Setting' })).toBeInTheDocument();
      });
    });

    it('should have proper heading structure', async () => {
      render(
        <FeedNotificationSettings
          feedSettings={mockFeedSettings}
          onFeedSettingsChange={mockOnFeedSettingsChange}
        />,
        { wrapper: createWrapper() }
      );

      expect(
        screen.getByRole('heading', { name: 'Feed Notification Settings' })
      ).toBeInTheDocument();
    });

    it('should provide descriptive button titles', async () => {
      render(
        <FeedNotificationSettings
          feedSettings={mockFeedSettings}
          onFeedSettingsChange={mockOnFeedSettingsChange}
        />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(screen.getByTitle('Remove feed setting')).toBeInTheDocument();
      });
    });
  });
});
