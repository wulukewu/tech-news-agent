import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { SchedulerStatusIndicator, SchedulerStatus } from '@/components/SchedulerStatusIndicator';

describe('SchedulerStatusIndicator Component', () => {
  const mockStatus: SchedulerStatus = {
    lastExecutionTime: new Date('2024-01-01T12:00:00Z'),
    nextScheduledTime: new Date('2024-01-01T13:00:00Z'),
    isRunning: false,
    lastExecutionArticleCount: 15,
    estimatedTimeUntilArticles: '5-10 minutes',
  };

  it('should display running indicator when isRunning is true', () => {
    const runningStatus = { ...mockStatus, isRunning: true };
    render(<SchedulerStatusIndicator status={runningStatus} />);
    expect(screen.getByText('Scheduler running...')).toBeInTheDocument();
  });

  it('should show spinning icon when running', () => {
    const runningStatus = { ...mockStatus, isRunning: true };
    const { container } = render(<SchedulerStatusIndicator status={runningStatus} />);
    expect(container.querySelector('[class*="animate"]')).toBeInTheDocument();
  });

  it('should not display running indicator when isRunning is false', () => {
    render(<SchedulerStatusIndicator status={mockStatus} />);
    expect(screen.queryByText('Scheduler running...')).not.toBeInTheDocument();
  });

  it('should display last execution time when not running', () => {
    render(<SchedulerStatusIndicator status={mockStatus} />);
    expect(screen.getByText(/Last execution/)).toBeInTheDocument();
  });

  it('should display article count from last execution', () => {
    render(<SchedulerStatusIndicator status={mockStatus} />);
    expect(screen.getByText(/Fetched 15 articles/)).toBeInTheDocument();
  });

  it('should not display article count when zero', () => {
    const statusWithZeroArticles = { ...mockStatus, lastExecutionArticleCount: 0 };
    render(<SchedulerStatusIndicator status={statusWithZeroArticles} />);
    expect(screen.queryByText(/Fetched 0 articles/)).not.toBeInTheDocument();
  });

  it('should display next scheduled time', () => {
    render(<SchedulerStatusIndicator status={mockStatus} />);
    expect(screen.getByText(/Next scheduled/)).toBeInTheDocument();
  });

  it('should handle null next scheduled time', () => {
    const statusWithoutNext = { ...mockStatus, nextScheduledTime: null };
    render(<SchedulerStatusIndicator status={statusWithoutNext} />);
    expect(screen.queryByText(/Next scheduled/)).not.toBeInTheDocument();
  });

  it('should display estimated time until articles', () => {
    render(<SchedulerStatusIndicator status={mockStatus} />);
    expect(screen.getByText(/5-10 minutes/)).toBeInTheDocument();
  });

  it('should display manual trigger button when callback provided', () => {
    const handleTrigger = vi.fn();
    render(
      <SchedulerStatusIndicator
        status={mockStatus}
        onManualTrigger={handleTrigger}
        canManualTrigger={true}
      />
    );
    expect(screen.getByRole('button', { name: /Manual trigger fetch/i })).toBeInTheDocument();
  });

  it('should call onManualTrigger when button clicked', () => {
    const handleTrigger = vi.fn();
    render(
      <SchedulerStatusIndicator
        status={mockStatus}
        onManualTrigger={handleTrigger}
        canManualTrigger={true}
      />
    );
    fireEvent.click(screen.getByRole('button', { name: /Manual trigger fetch/i }));
    expect(handleTrigger).toHaveBeenCalledTimes(1);
  });

  it('should not display button when canManualTrigger is false', () => {
    const handleTrigger = vi.fn();
    render(
      <SchedulerStatusIndicator
        status={mockStatus}
        onManualTrigger={handleTrigger}
        canManualTrigger={false}
      />
    );
    expect(screen.queryByRole('button', { name: /Manual trigger fetch/i })).not.toBeInTheDocument();
  });

  it('should not display button when no callback provided', () => {
    render(<SchedulerStatusIndicator status={mockStatus} />);
    expect(screen.queryByRole('button', { name: /Manual trigger fetch/i })).not.toBeInTheDocument();
  });

  it('should hide manual trigger button when running', () => {
    const runningStatus = { ...mockStatus, isRunning: true };
    const handleTrigger = vi.fn();
    render(
      <SchedulerStatusIndicator
        status={runningStatus}
        onManualTrigger={handleTrigger}
        canManualTrigger={true}
      />
    );
    expect(screen.queryByRole('button', { name: /Manual trigger fetch/i })).not.toBeInTheDocument();
  });
});
