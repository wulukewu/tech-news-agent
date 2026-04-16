/**
 * Unit Tests for useAuth Hook
 *
 * Tests authentication state management and user information retrieval.
 *
 * Requirements: 5.10
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useAuth } from '@/lib/auth/useAuth';
import { apiClient } from '@/lib/api/client';
import type { User } from '@/lib/auth/useAuth';

// Mock the API client
vi.mock('@/lib/api/client');

describe('useAuth Hook', () => {
  let queryClient: QueryClient;

  const mockUser: User = {
    user_id: 'test-user-123',
    discord_id: 'discord-456',
    username: 'testuser',
    avatar: 'https://example.com/avatar.png',
  };

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
          gcTime: 0,
        },
      },
    });

    vi.clearAllMocks();
  });

  afterEach(() => {
    queryClient.clear();
  });

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  describe('Authentication State', () => {
    it('should return authenticated state when user is logged in', async () => {
      vi.mocked(apiClient.get).mockResolvedValue({ data: mockUser });

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.user).toEqual(mockUser);
      expect(result.current.error).toBeNull();
    });

    it('should return unauthenticated state when user is not logged in', async () => {
      vi.mocked(apiClient.get).mockRejectedValue({
        response: { status: 401 },
      });

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBeNull();
      expect(result.current.error).toBeNull();
    });

    it('should show loading state initially', () => {
      vi.mocked(apiClient.get).mockImplementation(() => new Promise(() => {}));

      const { result } = renderHook(() => useAuth(), { wrapper });

      expect(result.current.isLoading).toBe(true);
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBeNull();
    });
  });

  describe('Error Handling', () => {
    it('should handle 401 errors as unauthenticated state', async () => {
      vi.mocked(apiClient.get).mockRejectedValue({
        response: { status: 401 },
      });

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBeNull();
      expect(result.current.error).toBeNull();
    });

    it('should handle network errors', async () => {
      const networkError = new Error('Network error');
      vi.mocked(apiClient.get).mockRejectedValue(networkError);

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.error).toEqual(networkError);
    });

    it('should handle server errors', async () => {
      const serverError = {
        response: { status: 500 },
        message: 'Internal server error',
      };
      vi.mocked(apiClient.get).mockRejectedValue(serverError);

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.error).toBeTruthy();
    });

    it('should not retry on authentication failures', async () => {
      vi.mocked(apiClient.get).mockRejectedValue({
        response: { status: 401 },
      });

      renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        const queries = queryClient.getQueryCache().getAll();
        expect(queries.length).toBe(1);
      });

      // Should only call API once (no retries)
      expect(vi.mocked(apiClient.get).mock.calls.length).toBe(1);
    });
  });

  describe('User Information', () => {
    it('should return complete user information', async () => {
      vi.mocked(apiClient.get).mockResolvedValue({ data: mockUser });

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.isAuthenticated).toBe(true);
      });

      expect(result.current.user).toEqual({
        user_id: 'test-user-123',
        discord_id: 'discord-456',
        username: 'testuser',
        avatar: 'https://example.com/avatar.png',
      });
    });

    it('should handle user without optional fields', async () => {
      const minimalUser: User = {
        user_id: 'test-user-123',
        discord_id: 'discord-456',
      };

      vi.mocked(apiClient.get).mockResolvedValue({ data: minimalUser });

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.isAuthenticated).toBe(true);
      });

      expect(result.current.user).toEqual(minimalUser);
      expect(result.current.user?.username).toBeUndefined();
      expect(result.current.user?.avatar).toBeUndefined();
    });
  });

  describe('Caching Behavior', () => {
    it('should cache authentication state for 5 minutes', async () => {
      vi.mocked(apiClient.get).mockResolvedValue({ data: mockUser });

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.isAuthenticated).toBe(true);
      });

      const queries = queryClient.getQueryCache().getAll();
      expect(queries[0].options.staleTime).toBe(5 * 60 * 1000);
    });

    it('should use cached data for subsequent hook instances', async () => {
      vi.mocked(apiClient.get).mockResolvedValue({ data: mockUser });

      const { result: result1 } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result1.current.isAuthenticated).toBe(true);
      });

      // Create second hook instance
      const { result: result2 } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result2.current.isAuthenticated).toBe(true);
      });

      // Should only call API once due to caching
      expect(vi.mocked(apiClient.get).mock.calls.length).toBe(1);

      // Both hooks should have the same data
      expect(result1.current.user).toEqual(result2.current.user);
    });
  });

  describe('Query Key', () => {
    it('should use correct query key', async () => {
      vi.mocked(apiClient.get).mockResolvedValue({ data: mockUser });

      renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        const queries = queryClient.getQueryCache().getAll();
        expect(queries.length).toBe(1);
        expect(queries[0].queryKey).toEqual(['auth', 'current-user']);
      });
    });
  });

  describe('API Integration', () => {
    it('should call correct API endpoint', async () => {
      vi.mocked(apiClient.get).mockResolvedValue({ data: mockUser });

      renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(vi.mocked(apiClient.get)).toHaveBeenCalledWith('/api/auth/me');
      });
    });

    it('should handle API response format correctly', async () => {
      const apiResponse = { data: mockUser };
      vi.mocked(apiClient.get).mockResolvedValue(apiResponse);

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.isAuthenticated).toBe(true);
      });

      expect(result.current.user).toEqual(mockUser);
    });
  });

  describe('State Transitions', () => {
    it('should transition from loading to authenticated', async () => {
      let resolveAuth: (value: any) => void;
      const authPromise = new Promise((resolve) => {
        resolveAuth = resolve;
      });

      vi.mocked(apiClient.get).mockReturnValue(authPromise as any);

      const { result } = renderHook(() => useAuth(), { wrapper });

      expect(result.current.isLoading).toBe(true);
      expect(result.current.isAuthenticated).toBe(false);

      resolveAuth!({ data: mockUser });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.user).toEqual(mockUser);
    });

    it('should transition from loading to unauthenticated', async () => {
      let rejectAuth: (value: any) => void;
      const authPromise = new Promise((_, reject) => {
        rejectAuth = reject;
      });

      vi.mocked(apiClient.get).mockReturnValue(authPromise as any);

      const { result } = renderHook(() => useAuth(), { wrapper });

      expect(result.current.isLoading).toBe(true);

      rejectAuth!({ response: { status: 401 } });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBeNull();
    });

    it('should transition from loading to error', async () => {
      let rejectAuth: (value: any) => void;
      const authPromise = new Promise((_, reject) => {
        rejectAuth = reject;
      });

      vi.mocked(apiClient.get).mockReturnValue(authPromise as any);

      const { result } = renderHook(() => useAuth(), { wrapper });

      expect(result.current.isLoading).toBe(true);

      const error = new Error('Network error');
      rejectAuth!(error);

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.error).toEqual(error);
    });
  });
});
