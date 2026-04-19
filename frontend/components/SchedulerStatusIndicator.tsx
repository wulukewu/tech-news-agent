import { Clock, RefreshCw, CheckCircle } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { useI18n } from '@/contexts/I18nContext';

/**
 * Scheduler status information
 */
export interface SchedulerStatus {
  lastExecutionTime: Date | null;
  nextScheduledTime: Date | null;
  isRunning: boolean;
  lastExecutionArticleCount: number;
  estimatedTimeUntilArticles: string;
}

/**
 * SchedulerStatusIndicator component props
 */
export interface SchedulerStatusIndicatorProps {
  /**
   * Current scheduler status
   */
  status: SchedulerStatus;

  /**
   * Callback when user wants to manually trigger fetch
   */
  onManualTrigger?: () => void;

  /**
   * Whether manual trigger is available
   */
  canManualTrigger?: boolean;
}

export function SchedulerStatusIndicator({
  status,
  onManualTrigger,
  canManualTrigger = true,
}: SchedulerStatusIndicatorProps) {
  const { t } = useI18n();
  const {
    lastExecutionTime,
    nextScheduledTime,
    isRunning,
    lastExecutionArticleCount,
    estimatedTimeUntilArticles,
  } = status;

  /**
   * Format date to relative time string
   */
  function formatRelativeTime(date: Date | null): string {
    if (!date) return t('ui.unknown');

    const now = new Date();
    const diff = date.getTime() - now.getTime();
    const absDiff = Math.abs(diff);

    const minutes = Math.floor(absDiff / (1000 * 60));
    const hours = Math.floor(absDiff / (1000 * 60 * 60));
    const days = Math.floor(absDiff / (1000 * 60 * 60 * 24));

    if (diff < 0) {
      // Past time
      if (minutes < 1) return t('time.just-now');
      if (minutes < 60) return t('time.minutes-ago', { count: minutes });
      if (hours < 24) return t('time.hours-ago', { count: hours });
      return t('time.days-ago', { count: days });
    } else {
      // Future time
      if (minutes < 1) return t('time.executing-soon');
      if (minutes < 60) return t('time.minutes-later', { count: minutes });
      if (hours < 24) return t('time.hours-later', { count: hours });
      return t('time.days-later', { count: days });
    }
  }

  return (
    <Card className="border-muted">
      <CardContent className="py-4">
        <div className="flex items-start justify-between">
          <div className="flex-1 space-y-2">
            {/* Running indicator */}
            {isRunning && (
              <div className="flex items-center gap-2 text-sm text-primary">
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span className="font-medium">{t('time.scheduler-running')}</span>
              </div>
            )}

            {/* Last execution time */}
            {!isRunning && lastExecutionTime && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <CheckCircle className="w-4 h-4" />
                <span>
                  {t('time.last-execution')}：{formatRelativeTime(lastExecutionTime)}
                  {lastExecutionArticleCount > 0 &&
                    ` (${t('time.fetched-articles', { count: lastExecutionArticleCount })})`}
                </span>
              </div>
            )}

            {/* Next scheduled time */}
            {nextScheduledTime && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Clock className="w-4 h-4" />
                <span>
                  {t('time.next-scheduled')}：{formatRelativeTime(nextScheduledTime)}
                </span>
              </div>
            )}

            {/* Estimated time until articles */}
            {estimatedTimeUntilArticles && !isRunning && (
              <div className="text-sm text-muted-foreground">
                {t('time.estimated-time', { time: estimatedTimeUntilArticles })}
              </div>
            )}
          </div>

          {/* Manual trigger button */}
          {onManualTrigger && canManualTrigger && !isRunning && (
            <button
              onClick={onManualTrigger}
              className="ml-4 px-3 py-1.5 text-sm border border-input bg-background rounded-md hover:bg-accent hover:text-accent-foreground transition-colors"
              aria-label={t('time.manual-trigger')}
            >
              {t('time.manual-fetch')}
            </button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
