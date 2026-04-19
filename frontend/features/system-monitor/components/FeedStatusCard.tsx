/**
 * Feed Status Card Component
 *
 * Displays individual feed fetch status and error messages
 * with health indicators.
 *
 * Requirements: 5.6
 */

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Rss,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Clock,
  FileText,
  ExternalLink,
} from 'lucide-react';
import type { FeedStatus } from '../types';
import { formatDistanceToNow } from 'date-fns';
import { zhTW, enUS } from 'date-fns/locale';
import { useI18n } from '@/contexts/I18nContext';

interface FeedStatusCardProps {
  feeds: FeedStatus[];
}

/**
 * Get status icon and color based on feed health
 */
function getStatusDisplay(status: FeedStatus['status'], t: any) {
  switch (status) {
    case 'healthy':
      return {
        icon: CheckCircle2,
        color: 'text-green-600 dark:text-green-400',
        bgColor: 'bg-green-50 dark:bg-green-950',
        badge: 'default',
        label: t('ui.healthy'),
      };
    case 'warning':
      return {
        icon: AlertTriangle,
        color: 'text-yellow-600 dark:text-yellow-400',
        bgColor: 'bg-yellow-50 dark:bg-yellow-950',
        badge: 'secondary',
        label: t('ui.warning'),
      };
    case 'error':
      return {
        icon: XCircle,
        color: 'text-red-600 dark:text-red-400',
        bgColor: 'bg-red-50 dark:bg-red-950',
        badge: 'destructive',
        label: t('ui.error'),
      };
  }
}

/**
 * Format processing time with appropriate color
 */
function formatProcessingTime(ms: number): { value: string; color: string } {
  const seconds = ms / 1000;
  if (seconds < 5) {
    return { value: `${seconds.toFixed(1)}s`, color: 'text-green-600 dark:text-green-400' };
  } else if (seconds < 15) {
    return { value: `${seconds.toFixed(1)}s`, color: 'text-yellow-600 dark:text-yellow-400' };
  } else {
    return { value: `${seconds.toFixed(1)}s`, color: 'text-red-600 dark:text-red-400' };
  }
}

/**
 * Individual feed status item
 */
function FeedStatusItem({ feed, t, locale }: { feed: FeedStatus; t: any; locale: any }) {
  const statusDisplay = getStatusDisplay(feed.status, t);
  const StatusIcon = statusDisplay.icon;
  const processingTime = formatProcessingTime(feed.processingTime);

  return (
    <div className={`rounded-lg border p-4 ${statusDisplay.bgColor} border-border`}>
      <div className="space-y-3">
        {/* Feed Header */}
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <Rss className="h-4 w-4 text-muted-foreground flex-shrink-0" />
              <h4 className="font-medium text-sm truncate">{feed.name}</h4>
            </div>
            <a
              href={feed.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-muted-foreground hover:text-primary flex items-center gap-1 truncate"
            >
              <span className="truncate">{feed.url}</span>
              <ExternalLink className="h-3 w-3 flex-shrink-0" />
            </a>
          </div>
          <Badge variant={statusDisplay.badge as any} className="flex-shrink-0">
            <StatusIcon className="h-3 w-3 mr-1" />
            {statusDisplay.label}
          </Badge>
        </div>

        {/* Feed Metrics */}
        <div className="grid grid-cols-3 gap-3 text-xs">
          <div className="space-y-1">
            <div className="text-muted-foreground">{t('ui.last-fetch')}</div>
            <div className="font-medium">
              {feed.lastFetch
                ? formatDistanceToNow(feed.lastFetch, { addSuffix: true, locale })
                : t('ui.never')}
            </div>
          </div>
          <div className="space-y-1">
            <div className="text-muted-foreground">{t('ui.articles-processed')}</div>
            <div className="font-medium flex items-center gap-1">
              <FileText className="h-3 w-3" />
              {feed.articlesProcessed}
            </div>
          </div>
          <div className="space-y-1">
            <div className="text-muted-foreground">{t('ui.processing-time')}</div>
            <div className={`font-medium font-mono ${processingTime.color}`}>
              {processingTime.value}
            </div>
          </div>
        </div>

        {/* Next Fetch */}
        {feed.nextFetch && (
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Clock className="h-3 w-3" />
            <span>
              {t('ui.next-fetch')}:{' '}
              {formatDistanceToNow(feed.nextFetch, { addSuffix: true, locale })}
            </span>
          </div>
        )}

        {/* Error Message */}
        {feed.errorMessage && (
          <div className="rounded bg-destructive/10 p-2 text-xs text-destructive">
            <div className="font-medium mb-1">{t('ui.error-message')}:</div>
            <div className="break-words">{feed.errorMessage}</div>
          </div>
        )}
      </div>
    </div>
  );
}

export function FeedStatusCard({ feeds }: FeedStatusCardProps) {
  const { t, locale } = useI18n();
  const dateLocale = locale === 'zh-TW' ? zhTW : enUS;

  // Sort feeds by status (error > warning > healthy) and then by name
  const sortedFeeds = [...feeds].sort((a, b) => {
    const statusOrder = { error: 0, warning: 1, healthy: 2 };
    const statusDiff = statusOrder[a.status] - statusOrder[b.status];
    if (statusDiff !== 0) return statusDiff;
    return a.name.localeCompare(b.name);
  });

  // Calculate status counts
  const statusCounts = feeds.reduce(
    (acc, feed) => {
      acc[feed.status]++;
      return acc;
    },
    { healthy: 0, warning: 0, error: 0 }
  );

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-xl flex items-center gap-2">
              <Rss className="h-5 w-5" />
              {t('ui.feed-status')}
            </CardTitle>
            <CardDescription>{t('ui.feed-status-desc')}</CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="default" className="bg-green-500 hover:bg-green-600">
              {statusCounts.healthy} {t('ui.healthy')}
            </Badge>
            {statusCounts.warning > 0 && (
              <Badge variant="secondary">
                {statusCounts.warning} {t('ui.warning')}
              </Badge>
            )}
            {statusCounts.error > 0 && (
              <Badge variant="destructive">
                {statusCounts.error} {t('ui.error')}
              </Badge>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {feeds.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <Rss className="h-12 w-12 mx-auto mb-3 opacity-50" />
            <p>{t('ui.no-feed-data')}</p>
          </div>
        ) : (
          <ScrollArea className="h-[600px] pr-4">
            <div className="space-y-3">
              {sortedFeeds.map((feed) => (
                <FeedStatusItem key={feed.id} feed={feed} t={t} locale={dateLocale} />
              ))}
            </div>
          </ScrollArea>
        )}
      </CardContent>
    </Card>
  );
}
