import { render, screen, fireEvent } from '@testing-library/react';
import { vi } from 'vitest';
import { QuietHoursSettings } from '../../components/QuietHoursSettings';

describe('QuietHoursSettings', () => {
  const mockOnQuietHoursChange = vi.fn();

  beforeEach(() => {
    mockOnQuietHoursChange.mockClear();
  });

  it('should render with default values when quietHours is undefined', () => {
    render(
      <QuietHoursSettings quietHours={undefined} onQuietHoursChange={mockOnQuietHoursChange} />
    );

    expect(screen.getByText('勿擾時段')).toBeInTheDocument();
    expect(screen.getByText('設定您不希望接收通知的時段')).toBeInTheDocument();

    // Should show the switch as unchecked (default)
    const enableSwitch = screen.getByRole('switch');
    expect(enableSwitch).not.toBeChecked();
  });

  it('should render with provided quietHours values', () => {
    const quietHours = {
      enabled: true,
      start: '23:00',
      end: '07:00',
    };

    render(
      <QuietHoursSettings quietHours={quietHours} onQuietHoursChange={mockOnQuietHoursChange} />
    );

    const enableSwitch = screen.getByRole('switch');
    expect(enableSwitch).toBeChecked();

    // Time inputs should be visible when enabled
    expect(screen.getByDisplayValue('23:00')).toBeInTheDocument();
    expect(screen.getByDisplayValue('07:00')).toBeInTheDocument();
  });

  it('should handle toggle correctly with undefined quietHours', () => {
    render(
      <QuietHoursSettings quietHours={undefined} onQuietHoursChange={mockOnQuietHoursChange} />
    );

    const enableSwitch = screen.getByRole('switch');
    fireEvent.click(enableSwitch);

    expect(mockOnQuietHoursChange).toHaveBeenCalledWith({
      enabled: true,
      start: '22:00',
      end: '08:00',
    });
  });

  it('should handle start time change', () => {
    const quietHours = {
      enabled: true,
      start: '22:00',
      end: '08:00',
    };

    render(
      <QuietHoursSettings quietHours={quietHours} onQuietHoursChange={mockOnQuietHoursChange} />
    );

    const startTimeInput = screen.getByDisplayValue('22:00');
    fireEvent.change(startTimeInput, { target: { value: '23:30' } });

    expect(mockOnQuietHoursChange).toHaveBeenCalledWith({
      enabled: true,
      start: '23:30',
      end: '08:00',
    });
  });

  it('should handle end time change', () => {
    const quietHours = {
      enabled: true,
      start: '22:00',
      end: '08:00',
    };

    render(
      <QuietHoursSettings quietHours={quietHours} onQuietHoursChange={mockOnQuietHoursChange} />
    );

    const endTimeInput = screen.getByDisplayValue('08:00');
    fireEvent.change(endTimeInput, { target: { value: '09:00' } });

    expect(mockOnQuietHoursChange).toHaveBeenCalledWith({
      enabled: true,
      start: '22:00',
      end: '09:00',
    });
  });

  it('should be disabled when disabled prop is true', () => {
    const quietHours = {
      enabled: true,
      start: '22:00',
      end: '08:00',
    };

    render(
      <QuietHoursSettings
        quietHours={quietHours}
        onQuietHoursChange={mockOnQuietHoursChange}
        disabled={true}
      />
    );

    const enableSwitch = screen.getByRole('switch');
    const startTimeInput = screen.getByDisplayValue('22:00');
    const endTimeInput = screen.getByDisplayValue('08:00');

    expect(enableSwitch).toBeDisabled();
    expect(startTimeInput).toBeDisabled();
    expect(endTimeInput).toBeDisabled();
  });

  it('should not show time inputs when quiet hours is disabled', () => {
    const quietHours = {
      enabled: false,
      start: '22:00',
      end: '08:00',
    };

    render(
      <QuietHoursSettings quietHours={quietHours} onQuietHoursChange={mockOnQuietHoursChange} />
    );

    // Time inputs should not be visible when disabled
    expect(screen.queryByDisplayValue('22:00')).not.toBeInTheDocument();
    expect(screen.queryByDisplayValue('08:00')).not.toBeInTheDocument();
  });

  it('should show summary text when quiet hours is enabled', () => {
    const quietHours = {
      enabled: true,
      start: '23:00',
      end: '07:00',
    };

    render(
      <QuietHoursSettings quietHours={quietHours} onQuietHoursChange={mockOnQuietHoursChange} />
    );

    expect(screen.getByText('通知將在 23:00 至 07:00 期間暫停')).toBeInTheDocument();
  });
});
