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
import { useI18n } from '@/contexts/I18nContext';

export interface SchedulerStatusWidgetProps {
  /** Scheduler status data */
  status: SchedulerStatus;
  /** Whether manual trigger is in progress */
  isTriggering?: boolean;
  /** Callback when user triggers manual fetch */
  onTrigger?: () => void;
}

export function SchedulerStatusWidget({
  status,
  isTriggering = false,
  onTrigger,
}: SchedulerStatusWidgetProps) {
  const { t } = useI18n();

  /**
   * Format date to relative time string in Chinese
   */
  function formatRelativeTime(date: Date | null): string {
    if (!date) return t('ui.unknown');

    try {
      return formatDistanceToNow(date, {
        addSuffix: true,
        locale: zhTW,
      });
    } catch {
      return t('ui.unknown');
    }
  }

  /**
   * Get status badge variant based on health
   */
  function getStatusBadge(isHealthy: boolean, isRunning: boolean) {
    if (isRunning) {
      return { variant: 'default' as const, text: t('scheduler.running'), icon: RefreshCw };
    }
    if (isHealthy) {
      return { variant: 'default' as const, text: t('ui.healthy'), icon: CheckCircle };
    }
    return { variant: 'destructive' as const, text: t('scheduler.abnormal'), icon: AlertCircle };
  }

  const statusBadge = getStatusBadge(status.isHealthy, status.isRunning);
  const StatusIcon = statusBadge.icon;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <CardTitle className="text-xl">{t('scheduler.status')}</CardTitle>
            <CardDescription>{t('scheduler.description')}</CardDescription>
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
              <span>{t('scheduler.last-execution')}</span>
            </div>
            <div className="text-sm font-medium">
              {status.lastExecutionTime ? (
                <>
                  {formatRelativeTime(status.lastExecutionTime)}
                  {status.articlesProcessed > 0 && (
                    <span className="ml-2 text-muted-foreground">
                      ({t('scheduler.articles-processed', { count: status.articlesProcessed })})
                    </span>
                  )}
                </>
              ) : (
                <span className="text-muted-foreground">{t('scheduler.not-executed')}</span>
              )}
            </div>
          </div>

          {/* Next Execution */}
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Clock className="h-4 w-4" />
              <span>{t('scheduler.next-scheduled')}</span>
            </div>
            <div className="text-sm font-medium">
              {status.nextExecutionTime ? (
                formatRelativeTime(status.nextExecutionTime)
              ) : (
                <span className="text-muted-foreground">{t('scheduler.calculating')}</span>
              )}
            </div>
          </div>
        </div>

        {/* Execution Statistics */}
        {status.totalOperations > 0 && (
          <div className="rounded-lg bg-muted/50 p-3 space-y-2">
            <div className="text-sm font-medium">{t('scheduler.execution-stats')}</div>
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div>
                <div className="text-muted-foreground">{t('scheduler.total-operations')}</div>
                <div className="font-medium">{status.totalOperations}</div>
              </div>
              <div>
                <div className="text-muted-foreground">{t('scheduler.success')}</div>
                <div className="font-medium text-green-600 dark:text-green-400">
                  {status.totalOperations - status.failedOperations}
                </div>
              </div>
              <div>
                <div className="text-muted-foreground">{t('scheduler.failed')}</div>
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
              <span>{t('scheduler.health-issues')}</span>
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
                {t('scheduler.triggering')}
              </>
            ) : (
              <>
                <PlayCircle className="h-4 w-4" />
                {t('scheduler.manual-trigger')}
              </>
            )}
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
