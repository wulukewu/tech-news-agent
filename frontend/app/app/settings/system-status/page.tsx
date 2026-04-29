'use client';

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle, RefreshCw, CheckCircle, XCircle, Clock } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';
import { toast } from '@/lib/toast';
import { useI18n } from '@/contexts/I18nContext';

interface SchedulerStatusResponse {
  last_execution_time: string | null;
  articles_processed: number;
  failed_operations: number;
  total_operations: number;
  is_healthy: boolean;
  is_enabled: boolean;
  issues: string[];
}

async function getSchedulerStatus(): Promise<SchedulerStatusResponse> {
  const response = await apiClient.get<{ success: boolean; data: SchedulerStatusResponse }>(
    '/api/scheduler/status'
  );
  return response.data.data;
}

async function triggerManualFetch(): Promise<{ status: string; message: string }> {
  const response = await apiClient.post<{ status: string; message: string }>(
    '/api/scheduler/trigger',
    {}
  );
  return response.data;
}

export default function SystemStatusSettingsPage() {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const [showConfirm, setShowConfirm] = useState(false);

  const {
    data: status,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['scheduler-status'],
    queryFn: getSchedulerStatus,
    refetchInterval: 30000,
  });

  const triggerMutation = useMutation({
    mutationFn: triggerManualFetch,
    onSuccess: () => {
      toast.success(t('pages.system-status.triggering'));
      queryClient.invalidateQueries({ queryKey: ['scheduler-status'] });
      setShowConfirm(false);
    },
    onError: () => {
      toast.error(t('errors.server-error'));
      setShowConfirm(false);
    },
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{t('pages.system-status.title')}</h1>
          <p className="text-muted-foreground text-sm">{t('pages.system-status.description')}</p>
        </div>
        <Button variant="outline" size="sm" onClick={() => refetch()} disabled={isLoading}>
          <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
          {t('pages.system-status.refresh')}
        </Button>
      </div>

      {isLoading ? (
        <Card>
          <CardContent className="pt-6">
            <Skeleton className="h-20 w-full" />
          </CardContent>
        </Card>
      ) : error ? (
        <Card className="border-destructive">
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-destructive">
              <AlertCircle className="h-5 w-5" />
              <p>{t('pages.system-status.load-error')}</p>
            </div>
          </CardContent>
        </Card>
      ) : status ? (
        <div className="grid gap-4 md:grid-cols-2">
          {/* Scheduler Status */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                {!status.is_enabled ? (
                  <>
                    <AlertCircle className="h-5 w-5 text-yellow-500" />
                    {t('pages.system-status.scheduler-disabled')}
                  </>
                ) : status.is_healthy ? (
                  <>
                    <CheckCircle className="h-5 w-5 text-green-500" />
                    {t('pages.system-status.scheduler-status')}
                  </>
                ) : (
                  <>
                    <XCircle className="h-5 w-5 text-red-500" />
                    {t('pages.system-status.scheduler-status')}
                  </>
                )}
              </CardTitle>
              <CardDescription>
                {!status.is_enabled
                  ? t('pages.system-status.scheduler-disabled-desc')
                  : status.is_healthy
                    ? t('pages.system-status.scheduler-healthy')
                    : t('pages.system-status.scheduler-unhealthy')}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-muted-foreground">
                    {t('pages.system-status.articles-processed')}
                  </p>
                  <p className="font-medium">{status.articles_processed}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">{t('pages.system-status.success-rate')}</p>
                  <p className="font-medium">
                    {status.total_operations > 0
                      ? Math.round(
                          ((status.total_operations - status.failed_operations) /
                            status.total_operations) *
                            100
                        )
                      : 0}
                    %
                  </p>
                </div>
              </div>

              {status.last_execution_time && (
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Clock className="h-4 w-4" />
                  {t('pages.system-status.last-execution')}：
                  {new Date(status.last_execution_time).toLocaleString()}
                </div>
              )}

              {status.issues.length > 0 && (
                <div className="space-y-1">
                  <p className="text-sm font-medium text-muted-foreground">
                    {t('pages.system-status.status-label')}：
                  </p>
                  {status.issues.map((issue, i) => (
                    <p key={i} className="text-xs text-muted-foreground">
                      • {issue}
                    </p>
                  ))}
                </div>
              )}

              <div className="pt-2">
                {!status.is_enabled ? (
                  <p className="text-xs text-muted-foreground">
                    {t('pages.system-status.scheduler-disabled-note')}
                  </p>
                ) : showConfirm ? (
                  <div className="space-y-2">
                    <p className="text-sm text-muted-foreground">
                      {t('pages.system-status.confirm-trigger')}
                    </p>
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        onClick={() => triggerMutation.mutate()}
                        disabled={triggerMutation.isPending}
                      >
                        {triggerMutation.isPending
                          ? t('pages.system-status.triggering')
                          : t('pages.system-status.confirm')}
                      </Button>
                      <Button size="sm" variant="outline" onClick={() => setShowConfirm(false)}>
                        {t('pages.system-status.cancel')}
                      </Button>
                    </div>
                  </div>
                ) : (
                  <Button size="sm" onClick={() => setShowConfirm(true)}>
                    {t('pages.system-status.manual-trigger')}
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>

          {/* System Info */}
          <Card>
            <CardHeader>
              <CardTitle>{t('pages.system-status.system-info')}</CardTitle>
              <CardDescription>{t('pages.system-status.system-info-desc')}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-muted-foreground">{t('pages.system-status.database')}</p>
                  <div className="flex items-center gap-1">
                    <CheckCircle className="h-3 w-3 text-green-500" />
                    <span className="font-medium">{t('pages.system-status.healthy')}</span>
                  </div>
                </div>
                <div>
                  <p className="text-muted-foreground">{t('pages.system-status.api')}</p>
                  <div className="flex items-center gap-1">
                    <CheckCircle className="h-3 w-3 text-green-500" />
                    <span className="font-medium">{t('pages.system-status.healthy')}</span>
                  </div>
                </div>
              </div>
              <div className="text-xs text-muted-foreground">
                {t('pages.system-status.auto-refresh')}
              </div>
            </CardContent>
          </Card>
        </div>
      ) : null}
    </div>
  );
}
