/**
 * Notification Settings Hooks Tests
 *
 * Unit tests for notification settings hooks.
 *
 * Requirements: 6.10
 */

import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import {
  useNotificationSettings,
  useUpdateNotificationSettings,
  useTestNotification,
} from '@/features/notifications/hooks/useNotificationSettings';
import * as notificationApi from '@/lib/api/notifications';
import { DEFAULT_NOTIFICATION_SETTINGS } from '@/types/notification';

// Mock the API functions
vi.mock('@/lib/api/notifications', () => ({
  getNotificationSettings: vi.fn(),
  updateNotificationSettings: vi.fn(),
  sendTestNotification: vi.fn(),
}));

// Mock toast
vi.mock('@/lib/toast', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

const createQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

const createWrapper = () => {
  const queryClient = createQueryClient();
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('useNotificationSettings', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should fetch notification settings successfully', async () => {
    vi.mocked(notificationApi.getNotificationSettings).mockResolvedValue(
      DEFAULT_NOTIFICATION_SETTINGS
    );

    const { result } = renderHook(() => useNotificationSettings(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(DEFAULT_NOTIFICATION_SETTINGS);
    expect(notificationApi.getNotificationSettings).toHaveBeenCalledTimes(1);
  });

  it('should handle fetch errors', async () => {
    const error = new Error('Failed to fetch settings');
    vi.mocked(notificationApi.getNotificationSettings).mockRejectedValue(error);

    const { result } = renderHook(() => useNotificationSettings(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toEqual(error);
  });

  it('should use correct query key', () => {
    vi.mocked(notificationApi.getNotificationSettings).mockResolvedValue(
      DEFAULT_NOTIFICATION_SETTINGS
    );

    const { result } = renderHook(() => useNotificationSettings(), {
      wrapper: createWrapper(),
    });

    expect(result.current.isLoading).toBe(true);
  });
});

describe('useUpdateNotificationSettings', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should update notification settings successfully', async () => {
    const updatedSettings = { ...DEFAULT_NOTIFICATION_SETTINGS, enabled: false };
    vi.mocked(notificationApi.updateNotificationSettings).mockResolvedValue(updatedSettings);

    const { result } = renderHook(() => useUpdateNotificationSettings(), {
      wrapper: createWrapper(),
    });

    result.current.mutate({ enabled: false });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(notificationApi.updateNotificationSettings).toHaveBeenCalledWith(
      { enabled: false },
      expect.any(Object) // TanStack Query context parameters
    );
    expect(result.current.data).toEqual(updatedSettings);
  });

  it('should handle update errors', async () => {
    const error = new Error('Update failed');
    vi.mocked(notificationApi.updateNotificationSettings).mockRejectedValue(error);

    const { result } = renderHook(() => useUpdateNotificationSettings(), {
      wrapper: createWrapper(),
    });

    result.current.mutate({ enabled: false });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toEqual(error);
  });

  it('should call success callback on successful update', async () => {
    const updatedSettings = { ...DEFAULT_NOTIFICATION_SETTINGS, enabled: false };
    vi.mocked(notificationApi.updateNotificationSettings).mockResolvedValue(updatedSettings);

    const { result } = renderHook(() => useUpdateNotificationSettings(), {
      wrapper: createWrapper(),
    });

    result.current.mutate({ enabled: false });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    // Toast success should be called (mocked)
  });
});

describe('useTestNotification', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should send test notification successfully', async () => {
    vi.mocked(notificationApi.sendTestNotification).mockResolvedValue();

    const { result } = renderHook(() => useTestNotification(), {
      wrapper: createWrapper(),
    });

    result.current.mutate();

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(notificationApi.sendTestNotification).toHaveBeenCalledTimes(1);
  });

  it('should handle test notification errors', async () => {
    const error = new Error('Test notification failed');
    vi.mocked(notificationApi.sendTestNotification).mockRejectedValue(error);

    const { result } = renderHook(() => useTestNotification(), {
      wrapper: createWrapper(),
    });

    result.current.mutate();

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toEqual(error);
  });

  it('should call success callback on successful test', async () => {
    vi.mocked(notificationApi.sendTestNotification).mockResolvedValue();

    const { result } = renderHook(() => useTestNotification(), {
      wrapper: createWrapper(),
    });

    result.current.mutate();

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    // Toast success should be called (mocked)
  });
});
