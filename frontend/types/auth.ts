/**
 * Authentication-related type definitions
 *
 * This file defines the core types for authentication state management,
 * user information, and authentication context.
 */

/**
 * User interface representing authenticated user information
 *
 * @property id - Unique user identifier
 * @property discordId - Discord user ID
 * @property username - Discord username (optional)
 * @property avatar - Discord avatar URL (optional)
 * @property email - User email address (optional)
 */
export interface User {
  id: string;
  discordId: string;
  username?: string;
  avatar?: string;
  email?: string;
}

/**
 * Authentication context type defining the shape of the auth context
 *
 * @property isAuthenticated - Whether the user is currently authenticated
 * @property user - Current user information or null if not authenticated
 * @property loading - Whether authentication check is in progress
 * @property login - Function to initiate login flow
 * @property logout - Function to logout and clear authentication state
 * @property checkAuth - Function to verify JWT token validity
 */
export interface AuthContextType {
  isAuthenticated: boolean;
  user: User | null;
  loading: boolean;
  login: () => void;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
}

/**
 * Authentication error interface for handling auth-related errors
 *
 * @property error - Error type/code
 * @property message - Human-readable error message
 * @property description - Optional detailed error description
 */
export interface AuthError {
  error: string;
  message: string;
  description?: string;
}
