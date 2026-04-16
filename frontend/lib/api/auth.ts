/**
 * Authentication API functions
 *
 * This module provides functions for authentication-related API calls:
 * - checkAuthStatus: Verify JWT token validity and get current user
 * - logout: Logout and revoke JWT token
 * - refreshToken: Refresh JWT token
 *
 * All functions use the apiClient which automatically includes the Authorization header
 * with the JWT token from localStorage.
 */

import { apiClient } from './client';
import { User } from '@/types/auth';

/**
 * Get the JWT token from localStorage
 */
export function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('auth_token');
}

/**
 * Set the JWT token in localStorage
 */
export function setToken(token: string): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem('auth_token', token);
}

/**
 * Remove the JWT token from localStorage
 */
export function removeToken(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem('auth_token');
}

/**
 * Check authentication status and get current user information
 *
 * Calls GET /api/auth/me to verify the JWT token validity
 * and retrieve the current user's information.
 *
 * @returns Promise<User> - Current user information
 * @throws Error if token is invalid or request fails
 *
 * @example
 * ```typescript
 * try {
 *   const user = await checkAuthStatus();
 *   console.log('Authenticated as:', user.username);
 * } catch (error) {
 *   console.error('Not authenticated');
 * }
 * ```
 */
export async function checkAuthStatus(): Promise<User> {
  const response = await apiClient.get<User>('/api/auth/me');
  return response.data;
}

/**
 * Logout the current user
 *
 * Calls POST /api/auth/logout to revoke the JWT token
 * and removes the token from localStorage.
 *
 * @returns Promise<void>
 * @throws Error if logout request fails
 *
 * @example
 * ```typescript
 * try {
 *   await logout();
 *   console.log('Logged out successfully');
 * } catch (error) {
 *   console.error('Logout failed:', error);
 * }
 * ```
 */
export async function logout(): Promise<void> {
  try {
    await apiClient.post<void>('/api/auth/logout');
  } finally {
    removeToken();
  }
}

/**
 * Refresh the JWT token
 *
 * Calls POST /api/auth/refresh to refresh the JWT token
 * and updates the token in localStorage.
 *
 * @returns Promise<void>
 * @throws Error if refresh request fails
 *
 * @example
 * ```typescript
 * try {
 *   await refreshToken();
 *   console.log('Token refreshed successfully');
 * } catch (error) {
 *   console.error('Token refresh failed:', error);
 * }
 * ```
 */
export async function refreshToken(): Promise<void> {
  await apiClient.post<void>('/api/auth/refresh');
}
