/**
 * Scheduler Status Widget
 *
 * Displays scheduler execution status, timing information, and manual trigger option.
 *
 * Requirements: 5.1, 5.2, 5.3
 */

'use client';

import { Clock, RefreshCw, CheckCircle, AlertCircle, PlayCircle } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { formatDistanceToNow } from 'date-fns';
import { zhTW } from 'date-fns/locale';
import type { SchedulerStatus } from '../types';

export interface SchedulerStatusWidgetProps {
  /** Scheduler status data */
  status: SchedulerStatus;
  /** Whether manual trigger is in progress */
  isTriggering?: boolean;
  /** Callback when user triggers manual fetch */
  onTrigger?: () => void;
}

/**
 * Format date to relative time string in Chinese
 */
function formatRelativeTime(date: Date | null): string {
  if (!date) return '未知';

  try {
    return formatDistanceToNow(date, {
      addSuffix: true,
      locale: zhTW,
    });
  } catch {
    return '未知';
  }
}

/**
 * Get status badge variant based on health
 */
function getStatusBadge(isHealthy: boolean, isRunning: boolean) {
  if (isRunning) {
    return { variant: 'default' as const, text: '執行中', icon: RefreshCw };
  }
  if (isHealthy) {
    return { variant: 'default' as const, text: '正常', icon: CheckCircle };
  }
  return { variant: 'destructive' as const, text: '異常', icon: AlertCircle };
}

/**
 * SchedulerStatusWidget Component
 *
 * Displays scheduler execution status with:
 * - Current running status
 * - Last execution time and article count
 * - Next scheduled execution time
 * - Health status and issues
 * - Manual trigger button
 *
 * @example
 * ```tsx
 * <SchedulerStatusWidget
 *   status={schedulerStatus}
 *   isTriggering={false}
 *   onTrigger={handleTrigger}
 * />
 * ```
 */
export function SchedulerStatusWidget({
  status,
  isTriggering = false,
  onTrigger,
}: SchedulerStatusWidgetProps) {
  const statusBadge = getStatusBadge(status.isHealthy, status.isRunning);
  const StatusIcon = statusBadge.icon;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <CardTitle className="text-xl">排程器狀態</CardTitle>
            <CardDescription>背景任務執行狀況和下次執行時間</CardDescription>
          </div>
          <Badge variant={statusBadge.variant} className="gap-1.5">
            <StatusIcon className={`h-3.5 w-3.5 ${status.isRunning ? 'animate-spin' : ''}`} />
            {statusBadge.text}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Execution Information */}
        <div className="grid gap-4 sm:grid-cols-2">
          {/* Last Execution */}
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <CheckCircle className="h-4 w-4" />
              <span>上次執行</span>
            </div>
            <div className="text-sm font-medium">
              {status.lastExecutionTime ? (
                <>
                  {formatRelativeTime(status.lastExecutionTime)}
                  {status.articlesProcessed > 0 && (
                    <span className="ml-2 text-muted-foreground">
                      ({status.articlesProcessed} 篇文章)
                    </span>
                  )}
                </>
              ) : (
                <span className="text-muted-foreground">尚未執行</span>
              )}
            </div>
          </div>

          {/* Next Execution */}
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Clock className="h-4 w-4" />
              <span>下次排程</span>
            </div>
            <div className="text-sm font-medium">
              {status.nextExecutionTime ? (
                formatRelativeTime(status.nextExecutionTime)
              ) : (
                <span className="text-muted-foreground">計算中...</span>
              )}
            </div>
          </div>
        </div>

        {/* Execution Statistics */}
        {status.totalOperations > 0 && (
          <div className="rounded-lg bg-muted/50 p-3 space-y-2">
            <div className="text-sm font-medium">執行統計</div>
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div>
                <div className="text-muted-foreground">總操作</div>
                <div className="font-medium">{status.totalOperations}</div>
              </div>
              <div>
                <div className="text-muted-foreground">成功</div>
                <div className="font-medium text-green-600 dark:text-green-400">
                  {status.totalOperations - status.failedOperations}
                </div>
              </div>
              <div>
                <div className="text-muted-foreground">失敗</div>
                <div className="font-medium text-red-600 dark:text-red-400">
                  {status.failedOperations}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Health Issues */}
        {status.issues && status.issues.length > 0 && (
          <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-3 space-y-2">
            <div className="flex items-center gap-2 text-sm font-medium text-destructive">
              <AlertCircle className="h-4 w-4" />
              <span>健康度問題</span>
            </div>
            <ul className="space-y-1 text-sm text-muted-foreground">
              {status.issues.map((issue, index) => (
                <li key={index} className="flex items-start gap-2">
                  <span className="mt-1">•</span>
                  <span>{issue}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Manual Trigger Button */}
        {onTrigger && (
          <Button
            onClick={onTrigger}
            disabled={status.isRunning || isTriggering}
            className="w-full gap-2"
            variant="outline"
          >
            {isTriggering ? (
              <>
                <RefreshCw className="h-4 w-4 animate-spin" />
                觸發中...
              </>
            ) : (
              <>
                <PlayCircle className="h-4 w-4" />
                手動觸發抓取
              </>
            )}
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
