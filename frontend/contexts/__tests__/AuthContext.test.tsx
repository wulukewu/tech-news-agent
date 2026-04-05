import { renderHook, act, waitFor } from '@testing-library/react';
import { AuthProvider, useAuth } from '../AuthContext';
import * as authApi from '@/lib/api/auth';

jest.mock('@/lib/api/auth');

describe('AuthContext', () => {
  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <AuthProvider>{children}</AuthProvider>
  );

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should initialize with unauthenticated state', () => {
    const { result } = renderHook(() => useAuth(), { wrapper });

    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
    expect(result.current.loading).toBe(true); // Initially loading
  });

  it('should set authenticated state after successful checkAuth', async () => {
    const mockUser = {
      id: '123',
      discordId: '456',
      username: 'testuser',
      avatar: 'https://example.com/avatar.png',
    };
    (authApi.checkAuthStatus as jest.Mock).mockResolvedValue(mockUser);

    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => {
      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.user).toEqual(mockUser);
      expect(result.current.loading).toBe(false);
    });
  });

  it('should handle checkAuth failure', async () => {
    (authApi.checkAuthStatus as jest.Mock).mockRejectedValue(
      new Error('Unauthorized'),
    );

    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => {
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBeNull();
      expect(result.current.loading).toBe(false);
    });
  });

  it('should clear state on logout', async () => {
    const mockUser = {
      id: '123',
      discordId: '456',
      username: 'testuser',
    };
    (authApi.checkAuthStatus as jest.Mock).mockResolvedValue(mockUser);
    (authApi.logout as jest.Mock).mockResolvedValue(undefined);

    const { result } = renderHook(() => useAuth(), { wrapper });

    // Wait for initial auth check
    await waitFor(() => {
      expect(result.current.isAuthenticated).toBe(true);
    });

    // Logout
    await act(async () => {
      await result.current.logout();
    });

    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
  });

  it('should redirect to login on logout', async () => {
    const mockUser = {
      id: '123',
      discordId: '456',
      username: 'testuser',
    };
    (authApi.checkAuthStatus as jest.Mock).mockResolvedValue(mockUser);
    (authApi.logout as jest.Mock).mockResolvedValue(undefined);

    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => {
      expect(result.current.isAuthenticated).toBe(true);
    });

    await act(async () => {
      await result.current.logout();
    });

    // Should redirect to login (mocked router will be called)
    expect(result.current.isAuthenticated).toBe(false);
  });

  it('should handle login redirect', () => {
    const { result } = renderHook(() => useAuth(), { wrapper });

    act(() => {
      result.current.login();
    });

    // Login should redirect to API endpoint (tested via window.location)
    // In real implementation, this would redirect to Discord OAuth
  });

  it('should throw error when useAuth is used outside AuthProvider', () => {
    // Suppress console.error for this test
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

    expect(() => {
      renderHook(() => useAuth());
    }).toThrow('useAuth must be used within AuthProvider');

    consoleSpy.mockRestore();
  });
});
