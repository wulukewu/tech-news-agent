'use client';

/**
 * Protected Route Component
 *
 * This component wraps pages that require authentication.
 * It checks if the user is authenticated and redirects to the login page if not.
 *
 * Features:
 * - Checks authentication status before rendering protected content
 * - Redirects unauthenticated users to the login page
 * - Preserves the intended destination URL for post-login redirect
 * - Displays a loading indicator while checking authentication
 *
 * Requirements Coverage:
 * - Requirement 6.1: Implements ProtectedRoute component
 * - Requirement 6.2: Checks if user is authenticated before rendering
 * - Requirement 6.3: Redirects to login page when not authenticated
 * - Requirement 6.4: Preserves intended destination URL
 * - Requirement 6.5: Displays loading indicator during auth check
 * - Requirement 6.6: Protects dashboard, subscriptions, articles, reading-list routes
 * - Requirement 6.7: Login and callback pages accessible without authentication
 *
 * Usage:
 * ```tsx
 * // In a protected page
 * export default function DashboardPage() {
 *   return (
 *     <ProtectedRoute>
 *       <div>Protected content here</div>
 *     </ProtectedRoute>
 *   );
 * }
 * ```
 */

import { useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';

/**
 * Loading Screen Component
 *
 * Displays a centered loading spinner while authentication is being checked.
 * This provides visual feedback to users during the authentication process.
 */
function LoadingScreen() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="flex flex-col items-center gap-4">
        <div className="h-12 w-12 animate-spin rounded-full border-4 border-gray-300 border-t-blue-600"></div>
        <p className="text-sm text-gray-600">正在驗證身份...</p>
      </div>
    </div>
  );
}

/**
 * ProtectedRoute Component Props
 *
 * @property children - The protected content to render when authenticated
 */
interface ProtectedRouteProps {
  children: React.ReactNode;
}

/**
 * ProtectedRoute Component
 *
 * Wraps protected pages and handles authentication checks.
 *
 * Behavior:
 * 1. While loading: Shows LoadingScreen
 * 2. If not authenticated: Saves current path and redirects to login
 * 3. If authenticated: Renders the protected content
 *
 * The component saves the current pathname to sessionStorage before redirecting,
 * allowing the application to redirect back to the intended page after login.
 *
 * @param props - Component props
 * @param props.children - Protected content to render
 * @returns Protected content or loading/redirect state
 */
export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { isAuthenticated, loading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    // Only redirect if we're done loading and user is not authenticated
    if (!loading && !isAuthenticated) {
      // Save the intended destination URL for post-login redirect
      // This allows users to be redirected back to where they wanted to go
      sessionStorage.setItem('redirectAfterLogin', pathname);

      // Redirect to login page
      router.push('/');
    }
  }, [isAuthenticated, loading, pathname, router]);

  // Show loading screen while checking authentication status
  if (loading) {
    return <LoadingScreen />;
  }

  // Don't render anything while redirecting to login
  // This prevents a flash of protected content before redirect
  if (!isAuthenticated) {
    return null;
  }

  // User is authenticated, render the protected content
  return <>{children}</>;
}
