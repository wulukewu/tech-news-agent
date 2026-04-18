'use client';

/**
 * ConditionalLayout Component
 *
 * Conditionally renders Navigation, AppLayout, and Auth protection based on the current route.
 * - Landing page (/): No navigation, no layout, no auth
 * - Login page (/login): No navigation, no layout, no auth
 * - Auth callback (/auth/callback): No navigation, no layout, no auth
 * - App pages (/app/*): Navigation + AppLayout + Auth protection
 */

import { usePathname, useRouter } from 'next/navigation';
import { useEffect } from 'react';
import { Navigation } from '@/components/Navigation';
import { AppLayout } from '@/components/layout';
import { useAuth } from '@/contexts/AuthContext';
import { useNotFound } from '@/contexts/NotFoundContext';

interface ConditionalLayoutProps {
  children: React.ReactNode;
}

/**
 * Loading Screen Component
 */
function LoadingScreen() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
        <p className="mt-4 text-muted-foreground">Loading...</p>
      </div>
    </div>
  );
}

export function ConditionalLayout({ children }: ConditionalLayoutProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { isAuthenticated, loading } = useAuth();
  const { isNotFound } = useNotFound();

  // Routes that should NOT have navigation/layout/auth
  const publicRoutes = ['/', '/login', '/auth/callback'];
  const isPublicRoute = publicRoutes.includes(pathname);

  // Check if this is a protected route (app, recommendations, etc.)
  // Note: 404 pages should not be treated as protected routes
  const isProtectedRoute = !isPublicRoute && !isNotFound && pathname.startsWith('/app');

  // Handle auth redirect for protected routes
  useEffect(() => {
    if (isProtectedRoute && !loading && !isAuthenticated) {
      router.push(`/login?redirect=${encodeURIComponent(pathname)}`);
    }
  }, [isProtectedRoute, loading, isAuthenticated, pathname, router]);

  // If it's a public route, render children without layout
  if (isPublicRoute) {
    return <>{children}</>;
  }

  // If it's not a protected route (e.g., 404 page), render without layout
  if (!isProtectedRoute) {
    return <>{children}</>;
  }

  // For protected routes, show loading while checking auth
  if (loading) {
    return <LoadingScreen />;
  }

  // Don't render protected content if not authenticated (will redirect)
  if (!isAuthenticated) {
    return null;
  }

  // For authenticated users on protected routes, render with navigation and layout
  return <AppLayout header={<Navigation />}>{children}</AppLayout>;
}
