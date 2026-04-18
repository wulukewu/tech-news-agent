'use client';

/**
 * App Layout with Route Protection
 *
 * Layout component for all authenticated routes under /app/*.
 * Provides route protection, loading states, error handling, and shared layout structure.
 *
 * Features:
 * - Authentication check before rendering
 * - Redirect to /login with return URL for unauthenticated users
 * - Loading screen while checking authentication
 * - Graceful error handling for authentication failures
 * - Shared navigation and layout for all app pages
 *
 * Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6
 */

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { AuthGuard } from '@/components/AuthGuard';
import { Button } from '@/components/ui/button';
import { AlertCircle, RefreshCw } from 'lucide-react';

/**
 * Loading Screen Component
 *
 * Displayed while checking authentication status.
 * Requirement 13.3: Implement loading screen
 */
function LoadingScreen() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
        <p className="mt-4 text-muted-foreground">Checking authentication...</p>
      </div>
    </div>
  );
}

/**
 * Error Screen Component
 *
 * Displayed when authentication check fails.
 * Requirement 13.4: Handle authentication errors gracefully
 */
function ErrorScreen({ onRetry }: { onRetry: () => void }) {
  const router = useRouter();

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <div className="text-center max-w-md">
        <div className="flex justify-center mb-4">
          <div className="rounded-full bg-destructive/10 p-3">
            <AlertCircle className="h-8 w-8 text-destructive" />
          </div>
        </div>
        <h1 className="text-2xl font-bold mb-2">Authentication Error</h1>
        <p className="text-muted-foreground mb-6">
          We encountered an error while checking your authentication status. This could be due to a
          network issue or an expired session.
        </p>
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Button onClick={onRetry} variant="default" className="gap-2">
            <RefreshCw className="h-4 w-4" />
            Try Again
          </Button>
          <Button onClick={() => router.push('/login')} variant="outline">
            Go to Login
          </Button>
        </div>
      </div>
    </div>
  );
}

/**
 * App Layout Component
 *
 * Protects all routes under /app/* and provides shared layout.
 *
 * Requirement 13.1: Check authentication before rendering
 * Requirement 13.2: Redirect unauthenticated users to /login
 * Requirement 13.4: Handle authentication errors gracefully
 * Requirement 13.5: Don't render protected content until auth confirmed
 */
export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGuard fallback={<LoadingScreen />}>
      <AppLayoutInner>{children}</AppLayoutInner>
    </AuthGuard>
  );
}

/**
 * Inner App Layout Component
 *
 * Contains the actual layout logic that uses useAuth.
 * This is wrapped by AuthGuard to ensure context is available.
 */
function AppLayoutInner({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, loading, checkAuth } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [authError, setAuthError] = useState(false);
  const [, setRetryCount] = useState(0);

  /**
   * Handle authentication check with error handling
   *
   * Requirement 13.4: Handle authentication errors gracefully
   */
  useEffect(() => {
    const handleAuthCheck = async () => {
      // Skip if already authenticated or still loading
      if (isAuthenticated || loading) {
        setAuthError(false);
        return;
      }

      // If not authenticated and not loading, redirect to login
      if (!loading && !isAuthenticated) {
        // Small delay to prevent flash of error screen
        const timer = setTimeout(() => {
          router.push(`/login?redirect=${encodeURIComponent(pathname)}`);
        }, 100);

        return () => clearTimeout(timer);
      }
    };

    handleAuthCheck();
  }, [isAuthenticated, loading, pathname, router]);

  /**
   * Listen for authentication errors
   *
   * Requirement 13.4: Handle authentication errors gracefully
   */
  useEffect(() => {
    const handleAuthError = () => {
      setAuthError(true);
    };

    window.addEventListener('auth-error', handleAuthError);

    return () => {
      window.removeEventListener('auth-error', handleAuthError);
    };
  }, []);

  /**
   * Retry authentication check
   *
   * Requirement 13.4: Handle authentication errors gracefully
   */
  const handleRetry = async () => {
    setAuthError(false);
    setRetryCount((prev) => prev + 1);
    try {
      await checkAuth();
    } catch (error) {
      // Auth retry failed
      setAuthError(true);
    }
  };

  /**
   * Show error screen if authentication check failed
   *
   * Requirement 13.4: Handle authentication errors gracefully
   */
  if (authError) {
    return <ErrorScreen onRetry={handleRetry} />;
  }

  /**
   * Show loading screen while checking auth
   *
   * Requirement 13.3: Display loading screen
   */
  if (loading) {
    return <LoadingScreen />;
  }

  /**
   * Don't render if not authenticated (will redirect)
   *
   * Requirement 13.5: Don't render protected content
   */
  if (!isAuthenticated) {
    return null;
  }

  /**
   * Render protected content with shared layout
   *
   * Note: Navigation will be added in Phase 3
   * For now, just render children with basic container
   */
  return (
    <div className="min-h-screen bg-background">
      {/* TODO: Add AppNavigation component in Phase 3 */}
      <main id="main-content" className="container mx-auto px-4 py-6">
        {children}
      </main>
    </div>
  );
}
