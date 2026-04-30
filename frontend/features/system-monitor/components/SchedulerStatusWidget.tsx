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
    <Card className="animate-in fade-in slide-in-from-bottom-4 duration-500 hover:shadow-lg transition-all">
      <CardHeader>
        <div className="flex items-center justify-between animate-in slide-in-from-left-4 duration-500 delay-200">
          <div className="space-y-1">
            <CardTitle className="text-xl">{t('scheduler.status')}</CardTitle>
            <CardDescription className="animate-in fade-in duration-500 delay-300">
              {t('scheduler.description')}
            </CardDescription>
          </div>
          <Badge
            variant={statusBadge.variant}
            className="gap-1.5 animate-in zoom-in-50 duration-300 delay-400"
          >
            <StatusIcon
              className={`h-3.5 w-3.5 ${status.isRunning ? 'animate-spin' : 'animate-pulse'}`}
            />
            {statusBadge.text}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Execution Information */}
        <div className="grid gap-4 sm:grid-cols-2 animate-in slide-in-from-bottom-4 duration-500 delay-500">
          {/* Last Execution */}
          <div className="space-y-1 animate-in slide-in-from-left-4 duration-300 delay-600">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <CheckCircle className="h-4 w-4 transition-transform duration-200 hover:scale-110" />
              <span>{t('scheduler.last-execution')}</span>
            </div>
            <div className="text-sm font-medium transition-all duration-200 hover:text-primary">
              {status.lastExecutionTime ? (
                <>
                  {formatRelativeTime(status.lastExecutionTime)}
                  {status.articlesProcessed > 0 && (
                    <span className="ml-2 text-muted-foreground animate-in fade-in duration-300 delay-700">
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
          <div className="space-y-1 animate-in slide-in-from-right-4 duration-300 delay-700">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Clock className="h-4 w-4 transition-transform duration-200 hover:scale-110" />
              <span>{t('scheduler.next-scheduled')}</span>
            </div>
            <div className="text-sm font-medium transition-all duration-200 hover:text-primary">
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
          <div className="rounded-lg bg-muted/50 p-3 space-y-2 animate-in slide-in-from-bottom-4 duration-500 delay-800 hover:bg-muted/70 transition-colors">
            <div className="text-sm font-medium animate-in fade-in duration-300 delay-900">
              {t('scheduler.execution-stats')}
            </div>
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div className="animate-in slide-in-from-left-2 duration-300 delay-1000">
                <div className="text-muted-foreground">{t('scheduler.total-operations')}</div>
                <div className="font-medium transition-all duration-200 hover:scale-110">
                  {status.totalOperations}
                </div>
              </div>
              <div className="animate-in slide-in-from-bottom-2 duration-300 delay-1100">
                <div className="text-muted-foreground">{t('scheduler.success')}</div>
                <div className="font-medium text-green-600 dark:text-green-400 transition-all duration-200 hover:scale-110">
                  {status.totalOperations - status.failedOperations}
                </div>
              </div>
              <div className="animate-in slide-in-from-right-2 duration-300 delay-1200">
                <div className="text-muted-foreground">{t('scheduler.failed')}</div>
                <div className="font-medium text-red-600 dark:text-red-400 transition-all duration-200 hover:scale-110">
                  {status.failedOperations}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Health Issues */}
        {status.issues && status.issues.length > 0 && (
          <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-3 space-y-2 animate-in slide-in-from-bottom-4 duration-500 delay-1000">
            <div className="flex items-center gap-2 text-sm font-medium text-destructive animate-in slide-in-from-left-2 duration-300 delay-1100">
              <AlertCircle className="h-4 w-4 animate-pulse" />
              <span>{t('scheduler.health-issues')}</span>
            </div>
            <ul className="space-y-1 text-sm text-muted-foreground">
              {status.issues.map((issue, index) => (
                <li
                  key={index}
                  className="flex items-start gap-2 animate-in slide-in-from-left-2 duration-300"
                  style={{ animationDelay: `${1200 + index * 100}ms` }}
                >
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
            className="w-full gap-2 animate-in slide-in-from-bottom-4 duration-500 delay-1300 transition-all hover:scale-105"
            variant="outline"
          >
            {isTriggering ? (
              <>
                <RefreshCw className="h-4 w-4 animate-spin" />
                {t('scheduler.triggering')}
              </>
            ) : (
              <>
                <PlayCircle className="h-4 w-4 transition-transform duration-200 hover:scale-110" />
                {t('scheduler.manual-trigger')}
              </>
            )}
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
