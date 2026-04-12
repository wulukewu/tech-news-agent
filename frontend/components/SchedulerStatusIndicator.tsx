import { Clock, RefreshCw, CheckCircle } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';

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

/**
 * Format date to relative time string
 */
function formatRelativeTime(date: Date | null): string {
  if (!date) return '未知';

  const now = new Date();
  const diff = date.getTime() - now.getTime();
  const absDiff = Math.abs(diff);

  const minutes = Math.floor(absDiff / (1000 * 60));
  const hours = Math.floor(absDiff / (1000 * 60 * 60));
  const days = Math.floor(absDiff / (1000 * 60 * 60 * 24));

  if (diff < 0) {
    // Past time
    if (minutes < 1) return '剛剛';
    if (minutes < 60) return `${minutes} 分鐘前`;
    if (hours < 24) return `${hours} 小時前`;
    return `${days} 天前`;
  } else {
    // Future time
    if (minutes < 1) return '即將執行';
    if (minutes < 60) return `${minutes} 分鐘後`;
    if (hours < 24) return `${hours} 小時後`;
    return `${days} 天後`;
  }
}

/**
 * SchedulerStatusIndicator component
 *
 * Displays scheduler execution status, timing information, and manual trigger option.
 * Shows loading indicator when scheduler is running.
 *
 * Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7
 *
 * @example
 * ```tsx
 * <SchedulerStatusIndicator
 *   status={{
 *     lastExecutionTime: new Date(),
 *     nextScheduledTime: new Date(Date.now() + 3600000),
 *     isRunning: false,
 *     lastExecutionArticleCount: 15,
 *     estimatedTimeUntilArticles: '5-10 分鐘'
 *   }}
 *   onManualTrigger={() => triggerFetch()}
 *   canManualTrigger={true}
 * />
 * ```
 */
export function SchedulerStatusIndicator({
  status,
  onManualTrigger,
  canManualTrigger = true,
}: SchedulerStatusIndicatorProps) {
  const {
    lastExecutionTime,
    nextScheduledTime,
    isRunning,
    lastExecutionArticleCount,
    estimatedTimeUntilArticles,
  } = status;

  return (
    <Card className="border-muted">
      <CardContent className="py-4">
        <div className="flex items-start justify-between">
          <div className="flex-1 space-y-2">
            {/* Running indicator */}
            {isRunning && (
              <div className="flex items-center gap-2 text-sm text-primary">
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span className="font-medium">排程器執行中...</span>
              </div>
            )}

            {/* Last execution time */}
            {!isRunning && lastExecutionTime && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <CheckCircle className="w-4 h-4" />
                <span>
                  上次執行：{formatRelativeTime(lastExecutionTime)}
                  {lastExecutionArticleCount > 0 && ` (抓取 ${lastExecutionArticleCount} 篇文章)`}
                </span>
              </div>
            )}

            {/* Next scheduled time */}
            {nextScheduledTime && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Clock className="w-4 h-4" />
                <span>下次排程：{formatRelativeTime(nextScheduledTime)}</span>
              </div>
            )}

            {/* Estimated time until articles */}
            {estimatedTimeUntilArticles && !isRunning && (
              <div className="text-sm text-muted-foreground">
                預計 {estimatedTimeUntilArticles} 後會有新文章
              </div>
            )}
          </div>

          {/* Manual trigger button */}
          {onManualTrigger && canManualTrigger && !isRunning && (
            <button
              onClick={onManualTrigger}
              className="ml-4 px-3 py-1.5 text-sm border border-input bg-background rounded-md hover:bg-accent hover:text-accent-foreground transition-colors"
              aria-label="手動觸發抓取"
            >
              手動抓取
            </button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
