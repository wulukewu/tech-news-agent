/**
 * Unit Tests for SchedulerStatusWidget
 *
 * Tests the scheduler status widget component including:
 * - Status display
 * - Manual trigger button
 * - Health indicators
 *
 * Requirements: 5.1, 5.2, 5.3
 */

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

  const mockRunningStatus: SchedulerStatus = {
    ...mockHealthyStatus,
    isRunning: true,
  };

  it('should render scheduler status widget', () => {
    render(<SchedulerStatusWidget status={mockHealthyStatus} />);

    expect(screen.getByText('排程器狀態')).toBeInTheDocument();
    expect(screen.getByText('背景任務執行狀況和下次執行時間')).toBeInTheDocument();
  });

  it('should display healthy status badge', () => {
    render(<SchedulerStatusWidget status={mockHealthyStatus} />);

    expect(screen.getByText('正常')).toBeInTheDocument();
  });

  it('should display unhealthy status badge', () => {
    render(<SchedulerStatusWidget status={mockUnhealthyStatus} />);

    expect(screen.getByText('異常')).toBeInTheDocument();
  });

  it('should display running status badge', () => {
    render(<SchedulerStatusWidget status={mockRunningStatus} />);

    expect(screen.getByText('執行中')).toBeInTheDocument();
  });

  it('should display last execution time', () => {
    render(<SchedulerStatusWidget status={mockHealthyStatus} />);

    expect(screen.getByText(/上次執行/)).toBeInTheDocument();
  });

  it('should display articles processed count', () => {
    render(<SchedulerStatusWidget status={mockHealthyStatus} />);

    expect(screen.getByText(/15 篇文章/)).toBeInTheDocument();
  });

  it('should display next execution time', () => {
    render(<SchedulerStatusWidget status={mockHealthyStatus} />);

    expect(screen.getByText(/下次排程/)).toBeInTheDocument();
  });

  it('should display execution statistics', () => {
    render(<SchedulerStatusWidget status={mockHealthyStatus} />);

    expect(screen.getByText('執行統計')).toBeInTheDocument();
    expect(screen.getByText('總操作')).toBeInTheDocument();
    expect(screen.getByText('成功')).toBeInTheDocument();
    expect(screen.getByText('失敗')).toBeInTheDocument();
  });

  it('should display health issues when present', () => {
    render(<SchedulerStatusWidget status={mockUnhealthyStatus} />);

    expect(screen.getByText('健康度問題')).toBeInTheDocument();
    expect(screen.getByText('Scheduler has never executed')).toBeInTheDocument();
    expect(screen.getByText('High failure rate')).toBeInTheDocument();
  });

  it('should not display health issues when healthy', () => {
    render(<SchedulerStatusWidget status={mockHealthyStatus} />);

    expect(screen.queryByText('健康度問題')).not.toBeInTheDocument();
  });

  it('should render manual trigger button when onTrigger is provided', () => {
    const onTrigger = vi.fn();
    render(<SchedulerStatusWidget status={mockHealthyStatus} onTrigger={onTrigger} />);

    expect(screen.getByRole('button', { name: /手動觸發抓取/ })).toBeInTheDocument();
  });

  it('should not render manual trigger button when onTrigger is not provided', () => {
    render(<SchedulerStatusWidget status={mockHealthyStatus} />);

    expect(screen.queryByRole('button', { name: /手動觸發抓取/ })).not.toBeInTheDocument();
  });

  it('should call onTrigger when manual trigger button is clicked', async () => {
    const user = userEvent.setup();
    const onTrigger = vi.fn();
    render(<SchedulerStatusWidget status={mockHealthyStatus} onTrigger={onTrigger} />);

    const button = screen.getByRole('button', { name: /手動觸發抓取/ });
    await user.click(button);

    expect(onTrigger).toHaveBeenCalledTimes(1);
  });

  it('should disable manual trigger button when scheduler is running', () => {
    const onTrigger = vi.fn();
    render(<SchedulerStatusWidget status={mockRunningStatus} onTrigger={onTrigger} />);

    const button = screen.getByRole('button', { name: /手動觸發抓取/ });
    expect(button).toBeDisabled();
  });

  it('should disable manual trigger button when isTriggering is true', () => {
    const onTrigger = vi.fn();
    render(
      <SchedulerStatusWidget status={mockHealthyStatus} onTrigger={onTrigger} isTriggering={true} />
    );

    const button = screen.getByRole('button', { name: /觸發中/ });
    expect(button).toBeDisabled();
  });

  it('should show triggering state when isTriggering is true', () => {
    const onTrigger = vi.fn();
    render(
      <SchedulerStatusWidget status={mockHealthyStatus} onTrigger={onTrigger} isTriggering={true} />
    );

    expect(screen.getByText('觸發中...')).toBeInTheDocument();
  });

  it('should display "尚未執行" when lastExecutionTime is null', () => {
    const status = { ...mockHealthyStatus, lastExecutionTime: null };
    render(<SchedulerStatusWidget status={status} />);

    expect(screen.getByText('尚未執行')).toBeInTheDocument();
  });

  it('should display "計算中..." when nextExecutionTime is null', () => {
    const status = { ...mockHealthyStatus, nextExecutionTime: null };
    render(<SchedulerStatusWidget status={status} />);

    expect(screen.getByText('計算中...')).toBeInTheDocument();
  });
});
