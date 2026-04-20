import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { NotificationPreview } from '@/features/notifications/components/NotificationPreview';
import { NotificationSettings } from '@/types/notification';
import { I18nProvider } from '@/contexts/I18nContext';

// Mock date-fns to ensure consistent test results
vi.mock('date-fns', () => ({
  formatDistanceToNow: vi.fn(() => '30 minutes ago'),
  zhTW: {},
  enUS: {},
}));

// Mock i18n context
const mockI18n = {
  t: (key: string) => {
    const translations: Record<string, string> = {
      'settings.notifications.preview-title': 'Notification Preview',
      'settings.notifications.preview-desc': 'See how notifications will appear',
      'settings.notifications.will-trigger': 'Will send notification',
      'settings.notifications.will-not-trigger': 'Will not send notification',
      'settings.notifications.reason': 'Reason:',
      'settings.notifications.global-disabled': 'Notifications are disabled',
      'settings.notifications.below-threshold': 'Article technical depth',
      'settings.notifications.in-quiet-hours': 'Currently in quiet hours',
      'settings.notifications.send-channels': 'Will send via:',
      'settings.notifications.no-channels': 'No channels configured',
      'settings.notifications.new-article': 'New Article',
      'settings.notifications.frequency-immediate': 'Immediate',
      'settings.notifications.frequency-daily': 'Daily',
      'settings.notifications.frequency-weekly': 'Weekly',
      'settings.notifications.immediate-send':
        'Notifications sent immediately when articles are published',
      'settings.notifications.daily-digest': 'Daily digest sent at your preferred time',
      'settings.notifications.weekly-digest': 'Weekly digest sent at your preferred time',
      'settings.notifications.channel-discord': 'Discord DM',
      'settings.notifications.channel-email': 'Email',
      'settings.notifications.channel-in-app': 'In-App',
    };
    return translations[key] || key;
  },
  locale: 'en-US',
  setLocale: vi.fn(),
};

const renderWithI18n = (ui: React.ReactElement) => {
  return render(<I18nProvider value={mockI18n}>{ui}</I18nProvider>);
};

