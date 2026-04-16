import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { NotificationFrequencySelector } from '@/features/notifications/components/NotificationFrequencySelector';
import { NotificationFrequency } from '@/types/notification';

describe('NotificationFrequencySelector', () => {
  it('should render all frequency options', () => {
    const onFrequencyChange = vi.fn();

    render(
      <NotificationFrequencySelector frequency="immediate" onFrequencyChange={onFrequencyChange} />
    );

    expect(screen.getByText('即時通知')).toBeInTheDocument();
    expect(screen.getByText('每日摘要')).toBeInTheDocument();
    expect(screen.getByText('每週摘要')).toBeInTheDocument();
  });

  it('should display the selected frequency', () => {
    const onFrequencyChange = vi.fn();

    render(
      <NotificationFrequencySelector frequency="daily" onFrequencyChange={onFrequencyChange} />
    );

    const dailyRadio = screen.getByRole('radio', { name: /每日摘要/i });
    expect(dailyRadio).toBeChecked();
  });

  it('should call onFrequencyChange when a different frequency is selected', async () => {
    const user = userEvent.setup();
    const onFrequencyChange = vi.fn();

    render(
      <NotificationFrequencySelector frequency="immediate" onFrequencyChange={onFrequencyChange} />
    );

    const weeklyRadio = screen.getByRole('radio', { name: /每週摘要/i });
    await user.click(weeklyRadio);

    expect(onFrequencyChange).toHaveBeenCalledWith('weekly');
  });

  it('should be disabled when disabled prop is true', () => {
    const onFrequencyChange = vi.fn();

    render(
      <NotificationFrequencySelector
        frequency="immediate"
        onFrequencyChange={onFrequencyChange}
        disabled={true}
      />
    );

    const immediateRadio = screen.getByRole('radio', { name: /即時通知/i });
    expect(immediateRadio).toBeDisabled();
  });

  it('should display descriptions for each frequency option', () => {
    const onFrequencyChange = vi.fn();

    render(
      <NotificationFrequencySelector frequency="immediate" onFrequencyChange={onFrequencyChange} />
    );

    expect(screen.getByText('新文章發布時立即通知')).toBeInTheDocument();
    expect(screen.getByText('每天一次彙整通知')).toBeInTheDocument();
    expect(screen.getByText('每週一次彙整通知')).toBeInTheDocument();
  });
});
