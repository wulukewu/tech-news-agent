/**
 * FeedHealthIndicator Component
 *
 * Displays feed health status including last update time and status indicator
 *
 * Validates: Requirements 4.2
 * - THE Feed_Management_Dashboard SHALL display Feed_Health_Indicator for each subscribed feed
 *   showing last update time and status
 */

import { Clock, CheckCircle2, AlertCircle, XCircle } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { zhTW } from 'date-fns/locale';
import { Badge } from '@/components/ui/badge';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';

export type FeedHealthStatus = 'healthy' | 'warning' | 'error' | 'unknown';

export interface FeedHealthIndicatorProps {
  lastUpdateTime?: Date | string | null;
  status: FeedHealthStatus;
  errorMessage?: string;
  className?: string;
}

const statusConfig = {
  healthy: {
    icon: CheckCircle2,
    label: '正常',
    variant: 'default' as const,
    color: 'text-green-600 dark:text-green-400',
  },
  warning: {
    icon: AlertCircle,
    label: '警告',
    variant: 'secondary' as const,
    color: 'text-yellow-600 dark:text-yellow-400',
  },
  error: {
    icon: XCircle,
    label: '錯誤',
    variant: 'destructive' as const,
    color: 'text-red-600 dark:text-red-400',
  },
  unknown: {
    icon: AlertCircle,
    label: '未知',
    variant: 'outline' as const,
    color: 'text-gray-600 dark:text-gray-400',
  },
};

export function FeedHealthIndicator({
  lastUpdateTime,
  status,
  errorMessage,
  className = '',
}: FeedHealthIndicatorProps) {
  const config = statusConfig[status];
  const Icon = config.icon;

  const formattedTime = lastUpdateTime
    ? (() => {
        try {
          return formatDistanceToNow(new Date(lastUpdateTime), {
            addSuffix: true,
            locale: zhTW,
          });
        } catch {
          return '從未更新';
        }
      })()
    : '從未更新';

  const tooltipContent = (
    <div className="space-y-1">
      <div className="flex items-center gap-2">
        <Icon className={`w-4 h-4 ${config.color}`} />
        <span className="font-medium">狀態: {config.label}</span>
      </div>
      <div className="flex items-center gap-2 text-sm">
        <Clock className="w-3 h-3" />
        <span>最後更新: {formattedTime}</span>
      </div>
      {errorMessage && (
        <div className="text-sm text-destructive mt-2 border-t pt-2">錯誤: {errorMessage}</div>
      )}
    </div>
  );

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <div className={`inline-flex items-center gap-2 ${className}`}>
            <Badge variant={config.variant} className="gap-1 cursor-help">
              <Icon className="w-3 h-3" />
              {config.label}
            </Badge>
            <span className="text-xs text-muted-foreground">{formattedTime}</span>
          </div>
        </TooltipTrigger>
        <TooltipContent side="bottom" className="max-w-xs">
          {tooltipContent}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
