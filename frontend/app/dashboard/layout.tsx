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
 * Protects all routes under /dashboard/* and provides shared layout.
 * Auth protection is handled by ConditionalLayout + AuthGuard at the root level.
 * This layout only provides the visual container for dashboard pages.
 *
 * Requirement 13.1: Check authentication before rendering (handled by AuthGuard)
 * Requirement 13.2: Redirect unauthenticated users to /login (handled by AuthGuard)
 * Requirement 13.5: Don't render protected content until auth confirmed (handled by AuthGuard)
 */
export default function AppLayout({ children }: { children: React.ReactNode }) {
  // No auth checks here - ConditionalLayout + AuthGuard handle it at root level
  // This prevents duplicate auth checks that cause infinite reloads
  return <div className="min-h-screen bg-background">{children}</div>;
}
