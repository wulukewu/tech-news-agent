import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { NotificationPreview } from '../../components/NotificationPreview';
import { NotificationSettings } from '@/types/notification';

vi.mock('date-fns', () => ({
  formatDistanceToNow: vi.fn(() => '30 minutes ago'),
}));

vi.mock('date-fns/locale', () => ({
  zhTW: {},
  enUS: {},
}));

describe('NotificationPreview', () => {
  const mockSettings: NotificationSettings = {
    enabled: true,
    dmEnabled: true,
    emailEnabled: false,
    frequency: 'immediate',
    quietHours: { enabled: false, start: '22:00', end: '08:00' },
    minTinkeringIndex: 3,
    feedSettings: [],
    channels: ['dm', 'in-app'],
  };

  it('should show notification will be sent when conditions are met', () => {
    render(<NotificationPreview settings={mockSettings} />);
    expect(screen.getByText(/This article will trigger notification/)).toBeInTheDocument();
    expect(screen.getByText('Discord DM')).toBeInTheDocument();
  });

  it('should show notification will not be sent when globally disabled', () => {
    const disabledSettings = { ...mockSettings, dmEnabled: false, emailEnabled: false };
    render(<NotificationPreview settings={disabledSettings} />);
    expect(screen.getByText(/This article will not trigger notification/)).toBeInTheDocument();
    expect(screen.getByText('Global notifications are disabled')).toBeInTheDocument();
  });

  it('should show notification will not be sent when tinkering index is too low', () => {
    const highThresholdSettings = { ...mockSettings, minTinkeringIndex: 6 };
    render(<NotificationPreview settings={highThresholdSettings} />);
    expect(screen.getByText(/This article will not trigger notification/)).toBeInTheDocument();
    expect(screen.getByText(/Technical depth below threshold/)).toBeInTheDocument();
  });

  it('should show notification will not be sent during quiet hours', () => {
    vi.setSystemTime(new Date('2024-01-01T23:00:00'));
    const quietHoursSettings = {
      ...mockSettings,
      quietHours: { enabled: true, start: '22:00', end: '08:00' },
    };
    render(<NotificationPreview settings={quietHoursSettings} />);
    expect(screen.getByText(/This article will not trigger notification/)).toBeInTheDocument();
    expect(screen.getByText('Currently in quiet hours')).toBeInTheDocument();
    vi.useRealTimers();
  });

  it('should display correct frequency information for daily', () => {
    const dailySettings = { ...mockSettings, frequency: 'daily' as const };
    render(<NotificationPreview settings={dailySettings} />);
    expect(screen.getByText('Notification will be included in daily digest')).toBeInTheDocument();
  });

  it('should display correct frequency information for weekly', () => {
    const weeklySettings = { ...mockSettings, frequency: 'weekly' as const };
    render(<NotificationPreview settings={weeklySettings} />);
    expect(screen.getByText('Notification will be included in weekly digest')).toBeInTheDocument();
  });

  it('should show active channels when email is also enabled', () => {
    const multiChannelSettings = { ...mockSettings, emailEnabled: true };
    render(<NotificationPreview settings={multiChannelSettings} />);
    expect(screen.getByText('Discord DM')).toBeInTheDocument();
    expect(screen.getByText('Email')).toBeInTheDocument();
  });

  it('should show no active channels when all channels are disabled', () => {
    const noChannelSettings = { ...mockSettings, dmEnabled: false, emailEnabled: false };
    render(<NotificationPreview settings={noChannelSettings} />);
    // When no channels, notification won't trigger
    expect(screen.getByText(/This article will not trigger notification/)).toBeInTheDocument();
  });

  it('should display mock article information', () => {
    render(<NotificationPreview settings={mockSettings} />);
    expect(screen.getByText('Vercel Blog')).toBeInTheDocument();
    expect(screen.getByText('30 minutes ago')).toBeInTheDocument();
  });
});
