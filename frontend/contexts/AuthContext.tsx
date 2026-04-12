'use client';

/**
 * Authentication Context
 *
 * This module provides a React Context for managing authentication state only.
 * It handles authentication status, login/logout flows, and token validation.
 *
 * Responsibilities:
 * - Authentication status (isAuthenticated, loading)
 * - Login/logout operations
 * - Token validation
 * - Automatic logout on 401 responses
 *
 * Does NOT handle:
 * - User profile data (see UserContext)
 * - Theme preferences (see ThemeContext)
 *
 * Usage:
 * ```tsx
 * // In app/layout.tsx
 * <AuthProvider>
 *   {children}
 * </AuthProvider>
 *
 * // In any component
 * const { isAuthenticated, login, logout } = useAuth();
 * ```
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { checkAuthStatus, logout as logoutApi } from '@/lib/api/auth';

/**
 * Authentication Context Type
 *
 * Defines the shape of the authentication context.
 * Only includes authentication-related state and methods.
 */
export interface AuthContextType {
  isAuthenticated: boolean;
  loading: boolean;
  login: () => void;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
}

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
 */
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);
  const router = useRouter();

  /**
   * Check authentication status
   *
   * Verifies JWT token validity by calling the backend /api/auth/me endpoint.
   * Updates authentication state based on the response.
   *
   * Note: This only checks if the user is authenticated. User data is managed
   * separately by UserContext to prevent unnecessary re-renders.
   */
  const checkAuth = useCallback(async () => {
    try {
      setLoading(true);
      await checkAuthStatus();
      setIsAuthenticated(true);
    } catch (error) {
      // Token is invalid or expired
      setIsAuthenticated(false);
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
   * Note: UserContext will automatically clear user data when it detects
   * the authentication state change.
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
      // Redirect to login page
      router.push('/');
    }
  }, [router]);

  /**
   * Initialize authentication state on mount
   *
   * Checks if the user has a valid JWT token by calling the checkAuth function.
   * Skip this check if we're on the callback page.
   */
  useEffect(() => {
    // Skip auto-check on callback page
    if (typeof window !== 'undefined' && window.location.pathname === '/auth/callback') {
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
      router.push('/');
    };

    window.addEventListener('unauthorized', handleUnauthorized);

    return () => {
      window.removeEventListener('unauthorized', handleUnauthorized);
    };
  }, [router]);

  const value: AuthContextType = {
    isAuthenticated,
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
 *   const { isAuthenticated, login, logout } = useAuth();
 *
 *   if (!isAuthenticated) {
 *     return <button onClick={login}>Login</button>;
 *   }
 *
 *   return <button onClick={logout}>Logout</button>;
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
