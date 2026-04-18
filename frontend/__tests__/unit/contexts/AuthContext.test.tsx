/**
 * Unit Tests: AuthContext
 *
 * Tests the AuthContext functionality including:
 * - Login function with redirect parameter
 * - SessionStorage management for redirect paths
 * - Logout functionality
 * - Authentication state management
 *
 * **Validates: Requirements 2.4, 2.5, 3.4**
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { AuthProvider, useAuth } from '@/contexts/AuthContext';
import * as authApi from '@/lib/api/auth';

// Mock Next.js router
const mockPush = vi.fn();
const mockReplace = vi.fn();

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
    replace: mockReplace,
    back: vi.fn(),
    forward: vi.fn(),
    refresh: vi.fn(),
    prefetch: vi.fn(),
  }),
  usePathname: () => '/test',
}));

// Mock auth API
vi.mock('@/lib/api/auth', () => ({
  checkAuthStatus: vi.fn(),
  logout: vi.fn(),
}));

describe('AuthContext', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    sessionStorage.clear();
    delete (window as any).location;
    (window as any).location = { href: '' };
    process.env.NEXT_PUBLIC_API_BASE_URL = 'http://localhost:8000';
  });

  afterEach(() => {
    sessionStorage.clear();
  });

  describe('Login Function', () => {
    it('should redirect to OAuth endpoint without redirect parameter', () => {
      // Requirement 2.4: Basic login functionality
      const { result } = renderHook(() => useAuth(), {
        wrapper: AuthProvider,
      });

      act(() => {
        result.current.login();
      });

      expect(window.location.href).toBe('http://localhost:8000/api/auth/discord/login');
      expect(sessionStorage.getItem('auth_redirect')).toBeNull();
    });

    it('should store redirect path in sessionStorage when provided', () => {
      // Requirement 2.5: Store redirect path for OAuth flow
      const redirectPath = '/app/reading-list';

      const { result } = renderHook(() => useAuth(), {
        wrapper: AuthProvider,
      });

      act(() => {
        result.current.login(redirectPath);
      });

      expect(sessionStorage.getItem('auth_redirect')).toBe(redirectPath);
      expect(window.location.href).toBe('http://localhost:8000/api/auth/discord/login');
    });

    it('should clear sessionStorage when login called without redirect', () => {
      // Ensure clean state
      sessionStorage.setItem('auth_redirect', '/old/path');

      const { result } = renderHook(() => useAuth(), {
        wrapper: AuthProvider,
      });

      act(() => {
        result.current.login();
      });

      expect(sessionStorage.getItem('auth_redirect')).toBeNull();
    });

    it('should handle multiple redirect paths correctly', () => {
      // Test updating redirect path
      const { result } = renderHook(() => useAuth(), {
        wrapper: AuthProvider,
      });

      act(() => {
        result.current.login('/app/articles');
      });

      expect(sessionStorage.getItem('auth_redirect')).toBe('/app/articles');

      // Reset location
      (window as any).location = { href: '' };

      act(() => {
        result.current.login('/app/subscriptions');
      });

      expect(sessionStorage.getItem('auth_redirect')).toBe('/app/subscriptions');
    });

    it('should handle special characters in redirect path', () => {
      // Test URL encoding
      const redirectPath = '/app/articles?category=AI&sort=latest';

      const { result } = renderHook(() => useAuth(), {
        wrapper: AuthProvider,
      });

      act(() => {
        result.current.login(redirectPath);
      });

      expect(sessionStorage.getItem('auth_redirect')).toBe(redirectPath);
    });
  });

  describe('Logout Function', () => {
    it('should call logout API and redirect to login page', async () => {
      vi.mocked(authApi.logout).mockResolvedValue();

      const { result } = renderHook(() => useAuth(), {
        wrapper: AuthProvider,
      });

      await act(async () => {
        await result.current.logout();
      });

      expect(authApi.logout).toHaveBeenCalled();
      expect(mockPush).toHaveBeenCalledWith('/login');
      expect(result.current.isAuthenticated).toBe(false);
    });

    it('should redirect to login even if API call fails', async () => {
      vi.mocked(authApi.logout).mockRejectedValue(new Error('API Error'));

      const { result } = renderHook(() => useAuth(), {
        wrapper: AuthProvider,
      });

      await act(async () => {
        await result.current.logout();
      });

      expect(mockPush).toHaveBeenCalledWith('/login');
      expect(result.current.isAuthenticated).toBe(false);
    });
  });

  describe('Check Auth Function', () => {
    it('should set authenticated state when token is valid', async () => {
      vi.mocked(authApi.checkAuthStatus).mockResolvedValue({
        id: 'user-123',
        username: 'testuser',
        email: 'test@example.com',
        avatar: null,
        discord_id: 'discord-123',
        created_at: new Date().toISOString(),
      });

      const { result } = renderHook(() => useAuth(), {
        wrapper: AuthProvider,
      });

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.isAuthenticated).toBe(true);
    });

    it('should set unauthenticated state when token is invalid', async () => {
      vi.mocked(authApi.checkAuthStatus).mockRejectedValue(new Error('Unauthorized'));

      const { result } = renderHook(() => useAuth(), {
        wrapper: AuthProvider,
      });

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.isAuthenticated).toBe(false);
    });

    it('should handle network errors gracefully', async () => {
      vi.mocked(authApi.checkAuthStatus).mockRejectedValue(new Error('Network Error'));

      const { result } = renderHook(() => useAuth(), {
        wrapper: AuthProvider,
      });

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.isAuthenticated).toBe(false);
    });
  });

  describe('Authentication State Management', () => {
    it('should start with loading state', () => {
      const { result } = renderHook(() => useAuth(), {
        wrapper: AuthProvider,
      });

      expect(result.current.loading).toBe(true);
      expect(result.current.isAuthenticated).toBe(false);
    });

    it('should handle unauthorized event', async () => {
      vi.mocked(authApi.checkAuthStatus).mockResolvedValue({
        id: 'user-123',
        username: 'testuser',
        email: 'test@example.com',
        avatar: null,
        discord_id: 'discord-123',
        created_at: new Date().toISOString(),
      });

      const { result } = renderHook(() => useAuth(), {
        wrapper: AuthProvider,
      });

      await waitFor(() => {
        expect(result.current.isAuthenticated).toBe(true);
      });

      // Simulate unauthorized event
      act(() => {
        window.dispatchEvent(new Event('unauthorized'));
      });

      await waitFor(() => {
        expect(result.current.isAuthenticated).toBe(false);
        expect(mockPush).toHaveBeenCalledWith('/login');
      });
    });

    it('should provide all required context values', () => {
      const { result } = renderHook(() => useAuth(), {
        wrapper: AuthProvider,
      });

      expect(result.current).toHaveProperty('isAuthenticated');
      expect(result.current).toHaveProperty('loading');
      expect(result.current).toHaveProperty('login');
      expect(result.current).toHaveProperty('logout');
      expect(result.current).toHaveProperty('checkAuth');
    });
  });

  describe('Error Handling', () => {
    it('should throw error when useAuth is used outside AuthProvider', () => {
      expect(() => {
        renderHook(() => useAuth());
      }).toThrow('useAuth must be used within AuthProvider');
    });
  });
});
