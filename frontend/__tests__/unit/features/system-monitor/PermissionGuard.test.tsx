/**
 * Unit Tests for ManualFetchDialog
 *
 * Tests the manual fetch confirmation dialog component.
 *
 * Requirements: 5.3
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ManualFetchDialog } from '@/features/system-monitor/components/ManualFetchDialog';

describe('ManualFetchDialog', () => {
  const mockOnOpenChange = vi.fn();
  const mockOnConfirm = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render dialog when open is true', () => {
    render(
      <ManualFetchDialog open={true} onOpenChange={mockOnOpenChange} onConfirm={mockOnConfirm} />
    );

    expect(screen.getByText('確認手動觸發抓取')).toBeInTheDocument();
  });

  it('should not render dialog when open is false', () => {
    render(
      <ManualFetchDialog open={false} onOpenChange={mockOnOpenChange} onConfirm={mockOnConfirm} />
    );

    expect(screen.queryByText('確認手動觸發抓取')).not.toBeInTheDocument();
  });

  it('should display dialog description', () => {
    render(
      <ManualFetchDialog open={true} onOpenChange={mockOnOpenChange} onConfirm={mockOnConfirm} />
    );

    expect(screen.getByText(/此操作將立即觸發文章抓取任務/)).toBeInTheDocument();
  });

  it('should display notice items', () => {
    render(
      <ManualFetchDialog open={true} onOpenChange={mockOnOpenChange} onConfirm={mockOnConfirm} />
    );

    expect(screen.getByText('注意事項：')).toBeInTheDocument();
    expect(screen.getByText(/抓取過程可能需要數分鐘時間/)).toBeInTheDocument();
    expect(screen.getByText(/頻繁觸發可能影響系統效能/)).toBeInTheDocument();
    expect(screen.getByText(/建議等待當前任務完成後再次觸發/)).toBeInTheDocument();
  });

  it('should render cancel and confirm buttons', () => {
    render(
      <ManualFetchDialog open={true} onOpenChange={mockOnOpenChange} onConfirm={mockOnConfirm} />
    );

    expect(screen.getByRole('button', { name: '取消' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '確認觸發' })).toBeInTheDocument();
  });

  it('should call onOpenChange with false when cancel button is clicked', async () => {
    const user = userEvent.setup();
    render(
      <ManualFetchDialog open={true} onOpenChange={mockOnOpenChange} onConfirm={mockOnConfirm} />
    );

    const cancelButton = screen.getByRole('button', { name: '取消' });
    await user.click(cancelButton);

    expect(mockOnOpenChange).toHaveBeenCalledWith(false);
  });

  it('should call onConfirm and onOpenChange when confirm button is clicked', async () => {
    const user = userEvent.setup();
    render(
      <ManualFetchDialog open={true} onOpenChange={mockOnOpenChange} onConfirm={mockOnConfirm} />
    );

    const confirmButton = screen.getByRole('button', { name: '確認觸發' });
    await user.click(confirmButton);

    expect(mockOnConfirm).toHaveBeenCalledTimes(1);
    expect(mockOnOpenChange).toHaveBeenCalledWith(false);
  });

  it('should disable buttons when isLoading is true', () => {
    render(
      <ManualFetchDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        onConfirm={mockOnConfirm}
        isLoading={true}
      />
    );

    const cancelButton = screen.getByRole('button', { name: '取消' });
    const confirmButton = screen.getByRole('button', { name: '觸發中...' });

    expect(cancelButton).toBeDisabled();
    expect(confirmButton).toBeDisabled();
  });

  it('should show loading text when isLoading is true', () => {
    render(
      <ManualFetchDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        onConfirm={mockOnConfirm}
        isLoading={true}
      />
    );

    expect(screen.getByText('觸發中...')).toBeInTheDocument();
  });

  it('should not call onConfirm when confirm button is clicked while loading', async () => {
    const user = userEvent.setup();
    render(
      <ManualFetchDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        onConfirm={mockOnConfirm}
        isLoading={true}
      />
    );

    const confirmButton = screen.getByRole('button', { name: '觸發中...' });
    await user.click(confirmButton);

    // Button is disabled, so click should not trigger the handler
    expect(mockOnConfirm).not.toHaveBeenCalled();
  });
});
