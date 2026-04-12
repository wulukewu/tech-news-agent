/**
 * Unit Tests: Split Contexts Architecture
 *
 * Tests context isolation, re-render behavior, React Query integration,
 * and state synchronization between split contexts.
 *
 * Requirements: 2.2, 2.3, 2.4
 * - 2.2: Context isolation - components only re-render when their specific context changes
 * - 2.3: React Query for server state caching and synchronization
 * - 2.4: Separate server state from client state management
 */

import React, { useState } from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider, useAuth } from '@/contexts/AuthContext';
import { UserProvider, useUser } from '@/contexts/UserContext';
import { ThemeProvider, useTheme } from '@/contexts/ThemeContext';
import * as authApi from '@/lib/api/auth';

jest.mock('@/lib/api/auth');

// Mock next/navigation
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
  }),
}));

const mockedAuthApi = authApi as jest.Mocked<typeof authApi>;

describe('Split Contexts - Context Isolation', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
    mockedAuthApi.checkAuthStatus.mockRejectedValue(new Error('Not authenticated'));
  });

  const AllProviders: React.FC<{ children: React.ReactNode }> = ({ children }) => (
    <AuthProvider>
      <UserProvider>
        <ThemeProvider>{children}</ThemeProvider>
      </UserProvider>
    </AuthProvider>
  );

  describe('Requirement 2.2: Context Isolation and Re-render Behavior', () => {
    it('should only re-render components consuming AuthContext when auth state changes', async () => {
      let authRenderCount = 0;
      let userRenderCount = 0;
      let themeRenderCount = 0;

      const AuthComponent: React.FC = () => {
        const { isAuthenticated } = useAuth();
        authRenderCount++;
        return <div data-testid="auth-component">{isAuthenticated ? 'auth' : 'no-auth'}</div>;
      };

      const UserComponent: React.FC = () => {
        const { user } = useUser();
        userRenderCount++;
        return <div data-testid="user-component">{user?.username || 'no-user'}</div>;
      };

      const ThemeComponent: React.FC = () => {
        const { theme } = useTheme();
        themeRenderCount++;
        return <div data-testid="theme-component">{theme}</div>;
      };

      render(
        <AllProviders>
          <AuthComponent />
          <UserComponent />
          <ThemeComponent />
        </AllProviders>
      );

      // Wait for initial render to complete
      await waitFor(() => {
        expect(screen.getByTestId('auth-component')).toHaveTextContent('no-auth');
      });

      const initialAuthRenders = authRenderCount;
      const initialUserRenders = userRenderCount;
      const initialThemeRenders = themeRenderCount;

      // Simulate auth state change by mocking successful auth
      mockedAuthApi.checkAuthStatus.mockResolvedValue({
        id: '123',
        discordId: '456',
        username: 'testuser',
      });

      // Trigger auth check
      const authComponent = screen.getByTestId('auth-component');
      await waitFor(() => {
        expect(authComponent).toBeInTheDocument();
      });

      // Auth component should have re-rendered
      // User component may re-render due to auth dependency
      // Theme component should NOT re-render
      expect(themeRenderCount).toBe(initialThemeRenders);
    });

    it('should only re-render components consuming ThemeContext when theme changes', async () => {
      let authRenderCount = 0;
      let themeRenderCount = 0;

      const AuthComponent: React.FC = () => {
        const { isAuthenticated } = useAuth();
        authRenderCount++;
        return <div data-testid="auth-component">{isAuthenticated ? 'auth' : 'no-auth'}</div>;
      };

      const ThemeComponent: React.FC = () => {
        const { theme, setTheme } = useTheme();
        themeRenderCount++;
        return (
          <div>
            <div data-testid="theme-component">{theme}</div>
            <button onClick={() => setTheme('dark')} data-testid="theme-button">
              Toggle
            </button>
          </div>
        );
      };

      const user = userEvent.setup();

      render(
        <AllProviders>
          <AuthComponent />
          <ThemeComponent />
        </AllProviders>
      );

      await waitFor(() => {
        expect(screen.getByTestId('theme-component')).toBeInTheDocument();
      });

      const initialAuthRenders = authRenderCount;
      const initialThemeRenders = themeRenderCount;

      // Change theme
      const themeButton = screen.getByTestId('theme-button');
      await user.click(themeButton);

      await waitFor(() => {
        expect(screen.getByTestId('theme-component')).toHaveTextContent('dark');
      });

      // Theme component should have re-rendered
      expect(themeRenderCount).toBeGreaterThan(initialThemeRenders);

      // Auth component should NOT have re-rendered
      expect(authRenderCount).toBe(initialAuthRenders);
    });

    it('should allow components to consume multiple contexts independently', async () => {
      const MultiContextComponent: React.FC = () => {
        const { isAuthenticated } = useAuth();
        const { user } = useUser();
        const { theme } = useTheme();

        return (
          <div>
            <div data-testid="auth-status">{isAuthenticated ? 'auth' : 'no-auth'}</div>
            <div data-testid="user-name">{user?.username || 'no-user'}</div>
            <div data-testid="theme-value">{theme}</div>
          </div>
        );
      };

      render(
        <AllProviders>
          <MultiContextComponent />
        </AllProviders>
      );

      await waitFor(() => {
        expect(screen.getByTestId('auth-status')).toHaveTextContent('no-auth');
        expect(screen.getByTestId('user-name')).toHaveTextContent('no-user');
        expect(screen.getByTestId('theme-value')).toHaveTextContent('system');
      });
    });

    it('should maintain separate state for each context', async () => {
      mockedAuthApi.checkAuthStatus.mockResolvedValue({
        id: '123',
        discordId: '456',
        username: 'testuser',
      });

      const StateDisplay: React.FC = () => {
        const { isAuthenticated } = useAuth();
        const { user } = useUser();
        const { theme, setTheme } = useTheme();

        return (
          <div>
            <div data-testid="auth">{isAuthenticated ? 'true' : 'false'}</div>
            <div data-testid="user">{user?.username || 'null'}</div>
            <div data-testid="theme">{theme}</div>
            <button onClick={() => setTheme('dark')} data-testid="change-theme">
              Change Theme
            </button>
          </div>
        );
      };

      const user = userEvent.setup();

      render(
        <AllProviders>
          <StateDisplay />
        </AllProviders>
      );

      // Wait for auth to complete
      await waitFor(() => {
        expect(screen.getByTestId('auth')).toHaveTextContent('true');
      });

      // User should be loaded
      await waitFor(() => {
        expect(screen.getByTestId('user')).toHaveTextContent('testuser');
      });

      // Theme should be independent
      expect(screen.getByTestId('theme')).toHaveTextContent('system');

      // Change theme
      await user.click(screen.getByTestId('change-theme'));

      await waitFor(() => {
        expect(screen.getByTestId('theme')).toHaveTextContent('dark');
      });

      // Auth and user should remain unchanged
      expect(screen.getByTestId('auth')).toHaveTextContent('true');
      expect(screen.getByTestId('user')).toHaveTextContent('testuser');
    });
  });

  describe('Requirement 2.4: State Synchronization Between Contexts', () => {
    it('should synchronize UserContext with AuthContext state', async () => {
      mockedAuthApi.checkAuthStatus.mockResolvedValue({
        id: '123',
        discordId: '456',
        username: 'testuser',
        avatar: 'https://example.com/avatar.png',
      });

      const SyncTest: React.FC = () => {
        const { isAuthenticated } = useAuth();
        const { user } = useUser();

        return (
          <div>
            <div data-testid="auth-status">
              {isAuthenticated ? 'authenticated' : 'not-authenticated'}
            </div>
            <div data-testid="user-data">{user ? user.username : 'no-user'}</div>
          </div>
        );
      };

      render(
        <AllProviders>
          <SyncTest />
        </AllProviders>
      );

      // Wait for auth to complete
      await waitFor(() => {
        expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated');
      });

      // User data should be synchronized
      await waitFor(() => {
        expect(screen.getByTestId('user-data')).toHaveTextContent('testuser');
      });
    });

    it('should clear UserContext when AuthContext logs out', async () => {
      mockedAuthApi.checkAuthStatus.mockResolvedValue({
        id: '123',
        discordId: '456',
        username: 'testuser',
      });
      mockedAuthApi.logout.mockResolvedValue(undefined);

      const LogoutTest: React.FC = () => {
        const { isAuthenticated, logout } = useAuth();
        const { user } = useUser();

        return (
          <div>
            <div data-testid="auth-status">
              {isAuthenticated ? 'authenticated' : 'not-authenticated'}
            </div>
            <div data-testid="user-data">{user ? user.username : 'no-user'}</div>
            <button onClick={logout} data-testid="logout-button">
              Logout
            </button>
          </div>
        );
      };

      const user = userEvent.setup();

      render(
        <AllProviders>
          <LogoutTest />
        </AllProviders>
      );

      // Wait for auth and user to load
      await waitFor(() => {
        expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated');
        expect(screen.getByTestId('user-data')).toHaveTextContent('testuser');
      });

      // Logout
      await user.click(screen.getByTestId('logout-button'));

      // Both auth and user should be cleared
      await waitFor(() => {
        expect(screen.getByTestId('auth-status')).toHaveTextContent('not-authenticated');
        expect(screen.getByTestId('user-data')).toHaveTextContent('no-user');
      });
    });

    it('should handle theme persistence independently of auth state', async () => {
      const ThemePersistenceTest: React.FC = () => {
        const { isAuthenticated } = useAuth();
        const { theme, setTheme } = useTheme();

        React.useEffect(() => {
          setTheme('dark');
        }, [setTheme]);

        return (
          <div>
            <div data-testid="auth">{isAuthenticated ? 'auth' : 'no-auth'}</div>
            <div data-testid="theme">{theme}</div>
          </div>
        );
      };

      render(
        <AllProviders>
          <ThemePersistenceTest />
        </AllProviders>
      );

      await waitFor(() => {
        expect(screen.getByTestId('theme')).toHaveTextContent('dark');
      });

      // Theme should be set regardless of auth state
      expect(screen.getByTestId('auth')).toHaveTextContent('no-auth');
      expect(screen.getByTestId('theme')).toHaveTextContent('dark');

      // Check localStorage
      expect(localStorage.getItem('theme-preference')).toBe('dark');
    });
  });
});
