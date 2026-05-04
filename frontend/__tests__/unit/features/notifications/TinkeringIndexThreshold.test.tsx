import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { TinkeringIndexThreshold } from '@/features/notifications/components/TinkeringIndexThreshold';

import { getTechnicalDepthSettings } from '@/lib/api/notifications';

vi.mock('@/lib/api/notifications', () => ({
  getTechnicalDepthSettings: vi.fn(),
  getTechnicalDepthLevels: vi.fn().mockResolvedValue([]),
  getTechnicalDepthStats: vi.fn().mockResolvedValue(null),
  updateTechnicalDepthSettings: vi.fn(),
}));

vi.mock('@/lib/toast', () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}));

const defaultSettings = {
  user_id: 'user1',
  threshold: 'intermediate' as const,
  enabled: true,
  threshold_numeric: 3,
};

describe('TinkeringIndexThreshold', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    vi.clearAllMocks();
    vi.mocked(getTechnicalDepthSettings).mockResolvedValue(defaultSettings);
  });

  const renderWithQueryClient = (component: React.ReactElement) =>
    render(<QueryClientProvider client={queryClient}>{component}</QueryClientProvider>);

  it('should render the threshold component title', async () => {
    const onThresholdChange = vi.fn();
    renderWithQueryClient(
      <TinkeringIndexThreshold threshold={3} onThresholdChange={onThresholdChange} />
    );
    await waitFor(() => {
      expect(screen.getByText('Technical Depth Filter')).toBeInTheDocument();
    });
  });

  it.skip('should render slider after loading', async () => {
    const onThresholdChange = vi.fn();
    renderWithQueryClient(
      <TinkeringIndexThreshold threshold={3} onThresholdChange={onThresholdChange} />
    );
    await waitFor(
      () => {
        expect(screen.getByRole('slider')).toBeInTheDocument();
      },
      { timeout: 5000 }
    );
  });

  it.skip('should be disabled when disabled prop is true', async () => {
    const onThresholdChange = vi.fn();
    renderWithQueryClient(
      <TinkeringIndexThreshold
        threshold={3}
        onThresholdChange={onThresholdChange}
        disabled={true}
      />
    );
    await waitFor(
      () => {
        expect(screen.getByRole('slider')).toBeInTheDocument();
      },
      { timeout: 5000 }
    );
    expect(screen.getByRole('slider')).toHaveAttribute('data-disabled', '');
  });

  it.skip('should render without crashing with threshold 1', async () => {
    const onThresholdChange = vi.fn();
    renderWithQueryClient(
      <TinkeringIndexThreshold threshold={1} onThresholdChange={onThresholdChange} />
    );
    await waitFor(
      () => {
        expect(screen.getByRole('slider')).toBeInTheDocument();
      },
      { timeout: 5000 }
    );
  });

  it.skip('should render without crashing with threshold 5', async () => {
    const onThresholdChange = vi.fn();
    renderWithQueryClient(
      <TinkeringIndexThreshold threshold={5} onThresholdChange={onThresholdChange} />
    );
    await waitFor(
      () => {
        expect(screen.getByRole('slider')).toBeInTheDocument();
      },
      { timeout: 5000 }
    );
  });
});
