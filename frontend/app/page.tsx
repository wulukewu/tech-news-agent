'use client';

/**
 * Login Page
 *
 * The main landing page for unauthenticated users.
 * Displays a "Login with Discord" button and handles authentication flow.
 *
 * Features:
 * - Discord OAuth2 login button
 * - Automatic redirect to dashboard for authenticated users
 * - Responsive design with shadcn/ui components
 * - Discord brand colors and styling
 *
 * Requirements:
 * - 3.1: Provides login page at root path "/"
 * - 3.2: Displays "Login with Discord" button
 * - 3.3: Uses Discord brand colors and icon
 * - 3.4: Redirects to FastAPI login endpoint on button click
 * - 3.5: Displays application name and description
 * - 3.6: Responsive design for mobile devices
 * - 3.7: Redirects authenticated users to dashboard
 */

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';

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
 */
export default function LoginPage() {
  const { isAuthenticated, loading, login } = useAuth();
  const router = useRouter();

  /**
   * Redirect authenticated users to dashboard
   *
   * If the user is already logged in, automatically redirect
   * them to the dashboard page instead of showing the login page.
   *
   * Requirement 3.7: Redirect authenticated users
   */
  useEffect(() => {
    if (!loading && isAuthenticated) {
      router.push('/dashboard');
    }
  }, [isAuthenticated, loading, router]);

  /**
   * Handle login button click
   *
   * Redirects to the FastAPI Discord OAuth2 login endpoint.
   * The backend will handle the OAuth2 flow and redirect back
   * to the callback page after successful authentication.
   *
   * Requirement 3.4: Redirect to FastAPI login endpoint
   */
  const handleLogin = () => {
    login();
  };

  /**
   * Show loading state while checking authentication
   *
   * Prevents flash of login page for authenticated users
   */
  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">載入中...</p>
        </div>
      </div>
    );
  }

  /**
   * Don't render login page if user is authenticated
   * (will redirect in useEffect)
   */
  if (isAuthenticated) {
    return null;
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-background to-muted p-4">
      <Card className="w-full max-w-md shadow-lg">
        <CardHeader className="space-y-1 text-center">
          <CardTitle className="text-3xl font-bold tracking-tight">
            Tech News Agent
          </CardTitle>
          <CardDescription className="text-base">
            技術資訊訂閱與管理平台
          </CardDescription>
          <CardDescription className="pt-2">
            使用 Discord 帳號登入以管理您的技術資訊訂閱
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
            <p>點擊登入即表示您同意我們的服務條款</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
