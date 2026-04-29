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
      toast.success('手動抓取已觸發');
      queryClient.invalidateQueries({ queryKey: ['scheduler-status'] });
      setShowConfirm(false);
    },
    onError: () => {
      toast.error('觸發失敗');
      setShowConfirm(false);
    },
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{t('nav.system-status')}</h1>
          <p className="text-muted-foreground text-sm">查看系統健康狀態和排程器狀況</p>
        </div>
        <Button variant="outline" size="sm" onClick={() => refetch()} disabled={isLoading}>
          <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
          重新整理
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
              <p>無法載入系統狀態</p>
            </div>
          </CardContent>
        </Card>
      ) : status ? (
        <div className="grid gap-4 md:grid-cols-2">
          {/* Scheduler Status */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                {status.is_healthy ? (
                  <CheckCircle className="h-5 w-5 text-green-500" />
                ) : (
                  <XCircle className="h-5 w-5 text-red-500" />
                )}
                排程器狀態
              </CardTitle>
              <CardDescription>{status.is_healthy ? '運行正常' : '發現問題'}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-muted-foreground">處理文章數</p>
                  <p className="font-medium">{status.articles_processed}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">成功率</p>
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
                  上次執行：{new Date(status.last_execution_time).toLocaleString('zh-TW')}
                </div>
              )}

              {status.issues.length > 0 && (
                <div className="space-y-1">
                  <p className="text-sm font-medium text-destructive">問題：</p>
                  {status.issues.map((issue, i) => (
                    <p key={i} className="text-xs text-muted-foreground">
                      • {issue}
                    </p>
                  ))}
                </div>
              )}

              <div className="pt-2">
                {showConfirm ? (
                  <div className="space-y-2">
                    <p className="text-sm text-muted-foreground">確定要手動觸發抓取嗎？</p>
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        onClick={() => triggerMutation.mutate()}
                        disabled={triggerMutation.isPending}
                      >
                        {triggerMutation.isPending ? '觸發中...' : '確定'}
                      </Button>
                      <Button size="sm" variant="outline" onClick={() => setShowConfirm(false)}>
                        取消
                      </Button>
                    </div>
                  </div>
                ) : (
                  <Button size="sm" onClick={() => setShowConfirm(true)}>
                    手動觸發抓取
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>

          {/* System Info */}
          <Card>
            <CardHeader>
              <CardTitle>系統資訊</CardTitle>
              <CardDescription>基本系統狀態</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-muted-foreground">資料庫</p>
                  <div className="flex items-center gap-1">
                    <CheckCircle className="h-3 w-3 text-green-500" />
                    <span className="font-medium">正常</span>
                  </div>
                </div>
                <div>
                  <p className="text-muted-foreground">API</p>
                  <div className="flex items-center gap-1">
                    <CheckCircle className="h-3 w-3 text-green-500" />
                    <span className="font-medium">正常</span>
                  </div>
                </div>
              </div>
              <div className="text-xs text-muted-foreground">自動更新間隔：30 秒</div>
            </CardContent>
          </Card>
        </div>
      ) : null}
    </div>
  );
}
