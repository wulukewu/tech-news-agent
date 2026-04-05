import { ReactNode } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Rss, FileText, BookMarked } from 'lucide-react';

/**
 * Scheduler status information (optional)
 */
export interface SchedulerStatus {
  lastExecutionTime: Date | null;
  nextScheduledTime: Date | null;
  isRunning: boolean;
  lastExecutionArticleCount: number;
  estimatedTimeUntilArticles: string;
}

/**
 * EmptyState component props
 * Supports three variants for different empty states
 */
export interface EmptyStateProps {
  /**
   * Variant type determines the icon and default styling
   */
  type?: 'no-subscriptions' | 'no-articles' | 'no-reading-list';

  /**
   * Main heading text
   */
  title: string;

  /**
   * Description text explaining the empty state
   */
  description: string;

  /**
   * Primary action button/element
   */
  primaryAction?: {
    label: string;
    onClick: () => void;
  };

  /**
   * Secondary action button/element (optional)
   */
  secondaryAction?: {
    label: string;
    onClick: () => void;
  };

  /**
   * Custom action element (for backward compatibility)
   */
  action?: ReactNode;

  /**
   * Custom icon element (overrides default variant icon)
   */
  icon?: ReactNode;

  /**
   * Scheduler status information (for no-articles variant)
   */
  schedulerStatus?: SchedulerStatus;
}

/**
 * Get default icon based on variant type
 */
function getDefaultIcon(type?: EmptyStateProps['type']): ReactNode {
  const iconClass = 'w-12 h-12';

  switch (type) {
    case 'no-subscriptions':
      return <Rss className={iconClass} />;
    case 'no-articles':
      return <FileText className={iconClass} />;
    case 'no-reading-list':
      return <BookMarked className={iconClass} />;
    default:
      return <FileText className={iconClass} />;
  }
}

/**
 * EmptyState component
 *
 * Displays helpful messages when users have no content.
 * Supports three variants:
 * - no-subscriptions: When user has no RSS subscriptions
 * - no-articles: When user has subscriptions but no articles yet
 * - no-reading-list: When user's reading list is empty
 *
 * @example
 * ```tsx
 * <EmptyState
 *   type="no-subscriptions"
 *   title="還沒有訂閱"
 *   description="開始訂閱一些 RSS 來源來查看文章"
 *   primaryAction={{
 *     label: "管理訂閱",
 *     onClick: () => router.push('/subscriptions')
 *   }}
 * />
 * ```
 */
export function EmptyState({
  type,
  title,
  description,
  primaryAction,
  secondaryAction,
  action,
  icon,
  schedulerStatus,
}: EmptyStateProps) {
  const displayIcon = icon || getDefaultIcon(type);

  return (
    <Card className="border-dashed">
      <CardContent className="flex flex-col items-center justify-center py-12 text-center">
        {displayIcon && (
          <div className="mb-4 text-muted-foreground">{displayIcon}</div>
        )}

        <h3 className="text-lg font-semibold mb-2">{title}</h3>
        <p className="text-muted-foreground mb-6 max-w-md">{description}</p>

        {/* Scheduler status info (for no-articles variant) */}
        {schedulerStatus && (
          <div className="mb-6 text-sm text-muted-foreground max-w-md">
            {schedulerStatus.lastExecutionTime && (
              <p>
                上次執行時間：
                {new Date(schedulerStatus.lastExecutionTime).toLocaleString(
                  'zh-TW',
                )}
              </p>
            )}
            {schedulerStatus.estimatedTimeUntilArticles && (
              <p className="mt-1">
                預計 {schedulerStatus.estimatedTimeUntilArticles} 後會有新文章
              </p>
            )}
          </div>
        )}

        {/* Action buttons */}
        {(primaryAction || secondaryAction || action) && (
          <div className="flex flex-col sm:flex-row gap-3">
            {primaryAction && (
              <button
                onClick={primaryAction.onClick}
                className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
              >
                {primaryAction.label}
              </button>
            )}

            {secondaryAction && (
              <button
                onClick={secondaryAction.onClick}
                className="px-4 py-2 border border-input bg-background rounded-md hover:bg-accent hover:text-accent-foreground transition-colors"
              >
                {secondaryAction.label}
              </button>
            )}

            {/* Backward compatibility with custom action element */}
            {action && <div>{action}</div>}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
