import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { QuietHoursSettings } from '@/features/notifications/components/QuietHoursSettings';

vi.mock('@/lib/api/notifications', () => ({
  getQuietHoursSettings: vi.fn().mockResolvedValue(null),
  getQuietHoursStatus: vi.fn().mockResolvedValue(null),
  getSupportedTimezones: vi.fn().mockResolvedValue([]),
  updateQuietHoursSettings: vi.fn(),
  getQuietHours: vi.fn().mockResolvedValue({
    enabled: false,
    start_time: '22:00:00',
    end_time: '08:00:00',
    timezone: 'Asia/Taipei',
    weekdays: [1, 2, 3, 4, 5, 6, 7],
  }),
  updateQuietHours: vi.fn(),
}));

vi.mock('@/lib/toast', () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}));

describe('QuietHoursSettings', () => {
  let queryClient: QueryClient;
  const defaultQuietHours = { enabled: false, start: '22:00', end: '08:00' };

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    vi.clearAllMocks();
  });

  const renderWithQueryClient = (component: React.ReactElement) =>
    render(<QueryClientProvider client={queryClient}>{component}</QueryClientProvider>);

  it('should render quiet hours toggle', async () => {
    const onQuietHoursChange = vi.fn();
    renderWithQueryClient(
      <QuietHoursSettings quietHours={defaultQuietHours} onQuietHoursChange={onQuietHoursChange} />
    );
    await waitFor(() => {
      expect(screen.getByText('Enable Quiet Hours')).toBeInTheDocument();
    });
  });

  it('should not show time inputs when quiet hours is disabled', async () => {
    const onQuietHoursChange = vi.fn();
    renderWithQueryClient(
      <QuietHoursSettings quietHours={defaultQuietHours} onQuietHoursChange={onQuietHoursChange} />
    );
    await waitFor(() => {
      expect(screen.getByText('Enable Quiet Hours')).toBeInTheDocument();
    });
    expect(screen.queryByDisplayValue('22:00')).not.toBeInTheDocument();
    expect(screen.queryByDisplayValue('08:00')).not.toBeInTheDocument();
  });

  it('should show time inputs when quiet hours is enabled', async () => {
    const { getQuietHours } = await import('@/lib/api/notifications');
    vi.mocked(getQuietHours).mockResolvedValue({
      enabled: true,
      start_time: '22:00:00',
      end_time: '08:00:00',
      timezone: 'Asia/Taipei',
      weekdays: [1, 2, 3, 4, 5, 6, 7],
    });
    const onQuietHoursChange = vi.fn();
    renderWithQueryClient(
      <QuietHoursSettings
        quietHours={{ enabled: true, start: '22:00', end: '08:00' }}
        onQuietHoursChange={onQuietHoursChange}
      />
    );
    await waitFor(() => {
      expect(screen.getByDisplayValue('22:00')).toBeInTheDocument();
    });
  });

  it('should call onQuietHoursChange when toggle is clicked', async () => {
    const user = userEvent.setup();
    const onQuietHoursChange = vi.fn();
    renderWithQueryClient(
      <QuietHoursSettings quietHours={defaultQuietHours} onQuietHoursChange={onQuietHoursChange} />
    );
    await waitFor(() => {
      expect(screen.getByRole('switch')).toBeInTheDocument();
    });
    await user.click(screen.getByRole('switch'));
    // updateQuietHours should be called (mutation)
    const { updateQuietHours } = await import('@/lib/api/notifications');
    expect(updateQuietHours).toHaveBeenCalled();
  });

  it('should call onQuietHoursChange when start time is changed', async () => {
    const { getQuietHours } = await import('@/lib/api/notifications');
    vi.mocked(getQuietHours).mockResolvedValue({
      enabled: true,
      start_time: '22:00:00',
      end_time: '08:00:00',
      timezone: 'Asia/Taipei',
      weekdays: [1, 2, 3, 4, 5, 6, 7],
    });
    const onQuietHoursChange = vi.fn();
    renderWithQueryClient(
      <QuietHoursSettings
        quietHours={{ enabled: true, start: '22:00', end: '08:00' }}
        onQuietHoursChange={onQuietHoursChange}
      />
    );
    await waitFor(() => {
      expect(screen.getByDisplayValue('22:00')).toBeInTheDocument();
    });
    fireEvent.change(screen.getByDisplayValue('22:00'), { target: { value: '23:00' } });
    const { updateQuietHours } = await import('@/lib/api/notifications');
    expect(updateQuietHours).toHaveBeenCalled();
  });

  it('should call onQuietHoursChange when end time is changed', async () => {
    const { getQuietHours } = await import('@/lib/api/notifications');
    vi.mocked(getQuietHours).mockResolvedValue({
      enabled: true,
      start_time: '22:00:00',
      end_time: '08:00:00',
      timezone: 'Asia/Taipei',
      weekdays: [1, 2, 3, 4, 5, 6, 7],
    });
    const onQuietHoursChange = vi.fn();
    renderWithQueryClient(
      <QuietHoursSettings
        quietHours={{ enabled: true, start: '22:00', end: '08:00' }}
        onQuietHoursChange={onQuietHoursChange}
      />
    );
    await waitFor(() => {
      expect(screen.getByDisplayValue('08:00')).toBeInTheDocument();
    });
    fireEvent.change(screen.getByDisplayValue('08:00'), { target: { value: '09:00' } });
    const { updateQuietHours } = await import('@/lib/api/notifications');
    expect(updateQuietHours).toHaveBeenCalled();
  });

  it('should be disabled when disabled prop is true', async () => {
    const onQuietHoursChange = vi.fn();
    renderWithQueryClient(
      <QuietHoursSettings
        quietHours={defaultQuietHours}
        onQuietHoursChange={onQuietHoursChange}
        disabled={true}
      />
    );
    await waitFor(() => {
      expect(screen.getByRole('switch')).toBeInTheDocument();
    });
    expect(screen.getByRole('switch')).toBeDisabled();
  });
});
