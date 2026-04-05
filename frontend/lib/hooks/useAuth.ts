/**
 * useAuth Hook
 *
 * Re-exports the useAuth hook from AuthContext for consistent import patterns.
 * This allows components to import from lib/hooks instead of contexts.
 *
 * @example
 * ```tsx
 * import { useAuth } from '@/lib/hooks/useAuth';
 *
 * function MyComponent() {
 *   const { isAuthenticated, user, logout } = useAuth();
 *   // ...
 * }
 * ```
 */

export { useAuth } from '@/contexts/AuthContext';
