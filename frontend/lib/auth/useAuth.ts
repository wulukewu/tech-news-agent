/**
 * Authentication Hook
 *
 * Provides authentication state and user information.
 * This is a simplified implementation for the system monitor feature.
 *
 * Requirements: 5.10
 */

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';

/**
 * User information
 */
export interface User {
  user_id: string;
  discord_id: string;
  username?: string;
  avatar?: string;
  email?: string;
}

/**
 * Authentication state
 */
export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: Error | null;
}

/**
 * Fetch current user information
 */
export async function getCurrentUser(): Promise<User | null> {
  try {
    const response = await apiClient.get<{ data: User }>('/api/auth/me');
    return response.data.data;
  } catch (error) {
    // If 401, user is not authenticated
    if ((error as any)?.response?.status === 401) {
      return null;
    }
    throw error;
  }
}

/**
 * Hook to get authentication state
 *
 * Requirements: 5.10
 *
 * @returns Authentication state with user information
 */
export function useAuth(): AuthState {
  const {
    data: user,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['auth', 'current-user'],
    queryFn: getCurrentUser,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: false, // Don't retry on auth failures
  });

  return {
    user: user || null,
    isAuthenticated: !!user,
    isLoading,
    error: error as Error | null,
  };
}
