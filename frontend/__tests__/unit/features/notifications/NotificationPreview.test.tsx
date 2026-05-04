import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { NotificationPreview } from '@/features/notifications/components/NotificationPreview';
import { NotificationSettings } from '@/types/notification';

vi.mock('date-fns', () => ({
  formatDistanceToNow: vi.fn(() => '30 minutes ago'),
}));

vi.mock('date-fns/locale', () => ({
  zhTW: {},
  enUS: {},
}));

describe('NotificationPreview', () => {
  const baseSettings: NotificationSettings = {
    dmEnabled: true,
    emailEnabled: false,
    frequency: 'immediate',
    minTinkeringIndex: 3,
    quietHours: { enabled: false, start: '22:00', end: '08:00' },
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should show notification will trigger when all conditions are met', () => {
    render(<NotificationPreview settings={baseSettings} />);
    expect(screen.getByText(/This article will trigger notification/)).toBeInTheDocument();
    expect(screen.getByText('Discord DM')).toBeInTheDocument();
  });

  it('should show notification will not trigger when DM is disabled', () => {
    const settings = { ...baseSettings, dmEnabled: false, emailEnabled: false };
    render(<NotificationPreview settings={settings} />);
    expect(screen.getByText(/This article will not trigger notification/)).toBeInTheDocument();
    expect(screen.getByText('Global notifications are disabled')).toBeInTheDocument();
  });

  it('should show notification will not trigger when article is below threshold', () => {
    const settings = { ...baseSettings, minTinkeringIndex: 6 };
    render(<NotificationPreview settings={settings} />);
    expect(screen.getByText(/This article will not trigger notification/)).toBeInTheDocument();
    expect(screen.getByText(/Technical depth below threshold/)).toBeInTheDocument();
  });

  it('should show notification will not trigger during quiet hours', () => {
    // Set time to 23:00 which is within 22:00-08:00 quiet hours
    vi.setSystemTime(new Date('2024-01-01T23:00:00'));
    const settings = {
      ...baseSettings,
      quietHours: { enabled: true, start: '22:00', end: '08:00' },
    };
    render(<NotificationPreview settings={settings} />);
    expect(screen.getByText(/This article will not trigger notification/)).toBeInTheDocument();
    expect(screen.getByText('Currently in quiet hours')).toBeInTheDocument();
    vi.useRealTimers();
  });

  it('should show Email when enabled', () => {
    const settings = { ...baseSettings, emailEnabled: true };
    render(<NotificationPreview settings={settings} />);
    expect(screen.getByText('Email')).toBeInTheDocument();
  });

  it('should show both channels when both are enabled', () => {
    const settings = { ...baseSettings, dmEnabled: true, emailEnabled: true };
    render(<NotificationPreview settings={settings} />);
    expect(screen.getByText('Discord DM')).toBeInTheDocument();
    expect(screen.getByText('Email')).toBeInTheDocument();
  });

  it('should show no channels message when none are enabled', () => {
    const settings = { ...baseSettings, dmEnabled: false, emailEnabled: false };
    render(<NotificationPreview settings={settings} />);
    expect(screen.getByText(/This article will not trigger notification/)).toBeInTheDocument();
  });

  it('should show daily frequency description', () => {
    const settings = { ...baseSettings, frequency: 'daily' as const };
    render(<NotificationPreview settings={settings} />);
    expect(screen.getByText('Notification will be included in daily digest')).toBeInTheDocument();
  });

  it('should show weekly frequency description', () => {
    const settings = { ...baseSettings, frequency: 'weekly' as const };
    render(<NotificationPreview settings={settings} />);
    expect(screen.getByText('Notification will be included in weekly digest')).toBeInTheDocument();
  });

  it('should display mock article information', () => {
    render(<NotificationPreview settings={baseSettings} />);
    expect(screen.getByText('Vercel Blog')).toBeInTheDocument();
    expect(screen.getByText('30 minutes ago')).toBeInTheDocument();
  });

  it('should have proper heading', () => {
    render(<NotificationPreview settings={baseSettings} />);
    expect(screen.getByText('Notification Preview')).toBeInTheDocument();
  });
});
