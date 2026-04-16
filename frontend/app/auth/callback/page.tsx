'use client';

/**
 * OAuth Callback Page
 *
 * Handles the OAuth2 callback from Discord after user authorization.
 * This page is responsible for:
 * - Processing the OAuth callback
 * - Updating authentication state
 * - Redirecting to dashboard on success
 * - Displaying errors on failure
 *
 * Flow:
 * 1. Discord redirects here with authorization code (or error)
 * 2. FastAPI backend has already processed the code and set HttpOnly cookie
 * 3. Frontend calls checkAuth to update authentication state
 * 4. Redirect to dashboard on success, or show error on failure
 *
 * Requirements:
 * - 4.1: Provides callback page at "/auth/callback"
 * - 4.2: Extracts JWT Token from response (via checkAuth)
 * - 4.3: Stores user information in global state
 * - 4.4: Redirects to dashboard after successful authentication
 * - 4.5: Displays error message on authentication failure
 * - 4.6: Handles user denial of authorization
 * - 4.7: Displays loading indicator during processing
 */

import { useEffect, useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { setToken } from '@/lib/api/auth';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

/**
 * Loading Spinner Component
 *
 * Displays an animated spinner during authentication processing.
 */
function LoadingSpinner() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-background to-muted">
      <div className="text-center space-y-4">
        <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-primary mx-auto"></div>
        <div className="space-y-2">
          <p className="text-xl font-semibold">正在驗證身份...</p>
          <p className="text-sm text-muted-foreground">請稍候，即將完成登入</p>
        </div>
      </div>
    </div>
  );
}

/**
 * Error Display Component
 *
 * Displays authentication error with retry option.
 *
 * @param error - Error message to display
 * @param onRetry - Callback function for retry button
 */
function ErrorDisplay({ error, onRetry }: { error: string; onRetry: () => void }) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-background to-muted p-4">
      <Card className="w-full max-w-md shadow-lg border-destructive">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-bold text-destructive">驗證失敗</CardTitle>
          <CardDescription>Authentication Error</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="rounded-lg bg-destructive/10 p-4 border border-destructive/20">
            <p className="text-sm text-destructive font-medium">{error}</p>
          </div>

          <div className="space-y-2">
            <Button onClick={onRetry} className="w-full" size="lg">
              返回登入頁面
            </Button>
            <p className="text-xs text-center text-muted-foreground">
              如果問題持續發生，請聯絡技術支援
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

/**
 * OAuth Callback Page Component (Inner)
 *
 * Main component for handling OAuth2 callback.
 * Processes authentication and redirects accordingly.
 * This component uses useSearchParams and must be wrapped in Suspense.
 */
function CallbackPageInner() {
  const { checkAuth } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const [error, setError] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(true);

  /**
   * Handle OAuth callback processing
   *
   * This effect runs once on component mount to:
   * 1. Check for error parameters (user denied or OAuth error)
   * 2. Call checkAuth to verify JWT token and update state
   * 3. Redirect to dashboard on success
   * 4. Display error message on failure
   *
   * Requirements:
   * - 4.2: Extract JWT Token (via checkAuth)
   * - 4.3: Store user information in global state
   * - 4.4: Redirect to dashboard on success
   * - 4.5: Display error on failure
   * - 4.6: Handle user denial
   */
  useEffect(() => {
    const handleCallback = async () => {
      try {
        // Check for OAuth error parameters
        // Requirement 4.6: Handle user denial of authorization
        const errorParam = searchParams.get('error');
        const errorDescription = searchParams.get('error_description');

        if (errorParam) {
          // User denied authorization or OAuth error occurred
          let errorMessage = '驗證失敗，請重試。';

          if (errorParam === 'access_denied') {
            errorMessage = '您拒絕了授權請求。若要使用本服務，請授權 Discord 登入。';
          } else if (errorDescription) {
            errorMessage = `驗證錯誤：${errorDescription}`;
          }

          setError(errorMessage);
          setIsProcessing(false);
          return;
        }

        // Extract token from URL parameter
        const token = searchParams.get('token');

        if (!token) {
          setError('驗證失敗：未收到認證令牌。');
          setIsProcessing(false);
          return;
        }

        console.log('Received token from URL:', token.substring(0, 20) + '...');

        // Store token in localStorage
        setToken(token);
        console.log('Token stored in localStorage');

        // Verify token was stored
        const storedToken = localStorage.getItem('auth_token');
        console.log(
          'Verified stored token:',
          storedToken ? storedToken.substring(0, 20) + '...' : 'none'
        );

        // Verify the token and update frontend state
        // Requirement 4.2 & 4.3: Extract token and store user info
        await checkAuth();
        console.log('checkAuth successful');

        // Requirement 4.4: Redirect to dashboard on success
        router.push('/dashboard');
      } catch (err) {
        // Requirement 4.5: Display error message on failure
        console.error('Authentication callback error:', {
          timestamp: new Date().toISOString(),
          error: err,
          url: window.location.href,
        });

        setError('無法完成身份驗證。請確認您的網路連線正常，然後重試。');
        setIsProcessing(false);
      }
    };

    handleCallback();
  }, [checkAuth, router, searchParams]);

  /**
   * Handle retry button click
   *
   * Redirects user back to login page to retry authentication.
   */
  const handleRetry = () => {
    router.push('/');
  };

  // Requirement 4.7: Display loading indicator
  if (isProcessing && !error) {
    return <LoadingSpinner />;
  }

  // Display error if authentication failed
  if (error) {
    return <ErrorDisplay error={error} onRetry={handleRetry} />;
  }

  // This state should not be reached, but provide fallback
  return <LoadingSpinner />;
}

/**
 * OAuth Callback Page Component (Wrapper)
 *
 * Wraps the inner component with Suspense boundary as required by Next.js
 * when using useSearchParams().
 */
export default function CallbackPage() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <CallbackPageInner />
    </Suspense>
  );
}
