import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { SchedulerStatusWidget } from '@/features/system-monitor/components/SchedulerStatusWidget';
import type { SchedulerStatus } from '@/features/system-monitor/types';

describe('SchedulerStatusWidget', () => {
  const mockHealthyStatus: SchedulerStatus = {
    isRunning: false,
    lastExecutionTime: new Date('2024-01-01T12:00:00Z'),
    nextExecutionTime: new Date('2024-01-01T13:00:00Z'),
    articlesProcessed: 15,
    failedOperations: 0,
    totalOperations: 15,
    isHealthy: true,
    issues: [],
  };

  const mockUnhealthyStatus: SchedulerStatus = {
    isRunning: false,
    lastExecutionTime: null,
    nextExecutionTime: null,
    articlesProcessed: 0,
    failedOperations: 5,
    totalOperations: 10,
    isHealthy: false,
    issues: ['Scheduler has never executed', 'High failure rate'],
  };

  const mockRunningStatus: SchedulerStatus = { ...mockHealthyStatus, isRunning: true };

  it('should render scheduler status widget', () => {
    render(<SchedulerStatusWidget status={mockHealthyStatus} />);
    expect(screen.getByText('Scheduler Status')).toBeInTheDocument();
  });

  it('should display healthy status badge', () => {
    render(<SchedulerStatusWidget status={mockHealthyStatus} />);
    expect(screen.getByText('Healthy')).toBeInTheDocument();
  });

  it('should display unhealthy status badge', () => {
    render(<SchedulerStatusWidget status={mockUnhealthyStatus} />);
    expect(screen.getByText('Abnormal')).toBeInTheDocument();
  });

  it('should display running status badge', () => {
    render(<SchedulerStatusWidget status={mockRunningStatus} />);
    expect(screen.getByText('Running')).toBeInTheDocument();
  });

  it('should display last execution label', () => {
    render(<SchedulerStatusWidget status={mockHealthyStatus} />);
    expect(screen.getByText('Last Execution')).toBeInTheDocument();
  });

  it('should display articles processed count', () => {
    render(<SchedulerStatusWidget status={mockHealthyStatus} />);
    expect(screen.getByText(/15 articles/)).toBeInTheDocument();
  });

  it('should display next scheduled label', () => {
    render(<SchedulerStatusWidget status={mockHealthyStatus} />);
    expect(screen.getByText('Next Scheduled')).toBeInTheDocument();
  });

  it('should display execution statistics', () => {
    render(<SchedulerStatusWidget status={mockHealthyStatus} />);
    expect(screen.getByText('Execution Statistics')).toBeInTheDocument();
    expect(screen.getByText('Total Operations')).toBeInTheDocument();
    expect(screen.getByText('Success')).toBeInTheDocument();
    expect(screen.getByText('Failed')).toBeInTheDocument();
  });

  it('should display health issues when present', () => {
    render(<SchedulerStatusWidget status={mockUnhealthyStatus} />);
    expect(screen.getByText('Health Issues')).toBeInTheDocument();
    expect(screen.getByText('Scheduler has never executed')).toBeInTheDocument();
    expect(screen.getByText('High failure rate')).toBeInTheDocument();
  });

  it('should not display health issues when healthy', () => {
    render(<SchedulerStatusWidget status={mockHealthyStatus} />);
    expect(screen.queryByText('Health Issues')).not.toBeInTheDocument();
  });

  it('should render manual trigger button when onTrigger is provided', () => {
    const onTrigger = vi.fn();
    render(<SchedulerStatusWidget status={mockHealthyStatus} onTrigger={onTrigger} />);
    expect(screen.getByRole('button', { name: /Manual Trigger Fetch/i })).toBeInTheDocument();
  });

  it('should not render manual trigger button when onTrigger is not provided', () => {
    render(<SchedulerStatusWidget status={mockHealthyStatus} />);
    expect(screen.queryByRole('button', { name: /Manual Trigger Fetch/i })).not.toBeInTheDocument();
  });

  it('should call onTrigger when manual trigger button is clicked', async () => {
    const user = userEvent.setup();
    const onTrigger = vi.fn();
    render(<SchedulerStatusWidget status={mockHealthyStatus} onTrigger={onTrigger} />);
    const button = screen.getByRole('button', { name: /Manual Trigger Fetch/i });
    await user.click(button);
    expect(onTrigger).toHaveBeenCalledTimes(1);
  });

  it('should disable manual trigger button when scheduler is running', () => {
    const onTrigger = vi.fn();
    render(<SchedulerStatusWidget status={mockRunningStatus} onTrigger={onTrigger} />);
    const button = screen.getByRole('button', { name: /Manual Trigger Fetch/i });
    expect(button).toBeDisabled();
  });

  it('should show triggering state when isTriggering is true', () => {
    const onTrigger = vi.fn();
    render(
      <SchedulerStatusWidget status={mockHealthyStatus} onTrigger={onTrigger} isTriggering={true} />
    );
    expect(screen.getByText('Triggering...')).toBeInTheDocument();
  });

  it('should display "Not executed yet" when lastExecutionTime is null', () => {
    const status = { ...mockHealthyStatus, lastExecutionTime: null };
    render(<SchedulerStatusWidget status={status} />);
    expect(screen.getByText('Not executed yet')).toBeInTheDocument();
  });

  it('should display "Calculating..." when nextExecutionTime is null', () => {
    const status = { ...mockHealthyStatus, nextExecutionTime: null };
    render(<SchedulerStatusWidget status={status} />);
    expect(screen.getByText('Calculating...')).toBeInTheDocument();
  });
});
