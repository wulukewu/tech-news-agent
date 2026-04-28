import { render, screen } from '@testing-library/react';
import { NotificationPreview } from '../../components/NotificationPreview';
import { NotificationSettings } from '@/types/notification';

// Mock date-fns
vi.mock('date-fns', () => ({
  formatDistanceToNow: vi.fn(() => '30 分鐘前'),
}));

vi.mock('date-fns/locale', () => ({
  zhTW: {},
}));

describe('NotificationPreview', () => {
  const mockSettings: NotificationSettings = {
    enabled: true,
    dmEnabled: true,
    emailEnabled: false,
    frequency: 'immediate',
    quietHours: {
      enabled: false,
      start: '22:00',
      end: '08:00',
    },
    minTinkeringIndex: 3,
    feedSettings: [],
    channels: ['dm', 'in-app'],
  };

  it('should show notification will be sent when conditions are met', () => {
    render(<NotificationPreview settings={mockSettings} />);

    expect(screen.getByText('此文章會觸發通知')).toBeInTheDocument();
    expect(screen.getByText('通知將立即發送')).toBeInTheDocument();
    expect(screen.getByText('Discord DM')).toBeInTheDocument();
  });

  it('should show notification will not be sent when globally disabled', () => {
    const disabledSettings = { ...mockSettings, enabled: false };
    render(<NotificationPreview settings={disabledSettings} />);

    expect(screen.getByText('此文章不會觸發通知')).toBeInTheDocument();
    expect(screen.getByText('全域通知已停用')).toBeInTheDocument();
  });

  it('should show notification will not be sent when tinkering index is too low', () => {
    const highThresholdSettings = { ...mockSettings, minTinkeringIndex: 5 };
    render(<NotificationPreview settings={highThresholdSettings} />);

    expect(screen.getByText('此文章不會觸發通知')).toBeInTheDocument();
    expect(screen.getByText(/技術深度.*低於閾值/)).toBeInTheDocument();
  });

  it('should show notification will not be sent during quiet hours', () => {
    const quietHoursSettings = {
      ...mockSettings,
      quietHours: { enabled: true, start: '00:00', end: '23:59' },
    };
    render(<NotificationPreview settings={quietHoursSettings} />);

    expect(screen.getByText('此文章不會觸發通知')).toBeInTheDocument();
    expect(screen.getByText('目前在勿擾時段內')).toBeInTheDocument();
  });

  it('should display correct frequency information', () => {
    const dailySettings = { ...mockSettings, frequency: 'daily' as const };
    render(<NotificationPreview settings={dailySettings} />);

    expect(screen.getByText('通知將包含在每日摘要中')).toBeInTheDocument();
    expect(screen.getByText('每日摘要')).toBeInTheDocument();
  });

  it('should display correct frequency information for weekly', () => {
    const weeklySettings = { ...mockSettings, frequency: 'weekly' as const };
    render(<NotificationPreview settings={weeklySettings} />);

    expect(screen.getByText('通知將包含在每週摘要中')).toBeInTheDocument();
    expect(screen.getByText('每週摘要')).toBeInTheDocument();
  });

  it('should show active channels when notifications are enabled', () => {
    const multiChannelSettings = { ...mockSettings, emailEnabled: true };
    render(<NotificationPreview settings={multiChannelSettings} />);

    expect(screen.getByText('Discord DM')).toBeInTheDocument();
    expect(screen.getByText('電子郵件')).toBeInTheDocument();
  });

  it('should show no active channels when all channels are disabled', () => {
    const noChannelSettings = { ...mockSettings, dmEnabled: false, emailEnabled: false };
    render(<NotificationPreview settings={noChannelSettings} />);

    expect(screen.getByText('無啟用的通知渠道')).toBeInTheDocument();
  });

  it('should display mock article information', () => {
    render(<NotificationPreview settings={mockSettings} />);

    expect(
      screen.getByText('Next.js 15 發布：全新的 App Router 功能與效能提升')
    ).toBeInTheDocument();
    expect(screen.getByText('Vercel Blog')).toBeInTheDocument();
    expect(screen.getByText('Web Dev')).toBeInTheDocument();
    expect(screen.getByText('30 分鐘前')).toBeInTheDocument();
  });

  it('should display correct star visualization for tinkering index', () => {
    render(<NotificationPreview settings={mockSettings} />);

    // Should show 4 filled stars (orange color for advanced level)
    const stars = screen.getAllByTestId(/star/);
    expect(stars).toHaveLength(5); // 5 stars total in the preview
  });

  it('should display category badge with correct styling', () => {
    render(<NotificationPreview settings={mockSettings} />);

    const categoryBadge = screen.getByText('Web Dev');
    expect(categoryBadge).toBeInTheDocument();
    expect(categoryBadge).toHaveClass('bg-green-100', 'text-green-800');
  });
});
