/**
 * useAuth Hook
 *
 * Re-exports the useAuth hook from AuthContext for consistent import patterns.
 * This allows components to import from lib/hooks instead of contexts.
 *
 * Note: After refactoring, useAuth only provides authentication state.
 * For user profile data, use useUser from UserContext.
 *
 * @example
 * ```tsx
 * import { useAuth } from '@/lib/hooks/useAuth';
 * import { useUser } from '@/contexts/UserContext';
 *
 * function MyComponent() {
 *   const { isAuthenticated, logout } = useAuth();
 *   const { user } = useUser();
 *   // ...
 * }
 * ```
 */

export { useAuth } from '@/contexts/AuthContext';
