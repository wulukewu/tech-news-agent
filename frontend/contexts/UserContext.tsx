'use client';

/**
 * User Context
 *
 * This module provides a React Context for managing user profile data.
 * It handles fetching and storing user information separately from authentication state.
 *
 * Responsibilities:
 * - User profile data (id, username, avatar, etc.)
 * - Fetching user data when authenticated
 * - Clearing user data on logout
 *
 * Does NOT handle:
 * - Authentication status (see AuthContext)
 * - Theme preferences (see ThemeContext)
 *
 * Usage:
 * ```tsx
 * // In app/layout.tsx (wrap inside AuthProvider)
 * <UserProvider>
 *   {children}
 * </UserProvider>
 *
 * // In any component
 * const { user, refreshUser } = useUser();
 * ```
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useAuth } from './AuthContext';
import { checkAuthStatus } from '@/lib/api/auth';

/**
 * User interface representing authenticated user information
 */
export interface User {
  id: string;
  discordId: string;
  username?: string;
  avatar?: string;
}

/**
 * User Context Type
 *
 * Defines the shape of the user context.
 * Only includes user profile data and related methods.
 */
export interface UserContextType {
  user: User | null;
  loading: boolean;
  refreshUser: () => Promise<void>;
}

/**
 * User Context
 *
 * Provides user profile data to all child components.
 * Should not be used directly - use the useUser hook instead.
 */
const UserContext = createContext<UserContextType | undefined>(undefined);

/**
 * UserProvider Component
 *
 * Wraps the application and provides user profile data to all child components.
 * Automatically fetches user data when authentication status changes.
 *
 * @param children - Child components to wrap
 *
 * Note: This provider should be nested inside AuthProvider to access authentication state.
 */
export function UserProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const { isAuthenticated } = useAuth();

  /**
   * Refresh user data
   *
   * Fetches the latest user information from the backend.
   * This is automatically called when authentication status changes,
   * but can also be called manually to refresh user data.
   */
  const refreshUser = useCallback(async () => {
    if (!isAuthenticated) {
      setUser(null);
      return;
    }

    try {
      setLoading(true);
      const userData = await checkAuthStatus();
      setUser(userData);
    } catch (error) {
      console.error('Failed to fetch user data:', error);
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated]);

  /**
   * Fetch user data when authentication status changes
   *
   * When the user logs in (isAuthenticated becomes true), fetch user data.
   * When the user logs out (isAuthenticated becomes false), clear user data.
   */
  useEffect(() => {
    refreshUser();
  }, [refreshUser]);

  const value: UserContextType = {
    user,
    loading,
    refreshUser,
  };

  return <UserContext.Provider value={value}>{children}</UserContext.Provider>;
}

/**
 * useUser Hook
 *
 * Custom hook to access user profile data and methods.
 * Must be used within a component wrapped by UserProvider.
 *
 * @returns UserContextType - User profile data and methods
 * @throws Error if used outside of UserProvider
 *
 * @example
 * ```tsx
 * function ProfileComponent() {
 *   const { user, loading, refreshUser } = useUser();
 *
 *   if (loading) {
 *     return <div>Loading...</div>;
 *   }
 *
 *   if (!user) {
 *     return <div>No user data</div>;
 *   }
 *
 *   return (
 *     <div>
 *       <p>Welcome, {user.username}</p>
 *       <img src={user.avatar} alt="Avatar" />
 *       <button onClick={refreshUser}>Refresh</button>
 *     </div>
 *   );
 * }
 * ```
 */
export function useUser(): UserContextType {
  const context = useContext(UserContext);
  if (!context) {
    throw new Error('useUser must be used within UserProvider');
  }
  return context;
}
