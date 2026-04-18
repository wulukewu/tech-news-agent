/**
 * Integration Tests: Authentication Flow
 *
 * Tests the complete authentication flow including:
 * - Login redirect logic with redirect query parameter
 * - OAuth callback redirect to original path
 * - Authenticated user redirect from /login to /app/articles
 *
 * **Validates: Requirements 2.4, 2.5, 3.4**
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { useRouter, useSearchParams } from 'next/navigation';
import LoginPage from '@/app/login/page';
import CallbackPage from '@/app/auth/callback/page';
import { useAuth } from '@/contexts/AuthContext';

// Mock Next.js navigation
vi.mock('next/navigation', () => ({
  useRouter: vi.fn(),
  useSearchParams: vi.fn(),
  usePathname: vi.fn(() => '/login'),
}));

// Mock AuthContext
vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

// Mock Logo component
vi.mock('@/components/Logo', () => ({
  Logo: () => <div data-testid="logo">Logo</div>,
}));

// Mock UI components
vi.mock('@/components/ui/button', () => ({
  Button: ({ children, onClick, ...props }: any) => (
    <button onClick={onClick} {...props}>
      {children}
    </button>
  ),
}));

vi.mock('@/components/ui/card', () => ({
  Card: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  CardHeader: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  CardTitle: ({ children, ...props }: any) => <h2 {...props}>{children}</h2>,
  CardDescription: ({ children, ...props }: any) => <p {...props}>{children}</p>,
  CardContent: ({ children, ...props }: any) => <div {...props}>{children}</div>,
}));

describe('Authentication Flow Integration Tests', () => {
  let mockPush: ReturnType<typeof vi.fn>;
  let mockLogin: ReturnType<typeof vi.fn>;
  let mockCheckAuth: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    mockPush = vi.fn();
    mockLogin = vi.fn();
    mockCheckAuth = vi.fn();

    (useRouter as ReturnType<typeof vi.fn>).mockReturnValue({
      push: mockPush,
      replace: vi.fn(),
      back: vi.fn(),
      forward: vi.fn(),
      refresh: vi.fn(),
      prefetch: vi.fn(),
    });

    // Clear sessionStorage before each test
    sessionStorage.clear();
  });

  afterEach(() => {
    vi.clearAllMocks();
    sessionStorage.clear();
  });

  describe('Login Page - Redirect Query Parameter', () => {
    it('should redirect authenticated users to /app/articles by default', async () => {
      // Requirement 2.4: Redirects authenticated users to /app/articles
      (useSearchParams as ReturnType<typeof vi.fn>).mockReturnValue({
        get: vi.fn(() => null), // No redirect parameter
      });

      (useAuth as ReturnType<typeof vi.fn>).mockReturnValue({
        isAuthenticated: true,
        loading: false,
        login: mockLogin,
        logout: vi.fn(),
        checkAuth: mockCheckAuth,
      });

      render(<LoginPage />);

      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/app/articles');
      });
    });

    it('should redirect authenticated users to original path from redirect parameter', async () => {
      // Requirement 2.5: Redirects to original path after login
      const redirectPath = '/app/reading-list';

      (useSearchParams as ReturnType<typeof vi.fn>).mockReturnValue({
        get: vi.fn((param: string) => (param === 'redirect' ? redirectPath : null)),
      });

      (useAuth as ReturnType<typeof vi.fn>).mockReturnValue({
        isAuthenticated: true,
        loading: false,
        login: mockLogin,
        logout: vi.fn(),
        checkAuth: mockCheckAuth,
      });

      render(<LoginPage />);

      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith(redirectPath);
      });
    });

    it('should pass redirect parameter to login function when clicking login button', async () => {
      // Requirement 2.5: Use redirect query parameter
      const redirectPath = '/app/subscriptions';

      (useSearchParams as ReturnType<typeof vi.fn>).mockReturnValue({
        get: vi.fn((param: string) => (param === 'redirect' ? redirectPath : null)),
      });

      (useAuth as ReturnType<typeof vi.fn>).mockReturnValue({
        isAuthenticated: false,
        loading: false,
        login: mockLogin,
        logout: vi.fn(),
        checkAuth: mockCheckAuth,
      });

      render(<LoginPage />);

      const loginButton = screen.getByText(/Login with Discord/i);
      loginButton.click();

      expect(mockLogin).toHaveBeenCalledWith(redirectPath);
    });

    it('should call login without redirect parameter when none is provided', async () => {
      (useSearchParams as ReturnType<typeof vi.fn>).mockReturnValue({
        get: vi.fn(() => null),
      });

      (useAuth as ReturnType<typeof vi.fn>).mockReturnValue({
        isAuthenticated: false,
        loading: false,
        login: mockLogin,
        logout: vi.fn(),
        checkAuth: mockCheckAuth,
      });

      render(<LoginPage />);

      const loginButton = screen.getByText(/Login with Discord/i);
      loginButton.click();

      expect(mockLogin).toHaveBeenCalledWith('/app/articles');
    });

    it('should show loading state while checking authentication', () => {
      (useSearchParams as ReturnType<typeof vi.fn>).mockReturnValue({
        get: vi.fn(() => null),
      });

      (useAuth as ReturnType<typeof vi.fn>).mockReturnValue({
        isAuthenticated: false,
        loading: true,
        login: mockLogin,
        logout: vi.fn(),
        checkAuth: mockCheckAuth,
      });

      render(<LoginPage />);

      expect(screen.getByText(/載入中/i)).toBeInTheDocument();
    });

    it('should not render login form for authenticated users', () => {
      (useSearchParams as ReturnType<typeof vi.fn>).mockReturnValue({
        get: vi.fn(() => null),
      });

      (useAuth as ReturnType<typeof vi.fn>).mockReturnValue({
        isAuthenticated: true,
        loading: false,
        login: mockLogin,
        logout: vi.fn(),
        checkAuth: mockCheckAuth,
      });

      const { container } = render(<LoginPage />);

      expect(container.firstChild).toBeNull();
    });
  });

  describe('OAuth Callback - Redirect to Original Path', () => {
    it('should redirect to /app/articles by default after successful authentication', async () => {
      // Requirement 3.4: OAuth callback redirects to original path or default
      (useSearchParams as ReturnType<typeof vi.fn>).mockReturnValue({
        get: vi.fn((param: string) => {
          if (param === 'token') return 'mock-jwt-token';
          return null;
        }),
      });

      (useAuth as ReturnType<typeof vi.fn>).mockReturnValue({
        isAuthenticated: false,
        loading: false,
        login: mockLogin,
        logout: vi.fn(),
        checkAuth: mockCheckAuth,
      });

      render(<CallbackPage />);

      await waitFor(() => {
        expect(mockCheckAuth).toHaveBeenCalled();
        expect(mockPush).toHaveBeenCalledWith('/app/articles');
      });
    });

    it('should redirect to path from redirect query parameter', async () => {
      // Requirement 2.5: Redirect to original path
      const redirectPath = '/app/analytics';

      (useSearchParams as ReturnType<typeof vi.fn>).mockReturnValue({
        get: vi.fn((param: string) => {
          if (param === 'token') return 'mock-jwt-token';
          if (param === 'redirect') return redirectPath;
          return null;
        }),
      });

      (useAuth as ReturnType<typeof vi.fn>).mockReturnValue({
        isAuthenticated: false,
        loading: false,
        login: mockLogin,
        logout: vi.fn(),
        checkAuth: mockCheckAuth,
      });

      render(<CallbackPage />);

      await waitFor(() => {
        expect(mockCheckAuth).toHaveBeenCalled();
        expect(mockPush).toHaveBeenCalledWith(redirectPath);
      });
    });

    it('should redirect to path from sessionStorage when no query parameter', async () => {
      // Requirement 2.5: Redirect to original path stored in sessionStorage
      const redirectPath = '/app/profile';
      sessionStorage.setItem('auth_redirect', redirectPath);

      (useSearchParams as ReturnType<typeof vi.fn>).mockReturnValue({
        get: vi.fn((param: string) => {
          if (param === 'token') return 'mock-jwt-token';
          return null;
        }),
      });

      (useAuth as ReturnType<typeof vi.fn>).mockReturnValue({
        isAuthenticated: false,
        loading: false,
        login: mockLogin,
        logout: vi.fn(),
        checkAuth: mockCheckAuth,
      });

      render(<CallbackPage />);

      await waitFor(() => {
        expect(mockCheckAuth).toHaveBeenCalled();
        expect(mockPush).toHaveBeenCalledWith(redirectPath);
      });
    });

    it('should clear sessionStorage after using redirect path', async () => {
      // Ensure sessionStorage is cleaned up after redirect
      const redirectPath = '/app/settings';
      sessionStorage.setItem('auth_redirect', redirectPath);

      (useSearchParams as ReturnType<typeof vi.fn>).mockReturnValue({
        get: vi.fn((param: string) => {
          if (param === 'token') return 'mock-jwt-token';
          return null;
        }),
      });

      (useAuth as ReturnType<typeof vi.fn>).mockReturnValue({
        isAuthenticated: false,
        loading: false,
        login: mockLogin,
        logout: vi.fn(),
        checkAuth: mockCheckAuth,
      });

      render(<CallbackPage />);

      await waitFor(() => {
        expect(sessionStorage.getItem('auth_redirect')).toBeNull();
      });
    });

    it('should prioritize redirect query parameter over sessionStorage', async () => {
      // Query parameter should take precedence
      const queryRedirect = '/app/articles';
      const storageRedirect = '/app/reading-list';

      sessionStorage.setItem('auth_redirect', storageRedirect);

      (useSearchParams as ReturnType<typeof vi.fn>).mockReturnValue({
        get: vi.fn((param: string) => {
          if (param === 'token') return 'mock-jwt-token';
          if (param === 'redirect') return queryRedirect;
          return null;
        }),
      });

      (useAuth as ReturnType<typeof vi.fn>).mockReturnValue({
        isAuthenticated: false,
        loading: false,
        login: mockLogin,
        logout: vi.fn(),
        checkAuth: mockCheckAuth,
      });

      render(<CallbackPage />);

      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith(queryRedirect);
      });
    });

    it('should handle OAuth error and display error message', async () => {
      // Requirement 3.4: Handle OAuth errors
      (useSearchParams as ReturnType<typeof vi.fn>).mockReturnValue({
        get: vi.fn((param: string) => {
          if (param === 'error') return 'access_denied';
          if (param === 'error_description') return 'User denied authorization';
          return null;
        }),
      });

      (useAuth as ReturnType<typeof vi.fn>).mockReturnValue({
        isAuthenticated: false,
        loading: false,
        login: mockLogin,
        logout: vi.fn(),
        checkAuth: mockCheckAuth,
      });

      render(<CallbackPage />);

      await waitFor(() => {
        expect(screen.getByText(/驗證失敗/i)).toBeInTheDocument();
      });
    });

    it('should handle missing token and display error', async () => {
      // Requirement 3.4: Handle missing token
      (useSearchParams as ReturnType<typeof vi.fn>).mockReturnValue({
        get: vi.fn(() => null), // No token
      });

      (useAuth as ReturnType<typeof vi.fn>).mockReturnValue({
        isAuthenticated: false,
        loading: false,
        login: mockLogin,
        logout: vi.fn(),
        checkAuth: mockCheckAuth,
      });

      render(<CallbackPage />);

      await waitFor(() => {
        expect(screen.getByText(/未收到認證令牌/i)).toBeInTheDocument();
      });
    });
  });

  describe('End-to-End Authentication Flow', () => {
    it('should complete full authentication flow with redirect', async () => {
      // Requirement 3.4: Test complete authentication flow
      const originalPath = '/app/subscriptions';

      // Step 1: User tries to access protected route, gets redirected to login
      (useSearchParams as ReturnType<typeof vi.fn>).mockReturnValue({
        get: vi.fn((param: string) => (param === 'redirect' ? originalPath : null)),
      });

      (useAuth as ReturnType<typeof vi.fn>).mockReturnValue({
        isAuthenticated: false,
        loading: false,
        login: mockLogin,
        logout: vi.fn(),
        checkAuth: mockCheckAuth,
      });

      const { rerender } = render(<LoginPage />);

      // Step 2: User clicks login button
      const loginButton = screen.getByText(/Login with Discord/i);
      loginButton.click();

      // Verify login was called with redirect path
      expect(mockLogin).toHaveBeenCalledWith(originalPath);

      // Step 3: After OAuth, user returns to callback page
      (useSearchParams as ReturnType<typeof vi.fn>).mockReturnValue({
        get: vi.fn((param: string) => {
          if (param === 'token') return 'mock-jwt-token';
          if (param === 'redirect') return originalPath;
          return null;
        }),
      });

      rerender(<CallbackPage />);

      // Step 4: Callback page should redirect to original path
      await waitFor(() => {
        expect(mockCheckAuth).toHaveBeenCalled();
        expect(mockPush).toHaveBeenCalledWith(originalPath);
      });
    });

    it('should handle authentication flow without redirect parameter', async () => {
      // Default flow without specific redirect
      (useSearchParams as ReturnType<typeof vi.fn>).mockReturnValue({
        get: vi.fn(() => null),
      });

      (useAuth as ReturnType<typeof vi.fn>).mockReturnValue({
        isAuthenticated: false,
        loading: false,
        login: mockLogin,
        logout: vi.fn(),
        checkAuth: mockCheckAuth,
      });

      const { rerender } = render(<LoginPage />);

      // User clicks login
      const loginButton = screen.getByText(/Login with Discord/i);
      loginButton.click();

      expect(mockLogin).toHaveBeenCalledWith('/app/articles');

      // After OAuth callback
      (useSearchParams as ReturnType<typeof vi.fn>).mockReturnValue({
        get: vi.fn((param: string) => (param === 'token' ? 'mock-jwt-token' : null)),
      });

      rerender(<CallbackPage />);

      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/app/articles');
      });
    });
  });
});
