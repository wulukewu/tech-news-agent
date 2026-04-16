import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QuietHoursSettings } from '@/features/notifications/components/QuietHoursSettings';

describe('QuietHoursSettings', () => {
  const defaultQuietHours = {
    enabled: false,
    start: '22:00',
    end: '08:00',
  };

  it('should render quiet hours toggle', () => {
    const onQuietHoursChange = vi.fn();

    render(
      <QuietHoursSettings quietHours={defaultQuietHours} onQuietHoursChange={onQuietHoursChange} />
    );

    expect(screen.getByText('啟用勿擾時段')).toBeInTheDocument();
    expect(screen.getByText('在指定時段內暫停通知')).toBeInTheDocument();
  });

  it('should not show time inputs when quiet hours is disabled', () => {
    const onQuietHoursChange = vi.fn();

    render(
      <QuietHoursSettings quietHours={defaultQuietHours} onQuietHoursChange={onQuietHoursChange} />
    );

    expect(screen.queryByLabelText('開始時間')).not.toBeInTheDocument();
    expect(screen.queryByLabelText('結束時間')).not.toBeInTheDocument();
  });

  it('should show time inputs when quiet hours is enabled', () => {
    const onQuietHoursChange = vi.fn();
    const enabledQuietHours = { ...defaultQuietHours, enabled: true };

    render(
      <QuietHoursSettings quietHours={enabledQuietHours} onQuietHoursChange={onQuietHoursChange} />
    );

    expect(screen.getByLabelText('開始時間')).toBeInTheDocument();
    expect(screen.getByLabelText('結束時間')).toBeInTheDocument();
  });

  it('should call onQuietHoursChange when toggle is clicked', async () => {
    const user = userEvent.setup();
    const onQuietHoursChange = vi.fn();

    render(
      <QuietHoursSettings quietHours={defaultQuietHours} onQuietHoursChange={onQuietHoursChange} />
    );

    const toggle = screen.getByRole('switch');
    await user.click(toggle);

    expect(onQuietHoursChange).toHaveBeenCalledWith({
      ...defaultQuietHours,
      enabled: true,
    });
  });

  it('should call onQuietHoursChange when start time is changed', async () => {
    const user = userEvent.setup();
    const onQuietHoursChange = vi.fn();
    const enabledQuietHours = { ...defaultQuietHours, enabled: true };

    render(
      <QuietHoursSettings quietHours={enabledQuietHours} onQuietHoursChange={onQuietHoursChange} />
    );

    const startInput = screen.getByLabelText('開始時間');

    // Use fireEvent.change to set the complete value at once
    fireEvent.change(startInput, { target: { value: '23:00' } });

    expect(onQuietHoursChange).toHaveBeenCalledWith({
      ...enabledQuietHours,
      start: '23:00',
    });
  });

  it('should call onQuietHoursChange when end time is changed', async () => {
    const user = userEvent.setup();
    const onQuietHoursChange = vi.fn();
    const enabledQuietHours = { ...defaultQuietHours, enabled: true };

    render(
      <QuietHoursSettings quietHours={enabledQuietHours} onQuietHoursChange={onQuietHoursChange} />
    );

    const endInput = screen.getByLabelText('結束時間');

    // Use fireEvent.change to set the complete value at once
    fireEvent.change(endInput, { target: { value: '09:00' } });

    expect(onQuietHoursChange).toHaveBeenCalledWith({
      ...enabledQuietHours,
      end: '09:00',
    });
  });

  it('should display quiet hours summary when enabled', () => {
    const onQuietHoursChange = vi.fn();
    const enabledQuietHours = { enabled: true, start: '22:00', end: '08:00' };

    render(
      <QuietHoursSettings quietHours={enabledQuietHours} onQuietHoursChange={onQuietHoursChange} />
    );

    expect(screen.getByText(/通知將在 22:00 至 08:00 期間暫停/)).toBeInTheDocument();
  });

  it('should be disabled when disabled prop is true', () => {
    const onQuietHoursChange = vi.fn();
    const enabledQuietHours = { ...defaultQuietHours, enabled: true };

    render(
      <QuietHoursSettings
        quietHours={enabledQuietHours}
        onQuietHoursChange={onQuietHoursChange}
        disabled={true}
      />
    );

    const toggle = screen.getByRole('switch');
    expect(toggle).toBeDisabled();

    const startInput = screen.getByLabelText('開始時間');
    const endInput = screen.getByLabelText('結束時間');
    expect(startInput).toBeDisabled();
    expect(endInput).toBeDisabled();
  });
});
