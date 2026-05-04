import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { QuietHoursSettings } from '../../components/QuietHoursSettings';

import * as notificationsApi from '@/lib/api/notifications';

vi.mock('@/lib/api/notifications', () => ({
  getQuietHoursSettings: vi.fn().mockResolvedValue(null),
  getQuietHoursStatus: vi.fn().mockResolvedValue(null),
  getSupportedTimezones: vi.fn().mockResolvedValue([]),
  updateQuietHoursSettings: vi.fn(),
  getQuietHours: vi.fn(),
  updateQuietHours: vi.fn(),
}));

vi.mock('@/lib/toast', () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}));

const defaultQuietHoursData = {
  enabled: false,
  start_time: '22:00:00',
  end_time: '08:00:00',
  timezone: 'Asia/Taipei',
  weekdays: [1, 2, 3, 4, 5, 6, 7],
};

describe('QuietHoursSettings', () => {
  let queryClient: QueryClient;
  const mockOnQuietHoursChange = vi.fn();

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    vi.clearAllMocks();
    vi.mocked(notificationsApi.getQuietHours).mockResolvedValue(defaultQuietHoursData);
  });

  const renderWithQueryClient = (component: React.ReactElement) =>
    render(<QueryClientProvider client={queryClient}>{component}</QueryClientProvider>);

  it('should render title', async () => {
    renderWithQueryClient(
      <QuietHoursSettings quietHours={undefined} onQuietHoursChange={mockOnQuietHoursChange} />
    );
    await waitFor(() => {
      expect(screen.getByText('Quiet Hours')).toBeInTheDocument();
    });
  });

  it('should render enable toggle after loading', async () => {
    renderWithQueryClient(
      <QuietHoursSettings quietHours={undefined} onQuietHoursChange={mockOnQuietHoursChange} />
    );
    await waitFor(() => {
      expect(screen.getByRole('switch')).toBeInTheDocument();
    });
  });

  it('should not show time inputs when quiet hours is disabled', async () => {
    renderWithQueryClient(
      <QuietHoursSettings quietHours={undefined} onQuietHoursChange={mockOnQuietHoursChange} />
    );
    await waitFor(() => {
      expect(screen.getByRole('switch')).toBeInTheDocument();
    });
    expect(screen.queryByDisplayValue('22:00')).not.toBeInTheDocument();
  });

  it('should show time inputs when quiet hours is enabled', async () => {
    vi.mocked(notificationsApi.getQuietHours).mockResolvedValue({
      ...defaultQuietHoursData,
      enabled: true,
    });
    renderWithQueryClient(
      <QuietHoursSettings quietHours={undefined} onQuietHoursChange={mockOnQuietHoursChange} />
    );
    await waitFor(() => {
      expect(screen.getByDisplayValue('22:00')).toBeInTheDocument();
    });
  });

  it('should handle toggle click', async () => {
    renderWithQueryClient(
      <QuietHoursSettings quietHours={undefined} onQuietHoursChange={mockOnQuietHoursChange} />
    );
    await waitFor(() => {
      expect(screen.getByRole('switch')).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole('switch'));
    // updateQuietHours should be called
    const { updateQuietHours } = await import('@/lib/api/notifications');
    expect(updateQuietHours).toHaveBeenCalled();
  });
});
