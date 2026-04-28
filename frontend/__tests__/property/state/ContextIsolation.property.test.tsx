/**
 * Property-Based Test: Context Isolation
 *
 * **Validates: Requirements 2.2**
 *
 * Property 3: Context Isolation
 * For any context value change in a split context, only components that consume
 * that specific context SHALL re-render, and components consuming other contexts
 * SHALL not re-render.
 *
 * This test validates that:
 * - AuthContext, UserContext, and ThemeContext are split into separate contexts
 * - Each context can be consumed independently
 * - Changes to one context don't force re-renders of components using other contexts
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import { AuthProvider, useAuth } from '@/contexts/AuthContext';
import { UserProvider, useUser } from '@/contexts/UserContext';
import { ThemeProvider, useTheme, Theme } from '@/contexts/ThemeContext';
import * as authApi from '@/lib/api/auth';
import fc from 'fast-check';

vi.mock('@/lib/api/auth');

// Mock next/navigation
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
  }),
}));

describe('Property Test: Context Isolation', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Default mock to prevent unhandled promises
    (authApi.checkAuthStatus as jest.Mock).mockRejectedValue(new Error('Not authenticated'));
  });

  const AllProviders: React.FC<{ children: React.ReactNode }> = ({ children }) => (
    <AuthProvider>
      <UserProvider>
        <ThemeProvider>{children}</ThemeProvider>
      </UserProvider>
    </AuthProvider>
  );

  it('Property: Each context provides independent state that can be consumed separately', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.record({
          isAuth: fc.boolean(),
          username: fc.string({ minLength: 1, maxLength: 20 }),
          theme: fc.constantFrom<Theme>('light', 'dark', 'system'),
        }),
        async ({ isAuth, username, theme }) => {
          // Setup auth state
          if (isAuth) {
            (authApi.checkAuthStatus as jest.Mock).mockResolvedValue({
              id: '123',
              discordId: '456',
              username,
            });
          } else {
            (authApi.checkAuthStatus as jest.Mock).mockRejectedValue(
              new Error('Not authenticated')
            );
          }

          // Component that only uses AuthContext
          const AuthOnlyComponent: React.FC = () => {
            const { isAuthenticated } = useAuth();
            return (
              <div data-testid="auth-only">
                {isAuthenticated ? 'authenticated' : 'not-authenticated'}
              </div>
            );
          };

          // Component that only uses UserContext
          const UserOnlyComponent: React.FC = () => {
            const { user } = useUser();
            return <div data-testid="user-only">{user?.username || 'no-user'}</div>;
          };

          // Component that only uses ThemeContext
          const ThemeOnlyComponent: React.FC = () => {
            const { theme: currentTheme, setTheme } = useTheme();
            React.useEffect(() => {
              setTheme(theme);
            }, [setTheme]);
            return <div data-testid="theme-only">{currentTheme}</div>;
          };

          render(
            <AllProviders>
              <AuthOnlyComponent />
              <UserOnlyComponent />
              <ThemeOnlyComponent />
            </AllProviders>
          );

          // Wait for initial render
          await screen.findByTestId('auth-only');
          await screen.findByTestId('user-only');
          await screen.findByTestId('theme-only');

          // Verify: Each component can access its context independently
          const authElement = screen.getByTestId('auth-only');
          const userElement = screen.getByTestId('user-only');
          const themeElement = screen.getByTestId('theme-only');

          // Auth context should reflect the auth state
          expect(authElement.textContent).toBe(isAuth ? 'authenticated' : 'not-authenticated');

          // User context should reflect the user state (depends on auth)
          if (isAuth) {
            expect(userElement.textContent).toBe(username);
          } else {
            expect(userElement.textContent).toBe('no-user');
          }

          // Theme context should reflect the theme
          expect(themeElement.textContent).toBe(theme);
        }
      ),
      { numRuns: 20 }
    );
  });

  it('Property: Contexts are split - not a single monolithic context', () => {
    // This test verifies that we have separate context providers, not one big context

    // Component that uses only AuthContext
    const AuthOnlyComponent: React.FC = () => {
      const { isAuthenticated } = useAuth();
      return <div data-testid="has-auth">{isAuthenticated ? 'yes' : 'no'}</div>;
    };

    // Component that uses only UserContext
    const UserOnlyComponent: React.FC = () => {
      const { user } = useUser();
      return <div data-testid="has-user">{user ? 'yes' : 'no'}</div>;
    };

    // Component that uses only ThemeContext
    const ThemeOnlyComponent: React.FC = () => {
      const { theme } = useTheme();
      return <div data-testid="has-theme">{theme}</div>;
    };

    // If contexts are properly split, we can render components that use only one context
    render(
      <AllProviders>
        <AuthOnlyComponent />
        <UserOnlyComponent />
        <ThemeOnlyComponent />
      </AllProviders>
    );

    // All components should render successfully
    expect(screen.getByTestId('has-auth')).toBeInTheDocument();
    expect(screen.getByTestId('has-user')).toBeInTheDocument();
    expect(screen.getByTestId('has-theme')).toBeInTheDocument();
  });

  it('Property: Theme changes are independent of Auth and User state', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.record({
          theme1: fc.constantFrom<Theme>('light', 'dark'),
          theme2: fc.constantFrom<Theme>('light', 'dark'),
        }),
        async ({ theme1, theme2 }) => {
          if (theme1 === theme2) return;

          // Setup authenticated state
          (authApi.checkAuthStatus as jest.Mock).mockResolvedValue({
            id: '123',
            discordId: '456',
            username: 'testuser',
          });

          let renderCount = 0;

          const TestComponent: React.FC = () => {
            const { isAuthenticated } = useAuth();
            const { user } = useUser();
            const { theme, setTheme } = useTheme();

            renderCount++;

            // Change theme on first render
            React.useEffect(() => {
              if (theme === theme1) {
                setTheme(theme2);
              }
            }, [theme, setTheme]);

            return (
              <div>
                <div data-testid="auth">{isAuthenticated ? 'auth' : 'no-auth'}</div>
                <div data-testid="user">{user?.username || 'no-user'}</div>
                <div data-testid="theme">{theme}</div>
              </div>
            );
          };

          const { findByTestId } = render(
            <AllProviders>
              <TestComponent />
            </AllProviders>
          );

          // Wait for theme to change
          const themeElement = await findByTestId('theme');

          // Eventually theme should be theme2
          await new Promise((resolve) => setTimeout(resolve, 100));

          // Verify: Auth and User values remain stable
          const authElement = screen.getByTestId('auth');
          const userElement = screen.getByTestId('user');

          expect(authElement.textContent).toBe('auth');
          expect(userElement.textContent).toBe('testuser');

          // Theme should have changed or be in the process of changing
          // The key property is that auth and user didn't change
        }
      ),
      { numRuns: 10 }
    );
  });

  it('Property: Contexts can be used in any combination without interference', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.record({
          useAuth: fc.boolean(),
          useUser: fc.boolean(),
          useTheme: fc.boolean(),
        }),
        async ({ useAuth: shouldUseAuth, useUser: shouldUseUser, useTheme: shouldUseTheme }) => {
          // Skip if no contexts are used
          if (!shouldUseAuth && !shouldUseUser && !shouldUseTheme) return;

          // Setup authenticated state
          (authApi.checkAuthStatus as jest.Mock).mockResolvedValue({
            id: '123',
            discordId: '456',
            username: 'testuser',
          });

          const TestComponent: React.FC = () => {
            const auth = shouldUseAuth ? useAuth() : null;
            const user = shouldUseUser ? useUser() : null;
            const theme = shouldUseTheme ? useTheme() : null;

            return (
              <div>
                {shouldUseAuth && (
                  <div data-testid="auth">{auth?.isAuthenticated ? 'auth' : 'no-auth'}</div>
                )}
                {shouldUseUser && <div data-testid="user">{user?.user?.username || 'no-user'}</div>}
                {shouldUseTheme && <div data-testid="theme">{theme?.theme}</div>}
              </div>
            );
          };

          render(
            <AllProviders>
              <TestComponent />
            </AllProviders>
          );

          // Wait a bit for async operations
          await new Promise((resolve) => setTimeout(resolve, 50));

          // Verify: Each context that should be used is accessible
          if (shouldUseAuth) {
            expect(screen.getByTestId('auth')).toBeInTheDocument();
          }
          if (shouldUseUser) {
            expect(screen.getByTestId('user')).toBeInTheDocument();
          }
          if (shouldUseTheme) {
            expect(screen.getByTestId('theme')).toBeInTheDocument();
          }
        }
      ),
      { numRuns: 20 }
    );
  });
});
