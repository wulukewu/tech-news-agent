/**
 * Permission Guard Component
 *
 * Protects system monitor pages by verifying user authentication.
 *
 * Requirements: 5.10
 */

'use client';

import { useAuth } from '@/contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Lock } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useI18n } from '@/contexts/I18nContext';

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
  const { isAuthenticated, loading } = useAuth();
  const { t } = useI18n();

  // Loading state
  if (loading) {
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
            <h1 className="text-3xl font-bold tracking-tight">{t('nav.system-status')}</h1>
            <p className="text-muted-foreground">{t('scheduler.description')}</p>
          </div>

          <Card className="border-destructive">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-destructive">
                <Lock className="h-5 w-5" />
                {t('errors.unauthorized')}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-muted-foreground">{t('system-monitor.auth-required')}</p>
              <Button
                onClick={() => {
                  window.location.href = '/';
                }}
              >
                {t('buttons.login')}
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  // Authenticated - render children
  return <>{children}</>;
}
