import { render, screen, fireEvent } from '@testing-library/react';
import {
  SchedulerStatusIndicator,
  SchedulerStatus,
} from '../SchedulerStatusIndicator';

describe('SchedulerStatusIndicator Component', () => {
  const mockStatus: SchedulerStatus = {
    lastExecutionTime: new Date('2024-01-01T12:00:00Z'),
    nextScheduledTime: new Date('2024-01-01T13:00:00Z'),
    isRunning: false,
    lastExecutionArticleCount: 15,
    estimatedTimeUntilArticles: '5-10 分鐘',
  };

  describe('Property 11: Scheduler Status Running Indicator', () => {
    it('should display running indicator when isRunning is true', () => {
      const runningStatus = { ...mockStatus, isRunning: true };

      render(<SchedulerStatusIndicator status={runningStatus} />);

      expect(screen.getByText('排程器執行中...')).toBeInTheDocument();
    });

    it('should show spinning icon when running', () => {
      const runningStatus = { ...mockStatus, isRunning: true };
      const { container } = render(
        <SchedulerStatusIndicator status={runningStatus} />,
      );

      const spinningIcon = container.querySelector('.animate-spin');
      expect(spinningIcon).toBeInTheDocument();
    });

    it('should not display running indicator when isRunning is false', () => {
      render(<SchedulerStatusIndicator status={mockStatus} />);

      expect(screen.queryByText('排程器執行中...')).not.toBeInTheDocument();
    });

    it('should hide manual trigger button when running', () => {
      const runningStatus = { ...mockStatus, isRunning: true };
      const handleTrigger = jest.fn();

      render(
        <SchedulerStatusIndicator
          status={runningStatus}
          onManualTrigger={handleTrigger}
          canManualTrigger={true}
        />,
      );

      expect(screen.queryByText('手動抓取')).not.toBeInTheDocument();
    });
  });

  describe('Last Execution Display', () => {
    it('should display last execution time when not running', () => {
      render(<SchedulerStatusIndicator status={mockStatus} />);

      expect(screen.getByText(/上次執行/)).toBeInTheDocument();
    });

    it('should display article count from last execution', () => {
      render(<SchedulerStatusIndicator status={mockStatus} />);

      expect(screen.getByText(/抓取 15 篇文章/)).toBeInTheDocument();
    });

    it('should not display article count when zero', () => {
      const statusWithZeroArticles = {
        ...mockStatus,
        lastExecutionArticleCount: 0,
      };

      render(<SchedulerStatusIndicator status={statusWithZeroArticles} />);

      expect(screen.queryByText(/抓取 0 篇文章/)).not.toBeInTheDocument();
    });
  });

  describe('Next Scheduled Time', () => {
    it('should display next scheduled time', () => {
      render(<SchedulerStatusIndicator status={mockStatus} />);

      expect(screen.getByText(/下次排程/)).toBeInTheDocument();
    });

    it('should handle null next scheduled time', () => {
      const statusWithoutNext = { ...mockStatus, nextScheduledTime: null };

      render(<SchedulerStatusIndicator status={statusWithoutNext} />);

      expect(screen.queryByText(/下次排程/)).not.toBeInTheDocument();
    });
  });

  describe('Estimated Time Display', () => {
    it('should display estimated time until articles', () => {
      render(<SchedulerStatusIndicator status={mockStatus} />);

      expect(
        screen.getByText(/預計 5-10 分鐘 後會有新文章/),
      ).toBeInTheDocument();
    });

    it('should not display estimated time when running', () => {
      const runningStatus = { ...mockStatus, isRunning: true };

      render(<SchedulerStatusIndicator status={runningStatus} />);

      expect(
        screen.queryByText(/預計 5-10 分鐘 後會有新文章/),
      ).not.toBeInTheDocument();
    });
  });

  describe('Property 12: Manual Fetch Feedback', () => {
    it('should display manual trigger button when callback provided', () => {
      const handleTrigger = jest.fn();

      render(
        <SchedulerStatusIndicator
          status={mockStatus}
          onManualTrigger={handleTrigger}
          canManualTrigger={true}
        />,
      );

      expect(screen.getByText('手動抓取')).toBeInTheDocument();
    });

    it('should call onManualTrigger when button clicked', () => {
      const handleTrigger = jest.fn();

      render(
        <SchedulerStatusIndicator
          status={mockStatus}
          onManualTrigger={handleTrigger}
          canManualTrigger={true}
        />,
      );

      const button = screen.getByText('手動抓取');
      fireEvent.click(button);

      expect(handleTrigger).toHaveBeenCalledTimes(1);
    });

    it('should not display button when canManualTrigger is false', () => {
      const handleTrigger = jest.fn();

      render(
        <SchedulerStatusIndicator
          status={mockStatus}
          onManualTrigger={handleTrigger}
          canManualTrigger={false}
        />,
      );

      expect(screen.queryByText('手動抓取')).not.toBeInTheDocument();
    });

    it('should not display button when no callback provided', () => {
      render(<SchedulerStatusIndicator status={mockStatus} />);

      expect(screen.queryByText('手動抓取')).not.toBeInTheDocument();
    });

    it('should provide visual feedback on hover', () => {
      const handleTrigger = jest.fn();
      const { container } = render(
        <SchedulerStatusIndicator
          status={mockStatus}
          onManualTrigger={handleTrigger}
          canManualTrigger={true}
        />,
      );

      const button = screen.getByText('手動抓取');
      expect(button.className).toContain('hover:bg-accent');
      expect(button.className).toContain('transition-colors');
    });
  });

  describe('Relative Time Formatting', () => {
    it('should format recent times correctly', () => {
      const recentTime = new Date(Date.now() - 5 * 60 * 1000); // 5 minutes ago
      const statusWithRecentTime = {
        ...mockStatus,
        lastExecutionTime: recentTime,
      };

      render(<SchedulerStatusIndicator status={statusWithRecentTime} />);

      expect(screen.getByText(/5 分鐘前/)).toBeInTheDocument();
    });

    it('should format future times correctly', () => {
      const futureTime = new Date(Date.now() + 30 * 60 * 1000); // 30 minutes from now
      const statusWithFutureTime = {
        ...mockStatus,
        nextScheduledTime: futureTime,
      };

      render(<SchedulerStatusIndicator status={statusWithFutureTime} />);

      // Check for "分鐘後" pattern (may be "30 分鐘後" or "約 30 分鐘後")
      expect(screen.getByText(/分鐘後/)).toBeInTheDocument();
    });
  });
});
