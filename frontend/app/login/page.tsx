'use client';

/**
 * Login Page
 *
 * Dedicated login page for authentication.
 * Displays a "Login with Discord" button and handles authentication flow.
 *
 * Features:
 * - Discord OAuth2 login button
 * - Automatic redirect to original path or /app/articles for authenticated users
 * - Responsive design with shadcn/ui components
 * - Discord brand colors and styling
 * - Back to Home link
 *
 * Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7
 */

import { useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { AuthGuard } from '@/components/AuthGuard';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Logo } from '@/components/Logo';
import { ArrowLeft } from 'lucide-react';
import Link from 'next/link';

/**
 * Discord Icon Component
 *
 * SVG icon for Discord logo using official brand colors.
 * Source: Discord Brand Guidelines
 */
function DiscordIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="currentColor"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515a.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0a12.64 12.64 0 0 0-.617-1.25a.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057a19.9 19.9 0 0 0 5.993 3.03a.078.078 0 0 0 .084-.028a14.09 14.09 0 0 0 1.226-1.994a.076.076 0 0 0-.041-.106a13.107 13.107 0 0 1-1.872-.892a.077.077 0 0 1-.008-.128a10.2 10.2 0 0 0 .372-.292a.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127a12.299 12.299 0 0 1-1.873.892a.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028a19.839 19.839 0 0 0 6.002-3.03a.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419c0-1.333.956-2.419 2.157-2.419c1.21 0 2.176 1.096 2.157 2.42c0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419c0-1.333.955-2.419 2.157-2.419c1.21 0 2.176 1.096 2.157 2.42c0 1.333-.946 2.418-2.157 2.418z" />
    </svg>
  );
}

/**
 * Login Page Component
 *
 * Main component for the login page.
 * Handles authentication state and redirects.
 *
 * Requirement 2.1: Login page accessible at /login
 * Requirement 2.4: Redirects authenticated users to /app/articles
 * Requirement 2.5: Redirects to original path after login
 */
export default function LoginPage() {
  return (
    <Suspense fallback={<LoginPageFallback />}>
      <AuthGuard fallback={<LoginPageFallback />}>
        <LoginPageInner />
      </AuthGuard>
    </Suspense>
  );
}

function LoginPageFallback() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
        <p className="mt-4 text-muted-foreground">載入中...</p>
      </div>
    </div>
  );
}

function LoginPageInner() {
  const { isAuthenticated, loading, login } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirect = searchParams.get('redirect') || '/app/articles';

  /**
   * Redirect authenticated users to their intended destination
   *
   * Requirement 2.4: Redirect authenticated users
   * Requirement 2.5: Use redirect query parameter
   */
  useEffect(() => {
    if (!loading && isAuthenticated) {
      router.push(redirect);
    }
  }, [isAuthenticated, loading, redirect, router]);

  /**
   * Handle login button click
   *
   * Redirects to the FastAPI Discord OAuth2 login endpoint.
   * The backend will handle the OAuth2 flow and redirect back
   * to the callback page after successful authentication.
   *
   * Requirement 2.2: Display Discord OAuth login button
   * Requirement 2.5: Pass redirect parameter through OAuth flow
   */
  const handleLogin = () => {
    login(redirect);
  };

  /**
   * Show loading state while checking authentication
   *
   * Requirement 2.6: Display loading indicator
   */
  if (loading) {
    return <LoginPageFallback />;
  }

  /**
   * Don't render login page if user is authenticated
   * (will redirect in useEffect)
   */
  if (isAuthenticated) {
    return null;
  }

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header with Back to Home link - Requirement 2.3 */}
      <header className="border-b">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <Logo size={32} showText />
          <Link href="/">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Home
            </Button>
          </Link>
        </div>
      </header>

      {/* Main login content - Requirement 2.7: Responsive */}
      <main className="flex-1 flex items-center justify-center p-4 bg-gradient-to-br from-background to-muted">
        <Card className="w-full max-w-md shadow-lg">
          <CardHeader className="space-y-1 text-center">
            <div className="flex justify-center mb-4">
              <Logo size={64} />
            </div>
            <CardTitle className="text-3xl font-bold tracking-tight">
              Login to Tech News Agent
            </CardTitle>
            <CardDescription className="text-base">
              Quick login with your Discord account
            </CardDescription>
            <CardDescription className="pt-2">
              Don&apos;t have an account? Sign up instantly with Discord
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Button
              onClick={handleLogin}
              className="w-full h-12 text-base font-semibold bg-[#5865F2] hover:bg-[#4752C4] text-white transition-colors"
              size="lg"
            >
              <DiscordIcon className="mr-2 h-5 w-5" />
              Login with Discord
            </Button>

            <div className="text-center text-sm text-muted-foreground">
              <p>By logging in, you agree to our Terms of Service</p>
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
