/**
 * App Layout Components Unit Tests
 *
 * Unit tests for LoadingScreen and ErrorScreen components.
 * Validates Requirements 13.3, 13.4
 *
 * Test Coverage:
 * - LoadingScreen rendering and accessibility
 * - ErrorScreen rendering and interactions
 * - Error handling UI elements
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// We need to test the components in isolation, but they're not exported
// So we'll test them through the layout component
import AppLayout from '@/app/app/layout';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter, usePathname } from 'next/navigation';

vi.mock('next/navigation', () => ({
  useRouter: vi.fn(),
  usePathname: vi.fn(),
}));

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

describe('LoadingScreen Component', () => {
  const mockPush = vi.fn();
  const mockCheckAuth = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    (useRouter as any).mockReturnValue({ push: mockPush });
    (usePathname as any).mockReturnValue('/app/articles');
  });

  describe('Requirement 13.3: Loading screen implementation', () => {
    it('should render loading message', () => {
      (useAuth as any).mockReturnValue({
        isAuthenticated: false,
        loading: true,
        checkAuth: mockCheckAuth,
      });

      render(
        <AppLayout>
          <div>Content</div>
        </AppLayout>
      );

      expect(screen.getByText('Checking authentication...')).toBeInTheDocument();
    });

    it('should render spinner with animation', () => {
      (useAuth as any).mockReturnValue({
        isAuthenticated: false,
        loading: true,
        checkAuth: mockCheckAuth,
      });

      const { container } = render(
        <AppLayout>
          <div>Content</div>
        </AppLayout>
      );

      const spinner = container.querySelector('.animate-spin');
      expect(spinner).toBeInTheDocument();
      expect(spinner).toHaveClass('rounded-full');
      expect(spinner).toHaveClass('border-b-2');
      expect(spinner).toHaveClass('border-primary');
    });

    it('should have proper styling for centering', () => {
      (useAuth as any).mockReturnValue({
        isAuthenticated: false,
        loading: true,
        checkAuth: mockCheckAuth,
      });

      const { container } = render(
        <AppLayout>
          <div>Content</div>
        </AppLayout>
      );

      const loadingContainer = container.querySelector('.flex.min-h-screen');
      expect(loadingContainer).toBeInTheDocument();
      expect(loadingContainer).toHaveClass('items-center');
      expect(loadingContainer).toHaveClass('justify-center');
    });

    it('should have accessible background color', () => {
      (useAuth as any).mockReturnValue({
        isAuthenticated: false,
        loading: true,
        checkAuth: mockCheckAuth,
      });

      const { container } = render(
        <AppLayout>
          <div>Content</div>
        </AppLayout>
      );

      const loadingContainer = container.querySelector('.bg-background');
      expect(loadingContainer).toBeInTheDocument();
    });
  });
});

describe('ErrorScreen Component', () => {
  const mockPush = vi.fn();
  const mockCheckAuth = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    (useRouter as any).mockReturnValue({ push: mockPush });
    (usePathname as any).mockReturnValue('/app/articles');
  });

  describe('Requirement 13.4: Error handling UI', () => {
    it('should render error title and message', async () => {
      (useAuth as any).mockReturnValue({
        isAuthenticated: false,
        loading: false,
        checkAuth: mockCheckAuth,
      });

      render(
        <AppLayout>
          <div>Content</div>
        </AppLayout>
      );

      // Trigger error
      window.dispatchEvent(new Event('auth-error'));

      await screen.findByText('Authentication Error');
      expect(screen.getByText(/network issue or an expired session/i)).toBeInTheDocument();
    });

    it('should render error icon', async () => {
      (useAuth as any).mockReturnValue({
        isAuthenticated: false,
        loading: false,
        checkAuth: mockCheckAuth,
      });

      const { container } = render(
        <AppLayout>
          <div>Content</div>
        </AppLayout>
      );

      // Trigger error
      window.dispatchEvent(new Event('auth-error'));

      await screen.findByText('Authentication Error');

      // Check for AlertCircle icon (lucide-react)
      const iconContainer = container.querySelector('.text-destructive');
      expect(iconContainer).toBeInTheDocument();
    });

    it('should render "Try Again" button', async () => {
      (useAuth as any).mockReturnValue({
        isAuthenticated: false,
        loading: false,
        checkAuth: mockCheckAuth,
      });

      render(
        <AppLayout>
          <div>Content</div>
        </AppLayout>
      );

      // Trigger error
      window.dispatchEvent(new Event('auth-error'));

      await screen.findByText('Authentication Error');

      const retryButton = screen.getByRole('button', { name: /try again/i });
      expect(retryButton).toBeInTheDocument();
      expect(retryButton).toHaveClass('gap-2'); // Has icon
    });

    it('should render "Go to Login" button', async () => {
      (useAuth as any).mockReturnValue({
        isAuthenticated: false,
        loading: false,
        checkAuth: mockCheckAuth,
      });

      render(
        <AppLayout>
          <div>Content</div>
        </AppLayout>
      );

      // Trigger error
      window.dispatchEvent(new Event('auth-error'));

      await screen.findByText('Authentication Error');

      const loginButton = screen.getByRole('button', { name: /go to login/i });
      expect(loginButton).toBeInTheDocument();
    });

    it('should call checkAuth when "Try Again" is clicked', async () => {
      const user = userEvent.setup();

      (useAuth as any).mockReturnValue({
        isAuthenticated: false,
        loading: false,
        checkAuth: mockCheckAuth,
      });

      render(
        <AppLayout>
          <div>Content</div>
        </AppLayout>
      );

      // Trigger error
      window.dispatchEvent(new Event('auth-error'));

      await screen.findByText('Authentication Error');

      const retryButton = screen.getByRole('button', { name: /try again/i });
      await user.click(retryButton);

      expect(mockCheckAuth).toHaveBeenCalledTimes(1);
    });

    it('should navigate to login when "Go to Login" is clicked', async () => {
      const user = userEvent.setup();

      (useAuth as any).mockReturnValue({
        isAuthenticated: false,
        loading: false,
        checkAuth: mockCheckAuth,
      });

      render(
        <AppLayout>
          <div>Content</div>
        </AppLayout>
      );

      // Trigger error
      window.dispatchEvent(new Event('auth-error'));

      await screen.findByText('Authentication Error');

      const loginButton = screen.getByRole('button', { name: /go to login/i });
      await user.click(loginButton);

      expect(mockPush).toHaveBeenCalledWith('/login');
    });

    it('should have responsive layout', async () => {
      (useAuth as any).mockReturnValue({
        isAuthenticated: false,
        loading: false,
        checkAuth: mockCheckAuth,
      });

      const { container } = render(
        <AppLayout>
          <div>Content</div>
        </AppLayout>
      );

      // Trigger error
      window.dispatchEvent(new Event('auth-error'));

      await screen.findByText('Authentication Error');

      // Check for responsive classes
      const errorContainer = container.querySelector('.max-w-md');
      expect(errorContainer).toBeInTheDocument();

      const buttonContainer = container.querySelector('.flex.flex-col.sm\\:flex-row');
      expect(buttonContainer).toBeInTheDocument();
    });

    it('should clear error state after successful retry', async () => {
      const user = userEvent.setup();

      (useAuth as any).mockReturnValue({
        isAuthenticated: false,
        loading: false,
        checkAuth: mockCheckAuth,
      });

      const { rerender } = render(
        <AppLayout>
          <div>Content</div>
        </AppLayout>
      );

      // Trigger error
      window.dispatchEvent(new Event('auth-error'));

      await screen.findByText('Authentication Error');

      // Mock successful auth
      mockCheckAuth.mockResolvedValueOnce(undefined);
      (useAuth as any).mockReturnValue({
        isAuthenticated: true,
        loading: false,
        checkAuth: mockCheckAuth,
      });

      const retryButton = screen.getByRole('button', { name: /try again/i });
      await user.click(retryButton);

      rerender(
        <AppLayout>
          <div>Content</div>
        </AppLayout>
      );

      // Error screen should be gone
      expect(screen.queryByText('Authentication Error')).not.toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA labels for error state', async () => {
      (useAuth as any).mockReturnValue({
        isAuthenticated: false,
        loading: false,
        checkAuth: mockCheckAuth,
      });

      render(
        <AppLayout>
          <div>Content</div>
        </AppLayout>
      );

      // Trigger error
      window.dispatchEvent(new Event('auth-error'));

      await screen.findByText('Authentication Error');

      // Buttons should be accessible
      expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /go to login/i })).toBeInTheDocument();
    });

    it('should have keyboard-accessible buttons', async () => {
      const user = userEvent.setup();

      (useAuth as any).mockReturnValue({
        isAuthenticated: false,
        loading: false,
        checkAuth: mockCheckAuth,
      });

      render(
        <AppLayout>
          <div>Content</div>
        </AppLayout>
      );

      // Trigger error
      window.dispatchEvent(new Event('auth-error'));

      await screen.findByText('Authentication Error');

      const retryButton = screen.getByRole('button', { name: /try again/i });

      // Should be focusable
      await user.tab();
      expect(retryButton).toHaveFocus();

      // Should be activatable with Enter
      await user.keyboard('{Enter}');
      expect(mockCheckAuth).toHaveBeenCalled();
    });
  });
});
