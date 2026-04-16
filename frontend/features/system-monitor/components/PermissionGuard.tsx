/**
 * Permission Guard Component
 *
 * Protects system monitor pages by verifying user authentication.
 *
 * Requirements: 5.10
 */

'use client';

import { useAuth } from '@/lib/auth/useAuth';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle, Lock } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface PermissionGuardProps {
  children: React.ReactNode;
}

/**
 * Permission Guard Component
 *
 * Verifies user authentication before allowing access to system monitor.
 * Shows loading state while checking authentication.
 * Shows error message if user is not authenticated.
 *
 * Requirements: 5.10
 */
export function PermissionGuard({ children }: PermissionGuardProps) {
  const { isAuthenticated, isLoading, error } = useAuth();

  // Loading state
  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-6 max-w-7xl">
        <div className="space-y-6">
          <div>
            <Skeleton className="h-10 w-64 mb-2" />
            <Skeleton className="h-5 w-96" />
          </div>
          <Card>
            <CardContent className="pt-6">
              <div className="space-y-4">
                <Skeleton className="h-20 w-full" />
                <Skeleton className="h-20 w-full" />
                <Skeleton className="h-20 w-full" />
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  // Not authenticated
  if (!isAuthenticated) {
    return (
      <div className="container mx-auto px-4 py-6 max-w-7xl">
        <div className="space-y-6">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">系統狀態</h1>
            <p className="text-muted-foreground">監控系統健康度和排程器執行狀況</p>
          </div>

          <Card className="border-destructive">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-destructive">
                <Lock className="h-5 w-5" />
                需要登入
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-muted-foreground">
                系統監控功能僅限已登入的使用者存取。請先登入以查看系統狀態。
              </p>
              <Button
                onClick={() => {
                  window.location.href = '/';
                }}
              >
                前往登入
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="container mx-auto px-4 py-6 max-w-7xl">
        <div className="space-y-6">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">系統狀態</h1>
            <p className="text-muted-foreground">監控系統健康度和排程器執行狀況</p>
          </div>

          <Card className="border-destructive">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-destructive">
                <AlertCircle className="h-5 w-5" />
                驗證失敗
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">無法驗證您的身份。請重新整理頁面或重新登入。</p>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  // Authenticated - render children
  return <>{children}</>;
}
