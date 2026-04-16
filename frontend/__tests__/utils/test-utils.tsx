/**
 * Test utilities for consistent component testing
 * Provides wrappers, mocks, and helper functions
 */

import React from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from '@/components/ThemeProvider';
import { vi } from 'vitest';

// Mock user context
const mockUser = {
  id: 'test-user-id',
  username: 'testuser',
  email: 'test@example.com',
  avatar: null,
  createdAt: new Date(),
};

const mockUserContext = {
  user: mockUser,
  login: vi.fn(),
  logout: vi.fn(),
  updateUser: vi.fn(),
  isLoading: false,
  error: null,
};

// Mock UserContext
vi.mock('@/contexts/UserContext', () => ({
  useUser: () => mockUserContext,
  UserProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

// Test wrapper with all necessary providers
interface TestWrapperProps {
  children: React.ReactNode;
  queryClient?: QueryClient;
  theme?: 'light' | 'dark' | 'system';
}

export function TestWrapper({ children, queryClient, theme = 'light' }: TestWrapperProps) {
  const client =
    queryClient ||
    new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
          gcTime: 0,
          staleTime: 0,
        },
        mutations: { retry: false },
      },
    });

  return (
    <QueryClientProvider client={client}>
      <ThemeProvider attribute="class" defaultTheme={theme} enableSystem={false}>
        {children}
      </ThemeProvider>
    </QueryClientProvider>
  );
}

// Custom render function with providers
interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  queryClient?: QueryClient;
  theme?: 'light' | 'dark' | 'system';
}

export function renderWithProviders(ui: React.ReactElement, options: CustomRenderOptions = {}) {
  const { queryClient, theme, ...renderOptions } = options;

  const Wrapper = ({ children }: { children: React.ReactNode }) => (
    <TestWrapper queryClient={queryClient} theme={theme}>
      {children}
    </TestWrapper>
  );

  return render(ui, { wrapper: Wrapper, ...renderOptions });
}

// Mock implementations for common hooks and utilities
export const mockNavigationItems = [
  { href: '/dashboard', label: 'Dashboard', icon: () => <div data-testid="dashboard-icon" /> },
  { href: '/articles', label: 'Articles', icon: () => <div data-testid="articles-icon" /> },
  {
    href: '/reading-list',
    label: 'Reading List',
    icon: () => <div data-testid="reading-list-icon" />,
  },
];

export const mockBreadcrumbItems = [
  { label: 'Home', href: '/' },
  { label: 'Articles', href: '/articles' },
  { label: 'Current Page', current: true },
];

// Viewport utilities for responsive testing
export function mockViewport(width: number, height: number = 768) {
  Object.defineProperty(window, 'innerWidth', {
    writable: true,
    configurable: true,
    value: width,
  });

  Object.defineProperty(window, 'innerHeight', {
    writable: true,
    configurable: true,
    value: height,
  });

  // Trigger resize event
  window.dispatchEvent(new Event('resize'));
}

// Media query utilities
export function mockMediaQuery(query: string, matches: boolean = false) {
  const mockMatchMedia = vi.fn().mockImplementation((query) => ({
    matches,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  }));

  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: mockMatchMedia,
  });

  return mockMatchMedia;
}

// Keyboard event utilities
export function createKeyboardEvent(
  type: 'keydown' | 'keyup' | 'keypress',
  key: string,
  options: Partial<KeyboardEventInit> = {}
) {
  return new KeyboardEvent(type, {
    key,
    bubbles: true,
    cancelable: true,
    ...options,
  });
}

// Touch event utilities for mobile testing
export function createTouchEvent(
  type: 'touchstart' | 'touchmove' | 'touchend',
  touches: Array<{ clientX: number; clientY: number }> = []
) {
  const touchList = touches.map((touch, index) => ({
    identifier: index,
    target: document.body,
    clientX: touch.clientX,
    clientY: touch.clientY,
    pageX: touch.clientX,
    pageY: touch.clientY,
    screenX: touch.clientX,
    screenY: touch.clientY,
    radiusX: 10,
    radiusY: 10,
    rotationAngle: 0,
    force: 1,
  }));

  return new TouchEvent(type, {
    touches: touchList as any,
    targetTouches: touchList as any,
    changedTouches: touchList as any,
    bubbles: true,
    cancelable: true,
  });
}

// Accessibility testing utilities
export function checkAccessibility(container: HTMLElement) {
  // Check for proper heading hierarchy
  const headings = container.querySelectorAll('h1, h2, h3, h4, h5, h6');
  const headingLevels = Array.from(headings).map((h) => parseInt(h.tagName.charAt(1)));

  // Should have at least one h1
  expect(headingLevels.includes(1)).toBe(true);

  // Check for proper landmarks
  const main = container.querySelector('main');
  if (main) {
    expect(main).toHaveAttribute('id');
  }

  // Check for proper link attributes
  const links = container.querySelectorAll('a');
  links.forEach((link) => {
    expect(link).toHaveAttribute('href');
  });

  // Check for proper button labels
  const buttons = container.querySelectorAll('button');
  buttons.forEach((button) => {
    const hasLabel =
      button.textContent?.trim() ||
      button.getAttribute('aria-label') ||
      button.getAttribute('aria-labelledby');
    expect(hasLabel).toBeTruthy();
  });
}

// Performance testing utilities
export function measureRenderTime(renderFn: () => void): number {
  const start = performance.now();
  renderFn();
  const end = performance.now();
  return end - start;
}

// Cleanup utilities
export function cleanupMocks() {
  vi.clearAllMocks();
  vi.resetAllMocks();
}

// Export mock user context for tests that need it
export { mockUser, mockUserContext };