describe('NotificationPreview', () => {
  const baseSettings: NotificationSettings = {
    dmEnabled: true,
    emailEnabled: false,
    frequency: 'immediate',
    minTinkeringIndex: 3,
    quietHours: {
      enabled: false,
      start: '22:00',
      end: '08:00',
    },
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Notification Triggering Logic', () => {
    it('should show notification will trigger when all conditions are met', () => {
      renderWithI18n(<NotificationPreview settings={baseSettings} />);

      expect(screen.getByText('✓ Will send notification')).toBeInTheDocument();
      expect(screen.getByText('Will send via:')).toBeInTheDocument();
      expect(screen.getByText('Discord DM')).toBeInTheDocument();
    });

    it('should show notification will not trigger when DM is disabled', () => {
      const settings = { ...baseSettings, dmEnabled: false };
      renderWithI18n(<NotificationPreview settings={settings} />);

      expect(screen.getByText('✗ Will not send notification')).toBeInTheDocument();
      expect(screen.getByText('Notifications are disabled')).toBeInTheDocument();
    });

    it('should show notification will not trigger when article is below threshold', () => {
      const settings = { ...baseSettings, minTinkeringIndex: 5 };
      renderWithI18n(<NotificationPreview settings={settings} />);

      expect(screen.getByText('✗ Will not send notification')).toBeInTheDocument();
      expect(screen.getByText(/Article technical depth.*低於閾值/)).toBeInTheDocument();
    });

    it('should show notification will not trigger during quiet hours', () => {
      // Mock current time to be within quiet hours
      const mockDate = new Date('2024-01-01T23:00:00Z');
      vi.setSystemTime(mockDate);

      const settings = {
        ...baseSettings,
        quietHours: { enabled: true, start: '22:00', end: '08:00' },
      };
      renderWithI18n(<NotificationPreview settings={settings} />);

      expect(screen.getByText('✗ Will not send notification')).toBeInTheDocument();
      expect(screen.getByText('Currently in quiet hours')).toBeInTheDocument();

      vi.useRealTimers();
    });
  });

  describe('Channel Display', () => {
    it('should show Discord DM when enabled', () => {
      const settings = { ...baseSettings, dmEnabled: true };
      renderWithI18n(<NotificationPreview settings={settings} />);

      expect(screen.getByText('Discord DM')).toBeInTheDocument();
    });

    it('should show Email when enabled', () => {
      const settings = { ...baseSettings, emailEnabled: true };
      renderWithI18n(<NotificationPreview settings={settings} />);

      expect(screen.getByText('Email')).toBeInTheDocument();
    });

    it('should show both channels when both are enabled', () => {
      const settings = { ...baseSettings, dmEnabled: true, emailEnabled: true };
      renderWithI18n(<NotificationPreview settings={settings} />);

      expect(screen.getByText('Discord DM')).toBeInTheDocument();
      expect(screen.getByText('Email')).toBeInTheDocument();
    });

    it('should show no channels message when none are enabled', () => {
      const settings = { ...baseSettings, dmEnabled: false, emailEnabled: false };
      renderWithI18n(<NotificationPreview settings={settings} />);

      expect(screen.getByText('No channels configured')).toBeInTheDocument();
    });
  });

  describe('Frequency Display', () => {
    it('should show immediate frequency badge and description', () => {
      const settings = { ...baseSettings, frequency: 'immediate' };
      renderWithI18n(<NotificationPreview settings={settings} />);

      expect(screen.getByText('Immediate')).toBeInTheDocument();
      expect(
        screen.getByText('Notifications sent immediately when articles are published')
      ).toBeInTheDocument();
    });

    it('should show daily frequency badge and description', () => {
      const settings = { ...baseSettings, frequency: 'daily' };
      renderWithI18n(<NotificationPreview settings={settings} />);

      expect(screen.getByText('Daily')).toBeInTheDocument();
      expect(screen.getByText('Daily digest sent at your preferred time')).toBeInTheDocument();
    });

    it('should show weekly frequency badge and description', () => {
      const settings = { ...baseSettings, frequency: 'weekly' };
      renderWithI18n(<NotificationPreview settings={settings} />);

      expect(screen.getByText('Weekly')).toBeInTheDocument();
      expect(screen.getByText('Weekly digest sent at your preferred time')).toBeInTheDocument();
    });
  });

  describe('Article Preview', () => {
    it('should display mock article information', () => {
      renderWithI18n(<NotificationPreview settings={baseSettings} />);

      expect(
        screen.getByText('Next.js 15 發布：全新的 App Router 功能與效能提升')
      ).toBeInTheDocument();
      expect(screen.getByText('Vercel Blog')).toBeInTheDocument();
      expect(screen.getByText('Web Dev')).toBeInTheDocument();
      expect(screen.getByText('30 minutes ago')).toBeInTheDocument();
    });

    it('should display technical depth stars correctly', () => {
      renderWithI18n(<NotificationPreview settings={baseSettings} />);

      // Check that stars are rendered (mock article has tinkeringIndex: 4)
      const stars = screen.getAllByTestId(/star-/);
      expect(stars).toHaveLength(5); // Should render 5 stars total
    });

    it('should display category badge with correct styling', () => {
      renderWithI18n(<NotificationPreview settings={baseSettings} />);

      const categoryBadge = screen.getByText('Web Dev');
      expect(categoryBadge).toBeInTheDocument();
      expect(categoryBadge).toHaveClass('bg-green-100', 'text-green-800');
    });
  });

  describe('Visual States', () => {
    it('should apply success styling when notification will trigger', () => {
      renderWithI18n(<NotificationPreview settings={baseSettings} />);

      const statusIndicator = screen.getByText('✓ Will send notification').closest('div');
      expect(statusIndicator).toHaveClass('bg-green-50', 'border-green-200');
    });

    it('should apply error styling when notification will not trigger', () => {
      const settings = { ...baseSettings, dmEnabled: false };
      renderWithI18n(<NotificationPreview settings={settings} />);

      const statusIndicator = screen.getByText('✗ Will not send notification').closest('div');
      expect(statusIndicator).toHaveClass('bg-red-50', 'border-red-200');
    });

    it('should show reason section when notification will not trigger', () => {
      const settings = { ...baseSettings, dmEnabled: false };
      renderWithI18n(<NotificationPreview settings={settings} />);

      expect(screen.getByText('Reason:')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have proper heading structure', () => {
      renderWithI18n(<NotificationPreview settings={baseSettings} />);

      expect(screen.getByRole('heading', { name: 'Notification Preview' })).toBeInTheDocument();
    });

    it('should have descriptive text for screen readers', () => {
      renderWithI18n(<NotificationPreview settings={baseSettings} />);

      expect(screen.getByText('See how notifications will appear')).toBeInTheDocument();
    });

    it('should use semantic HTML elements', () => {
      renderWithI18n(<NotificationPreview settings={baseSettings} />);

      // Check for proper list structure in reasons
      const settings = { ...baseSettings, dmEnabled: false };
      renderWithI18n(<NotificationPreview settings={settings} />);

      const reasonsList = screen.getByRole('list');
      expect(reasonsList).toBeInTheDocument();
    });
  });
});
