import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { NotificationFrequencySelector } from '@/features/notifications/components/NotificationFrequencySelector';
import { NotificationFrequency } from '@/types/notification';
import { I18nProvider } from '@/contexts/I18nContext';

// Helper to render with I18n context
const renderWithI18n = (ui: React.ReactElement) => {
  return render(<I18nProvider>{ui}</I18nProvider>);
};

describe('NotificationFrequencySelector', () => {
  it('should render all frequency options', async () => {
    const onFrequencyChange = vi.fn();

    renderWithI18n(
      <NotificationFrequencySelector frequency="immediate" onFrequencyChange={onFrequencyChange} />
    );

    // Wait for translations to load by checking for the title
    await screen.findByText(/Notification Frequency|通知頻率/i);

    // Check all options are rendered
    expect(screen.getByRole('radio', { name: /immediate/i })).toBeInTheDocument();
    expect(screen.getByRole('radio', { name: /daily/i })).toBeInTheDocument();
    expect(screen.getByRole('radio', { name: /weekly/i })).toBeInTheDocument();
    expect(screen.getByRole('radio', { name: /disabled/i })).toBeInTheDocument();
  });

  it('should display the selected frequency', async () => {
    const onFrequencyChange = vi.fn();

    renderWithI18n(
      <NotificationFrequencySelector frequency="daily" onFrequencyChange={onFrequencyChange} />
    );

    // Wait for translations to load
    await screen.findByText(/Notification Frequency|通知頻率/i);

    const dailyRadio = screen.getByRole('radio', { name: /daily/i });
    expect(dailyRadio).toBeChecked();
  });

  it('should call onFrequencyChange when a different frequency is selected', async () => {
    const user = userEvent.setup();
    const onFrequencyChange = vi.fn();

    renderWithI18n(
      <NotificationFrequencySelector frequency="immediate" onFrequencyChange={onFrequencyChange} />
    );

    // Wait for translations to load
    await screen.findByText(/Notification Frequency|通知頻率/i);

    const weeklyRadio = screen.getByRole('radio', { name: /weekly/i });
    await user.click(weeklyRadio);

    expect(onFrequencyChange).toHaveBeenCalledWith('weekly');
  });

  it('should be disabled when disabled prop is true', async () => {
    const onFrequencyChange = vi.fn();

    renderWithI18n(
      <NotificationFrequencySelector
        frequency="immediate"
        onFrequencyChange={onFrequencyChange}
        disabled={true}
      />
    );

    // Wait for translations to load
    await screen.findByText(/Notification Frequency|通知頻率/i);

    const immediateRadio = screen.getByRole('radio', { name: /immediate/i });
    expect(immediateRadio).toBeDisabled();
  });

  it('should display descriptions for each frequency option', async () => {
    const onFrequencyChange = vi.fn();

    renderWithI18n(
      <NotificationFrequencySelector frequency="immediate" onFrequencyChange={onFrequencyChange} />
    );

    // Wait for translations to load
    await screen.findByText(/Notification Frequency|通知頻率/i);

    // Check descriptions are present (using partial text matches)
    expect(screen.getByText(/Notify immediately|新文章發布時立即通知/i)).toBeInTheDocument();
    expect(screen.getByText(/once per day|每天一次彙整通知/i)).toBeInTheDocument();
    expect(screen.getByText(/once per week|每週一次彙整通知/i)).toBeInTheDocument();
    expect(screen.getByText(/Do not receive|不接收任何通知/i)).toBeInTheDocument();
  });
});
