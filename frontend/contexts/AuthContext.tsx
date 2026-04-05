'use client';

/**
 * Authentication Context
 *
 * This module provides a React Context for managing global authentication state.
 * It handles user authentication status, login/logout flows, and token validation.
 *
 * Features:
 * - Global authentication state management
 * - Automatic authentication check on mount
 * - Token validation via backend API
 * - Persistent authentication across page refreshes
 * - Automatic logout on 401 responses
 *
 * Usage:
 * 1. Wrap your app with AuthProvider in the root layout
 * 2. Use the useAuth hook in any component to access auth state
 *
 * @example
 * ```tsx
 * // In app/layout.tsx
 * <AuthProvider>
 *   {children}
 * </AuthProvider>
 *
 * // In any component
 * const { isAuthenticated, user, logout } = useAuth();
 * ```
 */

import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
} from 'react';
import { useRouter } from 'next/navigation';
import { AuthContextType, User } from '@/types/auth';
import { checkAuthStatus, logout as logoutApi } from '@/lib/api/auth';

/**
 * Authentication Context
 *
 * Provides authentication state and methods to all child components.
 * Should not be used directly - use the useAuth hook instead.
 */
const AuthContext = createContext<AuthContextType | undefined>(undefined);

/**
 * AuthProvider Component
 *
 * Wraps the application and provides authentication state to all child components.
 * Automatically checks authentication status on mount and listens for unauthorized events.
 *
 * @param children - Child components to wrap
 *
 * @example
 * ```tsx
 * <AuthProvider>
 *   <App />
 * </AuthProvider>
 * ```
 */
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const router = useRouter();

  /**
   * Check authentication status
   *
   * Verifies JWT token validity by calling the backend /api/auth/me endpoint.
   * Updates authentication state based on the response.
   *
   * - On success: Sets isAuthenticated to true and stores user information
   * - On failure: Sets isAuthenticated to false and clears user information
   *
   * This function is called:
   * - On component mount (to restore auth state after page refresh)
   * - After successful OAuth callback
   * - When manually triggered by components
   */
  const checkAuth = useCallback(async () => {
    try {
      setLoading(true);
      const userData = await checkAuthStatus();
      setIsAuthenticated(true);
      setUser(userData);
    } catch (error) {
      // Token is invalid or expired
      setIsAuthenticated(false);
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Login function
   *
   * Redirects the user to the FastAPI Discord OAuth2 login endpoint.
   * The backend will handle the OAuth2 flow and redirect back to the callback page.
   */
  const login = useCallback(() => {
    const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
    window.location.href = `${apiBaseUrl}/api/auth/discord/login`;
  }, []);

  /**
   * Logout function
   *
   * Logs out the user by:
   * 1. Calling the backend logout API to revoke the JWT token
   * 2. Clearing the authentication state
   * 3. Redirecting to the login page
   *
   * @throws Error if logout API call fails
   */
  const logout = useCallback(async () => {
    try {
      await logoutApi();
    } catch (error) {
      console.error('Logout API call failed:', error);
      // Continue with logout even if API call fails
    } finally {
      // Clear authentication state
      setIsAuthenticated(false);
      setUser(null);
      // Redirect to login page
      router.push('/');
    }
  }, [router]);

  /**
   * Initialize authentication state on mount
   *
   * Checks if the user has a valid JWT token (stored in localStorage)
   * by calling the checkAuth function.
   *
   * Skip this check if we're on the callback page, as it will handle
   * authentication after receiving the token from the URL.
   */
  useEffect(() => {
    // Skip auto-check on callback page
    if (
      typeof window !== 'undefined' &&
      window.location.pathname === '/auth/callback'
    ) {
      setLoading(false);
      return;
    }
    checkAuth();
  }, [checkAuth]);

  /**
   * Listen for unauthorized events
   *
   * When the API client receives a 401 Unauthorized response,
   * it dispatches an 'unauthorized' event. This listener catches
   * that event and triggers the logout flow.
   */
  useEffect(() => {
    const handleUnauthorized = () => {
      setIsAuthenticated(false);
      setUser(null);
      router.push('/');
    };

    window.addEventListener('unauthorized', handleUnauthorized);

    return () => {
      window.removeEventListener('unauthorized', handleUnauthorized);
    };
  }, [router]);

  const value: AuthContextType = {
    isAuthenticated,
    user,
    loading,
    login,
    logout,
    checkAuth,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/**
 * useAuth Hook
 *
 * Custom hook to access authentication state and methods.
 * Must be used within a component wrapped by AuthProvider.
 *
 * @returns AuthContextType - Authentication state and methods
 * @throws Error if used outside of AuthProvider
 *
 * @example
 * ```tsx
 * function MyComponent() {
 *   const { isAuthenticated, user, logout } = useAuth();
 *
 *   if (!isAuthenticated) {
 *     return <div>Please login</div>;
 *   }
 *
 *   return (
 *     <div>
 *       <p>Welcome, {user?.username}</p>
 *       <button onClick={logout}>Logout</button>
 *     </div>
 *   );
 * }
 * ```
 */
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
