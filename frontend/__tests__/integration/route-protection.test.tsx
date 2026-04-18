/**
 * Route Protection Integration Tests
 *
 * Tests for route protection functionality across all /app/* routes.
 * Validates Requirements 13.1, 13.2, 13.3, 13.4, 13.5, 13.6
 *
 * Test Coverage:
 * - Authentication check before rendering
 * - Redirect to /login with return URL for unauthenticated users
 * - Loading screen while checking authentication
 * - Error handling for authentication failures
 * - Protected content not rendered until auth confirmed
 * - Route protection on all /app/* routes
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useRouter, usePathname } from 'next/navigation';
import AppLayout from '@/app/app/layout';
import { useAuth } from '@/contexts/AuthContext';

// Mock Next.js navigation
vi.mock('next/navigation', () => ({
  useRouter: vi.fn(),
  usePathname: vi.fn(),
}));

// Mock AuthContext
vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

describe('Route Protection - App Layout', () => {
  const mockPush = vi.fn();
  const mockCheckAuth = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    (useRouter as any).mockReturnValue({ push: mockPush });
    (usePathname as any).mockReturnValue('/app/articles');
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Requirement 13.1: Check authentication before rendering', () => {
    it('should check authentication status on mount', () => {
      (useAuth as any).mockReturnValue({
        isAuthenticated: true,
        loading: false,
        checkAuth: mockCheckAuth,
      });

      render(
        <AppLayout>
          <div>Protected Content</div>
        </AppLayout>
      );

      // Auth context should be called
      expect(useAuth).toHaveBeenCalled();
    });

    it('should not render protected content while checking auth', () => {
      (useAuth as any).mockReturnValue({
        isAuthenticated: false,
        loading: true,
        checkAuth: mockCheckAuth,
      });

      render(
        <AppLayout>
          <div>Protected Content</div>
        </AppLayout>
      );

      // Should show loading screen, not protected content
      expect(screen.getByText('Checking authentication...')).toBeInTheDocument();
      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
    });
  });

  describe('Requirement 13.2: Redirect to /login with return URL', () => {
    it('should redirect unauthenticated users to login with redirect parameter', async () => {
      (useAuth as any).mockReturnValue({
        isAuthenticated: false,
        loading: false,
        checkAuth: mockCheckAuth,
      });
      (usePathname as any).mockReturnValue('/app/articles');

      render(
        <AppLayout>
          <div>Protected Content</div>
        </AppLayout>
      );

      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/login?redirect=%2Fapp%2Farticles');
      });
    });

    it('should redirect with correct path for different routes', async () => {
      (useAuth as any).mockReturnValue({
        isAuthenticated: false,
        loading: false,
        checkAuth: mockCheckAuth,
      });
      (usePathname as any).mockReturnValue('/app/reading-list');

      render(
        <AppLayout>
          <div>Protected Content</div>
        </AppLayout>
      );

      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/login?redirect=%2Fapp%2Freading-list');
      });
    });

    it('should handle complex paths with query parameters', async () => {
      (useAuth as any).mockReturnValue({
        isAuthenticated: false,
        loading: false,
        checkAuth: mockCheckAuth,
      });
      (usePathname as any).mockReturnValue('/app/articles?tab=recommended&category=tech');

      render(
        <AppLayout>
          <div>Protected Content</div>
        </AppLayout>
      );

      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith(
          '/login?redirect=%2Fapp%2Farticles%3Ftab%3Drecommended%26category%3Dtech'
        );
      });
    });
  });

  describe('Requirement 13.3: Loading screen while checking authentication', () => {
    it('should display loading screen when loading is true', () => {
      (useAuth as any).mockReturnValue({
        isAuthenticated: false,
        loading: true,
        checkAuth: mockCheckAuth,
      });

      render(
        <AppLayout>
          <div>Protected Content</div>
        </AppLayout>
      );

      expect(screen.getByText('Checking authentication...')).toBeInTheDocument();
      // Loading screen is displayed
      const loadingContainer = screen.getByText('Checking authentication...').closest('div');
      expect(loadingContainer).toBeInTheDocument();
    });

    it('should show spinner animation in loading screen', () => {
      (useAuth as any).mockReturnValue({
        isAuthenticated: false,
        loading: true,
        checkAuth: mockCheckAuth,
      });

      const { container } = render(
        <AppLayout>
          <div>Protected Content</div>
        </AppLayout>
      );

      const spinner = container.querySelector('.animate-spin');
      expect(spinner).toBeInTheDocument();
    });

    it('should hide loading screen when authentication check completes', async () => {
      const { rerender } = render(
        <AppLayout>
          <div>Protected Content</div>
        </AppLayout>
      );

      // Initially loading
      (useAuth as any).mockReturnValue({
        isAuthenticated: false,
        loading: true,
        checkAuth: mockCheckAuth,
      });

      rerender(
        <AppLayout>
          <div>Protected Content</div>
        </AppLayout>
      );

      expect(screen.getByText('Checking authentication...')).toBeInTheDocument();

      // Auth check completes
      (useAuth as any).mockReturnValue({
        isAuthenticated: true,
        loading: false,
        checkAuth: mockCheckAuth,
      });

      rerender(
        <AppLayout>
          <div>Protected Content</div>
        </AppLayout>
      );

      await waitFor(() => {
        expect(screen.queryByText('Checking authentication...')).not.toBeInTheDocument();
      });
    });
  });

  describe('Requirement 13.4: Handle authentication errors gracefully', () => {
    it('should display error screen when auth-error event is triggered', async () => {
      (useAuth as any).mockReturnValue({
        isAuthenticated: false,
        loading: false,
        checkAuth: mockCheckAuth,
      });

      render(
        <AppLayout>
          <div>Protected Content</div>
        </AppLayout>
      );

      // Trigger auth error event
      window.dispatchEvent(new Event('auth-error'));

      await waitFor(() => {
        expect(screen.getByText('Authentication Error')).toBeInTheDocument();
      });
    });

    it('should show error message with retry and login options', async () => {
      (useAuth as any).mockReturnValue({
        isAuthenticated: false,
        loading: false,
        checkAuth: mockCheckAuth,
      });

      render(
        <AppLayout>
          <div>Protected Content</div>
        </AppLayout>
      );

      // Trigger auth error event
      window.dispatchEvent(new Event('auth-error'));

      await waitFor(() => {
        expect(screen.getByText('Authentication Error')).toBeInTheDocument();
        expect(screen.getByText(/network issue or an expired session/i)).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /go to login/i })).toBeInTheDocument();
      });
    });

    it('should call checkAuth when retry button is clicked', async () => {
      const user = userEvent.setup();

      (useAuth as any).mockReturnValue({
        isAuthenticated: false,
        loading: false,
        checkAuth: mockCheckAuth,
      });

      render(
        <AppLayout>
          <div>Protected Content</div>
        </AppLayout>
      );

      // Trigger auth error event
      window.dispatchEvent(new Event('auth-error'));

      await waitFor(() => {
        expect(screen.getByText('Authentication Error')).toBeInTheDocument();
      });

      const retryButton = screen.getByRole('button', { name: /try again/i });
      await user.click(retryButton);

      expect(mockCheckAuth).toHaveBeenCalled();
    });

    it('should navigate to login when "Go to Login" button is clicked', async () => {
      const user = userEvent.setup();

      (useAuth as any).mockReturnValue({
        isAuthenticated: false,
        loading: false,
        checkAuth: mockCheckAuth,
      });

      render(
        <AppLayout>
          <div>Protected Content</div>
        </AppLayout>
      );

      // Trigger auth error event
      window.dispatchEvent(new Event('auth-error'));

      await waitFor(() => {
        expect(screen.getByText('Authentication Error')).toBeInTheDocument();
      });

      const loginButton = screen.getByRole('button', { name: /go to login/i });
      await user.click(loginButton);

      expect(mockPush).toHaveBeenCalledWith('/login');
    });
  });

  describe("Requirement 13.5: Don't render protected content until auth confirmed", () => {
    it('should not render children when not authenticated', () => {
      (useAuth as any).mockReturnValue({
        isAuthenticated: false,
        loading: false,
        checkAuth: mockCheckAuth,
      });

      render(
        <AppLayout>
          <div>Protected Content</div>
        </AppLayout>
      );

      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
    });

    it('should not render children while loading', () => {
      (useAuth as any).mockReturnValue({
        isAuthenticated: false,
        loading: true,
        checkAuth: mockCheckAuth,
      });

      render(
        <AppLayout>
          <div>Protected Content</div>
        </AppLayout>
      );

      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
    });

    it('should render children only when authenticated', () => {
      (useAuth as any).mockReturnValue({
        isAuthenticated: true,
        loading: false,
        checkAuth: mockCheckAuth,
      });

      render(
        <AppLayout>
          <div>Protected Content</div>
        </AppLayout>
      );

      expect(screen.getByText('Protected Content')).toBeInTheDocument();
    });

    it('should render layout structure when authenticated', () => {
      (useAuth as any).mockReturnValue({
        isAuthenticated: true,
        loading: false,
        checkAuth: mockCheckAuth,
      });

      const { container } = render(
        <AppLayout>
          <div>Protected Content</div>
        </AppLayout>
      );

      expect(container.querySelector('#main-content')).toBeInTheDocument();
      expect(screen.getByText('Protected Content')).toBeInTheDocument();
    });
  });

  describe('Requirement 13.6: Test route protection on all /app/* routes', () => {
    const protectedRoutes = [
      '/app',
      '/app/articles',
      '/app/reading-list',
      '/app/subscriptions',
      '/app/analytics',
      '/app/settings',
      '/app/system-status',
      '/app/profile',
    ];

    protectedRoutes.forEach((route) => {
      it(`should protect route: ${route}`, async () => {
        (useAuth as any).mockReturnValue({
          isAuthenticated: false,
          loading: false,
          checkAuth: mockCheckAuth,
        });
        (usePathname as any).mockReturnValue(route);

        render(
          <AppLayout>
            <div>Protected Content for {route}</div>
          </AppLayout>
        );

        await waitFor(() => {
          expect(mockPush).toHaveBeenCalledWith(`/login?redirect=${encodeURIComponent(route)}`);
        });

        expect(screen.queryByText(`Protected Content for ${route}`)).not.toBeInTheDocument();
      });

      it(`should allow authenticated access to: ${route}`, () => {
        (useAuth as any).mockReturnValue({
          isAuthenticated: true,
          loading: false,
          checkAuth: mockCheckAuth,
        });
        (usePathname as any).mockReturnValue(route);

        render(
          <AppLayout>
            <div>Protected Content for {route}</div>
          </AppLayout>
        );

        expect(screen.getByText(`Protected Content for ${route}`)).toBeInTheDocument();
        expect(mockPush).not.toHaveBeenCalled();
      });
    });
  });

  describe('Edge Cases', () => {
    it('should handle rapid authentication state changes', async () => {
      const { rerender } = render(
        <AppLayout>
          <div>Protected Content</div>
        </AppLayout>
      );

      // Start with loading
      (useAuth as any).mockReturnValue({
        isAuthenticated: false,
        loading: true,
        checkAuth: mockCheckAuth,
      });

      rerender(
        <AppLayout>
          <div>Protected Content</div>
        </AppLayout>
      );

      // Quickly change to authenticated
      (useAuth as any).mockReturnValue({
        isAuthenticated: true,
        loading: false,
        checkAuth: mockCheckAuth,
      });

      rerender(
        <AppLayout>
          <div>Protected Content</div>
        </AppLayout>
      );

      await waitFor(() => {
        expect(screen.getByText('Protected Content')).toBeInTheDocument();
      });
    });

    it('should cleanup event listeners on unmount', () => {
      const removeEventListenerSpy = vi.spyOn(window, 'removeEventListener');

      (useAuth as any).mockReturnValue({
        isAuthenticated: true,
        loading: false,
        checkAuth: mockCheckAuth,
      });

      const { unmount } = render(
        <AppLayout>
          <div>Protected Content</div>
        </AppLayout>
      );

      unmount();

      expect(removeEventListenerSpy).toHaveBeenCalledWith('auth-error', expect.any(Function));
    });

    it('should handle missing pathname gracefully', async () => {
      (useAuth as any).mockReturnValue({
        isAuthenticated: false,
        loading: false,
        checkAuth: mockCheckAuth,
      });
      (usePathname as any).mockReturnValue(null);

      render(
        <AppLayout>
          <div>Protected Content</div>
        </AppLayout>
      );

      await waitFor(() => {
        expect(mockPush).toHaveBeenCalled();
      });
    });
  });
});
