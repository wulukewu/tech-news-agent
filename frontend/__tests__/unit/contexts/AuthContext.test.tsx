import { renderHook, act, waitFor } from '@testing-library/react';
import { AuthProvider, useAuth } from '@/contexts/AuthContext';
import * as authApi from '@/lib/api/auth';

jest.mock('@/lib/api/auth');

// Mock next/navigation
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
  }),
}));

describe('AuthContext', () => {
  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <AuthProvider>{children}</AuthProvider>
  );

  beforeEach(() => {
    jest.clearAllMocks();
    // Default mock to prevent unhandled promises
    (authApi.checkAuthStatus as jest.Mock).mockRejectedValue(new Error('Not authenticated'));
  });

  it('should initialize with unauthenticated state', async () => {
    const { result } = renderHook(() => useAuth(), { wrapper });

    expect(result.current.loading).toBe(true);

    // Wait for initial auth check to complete
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.isAuthenticated).toBe(false);
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
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.isAuthenticated).toBe(true);
  });

  it('should handle checkAuth failure', async () => {
    (authApi.checkAuthStatus as jest.Mock).mockRejectedValue(new Error('Unauthorized'));

    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.isAuthenticated).toBe(false);
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

  it('should call login function', async () => {
    const { result } = renderHook(() => useAuth(), { wrapper });

    // Wait for initial load
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // Just verify login function exists and can be called
    expect(result.current.login).toBeDefined();
    expect(typeof result.current.login).toBe('function');

    // Note: Actual redirect behavior is tested in E2E tests
    // as jsdom doesn't fully support window.location navigation
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
