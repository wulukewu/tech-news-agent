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
function FeedStatusItem({
  feed,
  t,
  locale,
  index,
}: {
  feed: FeedStatus;
  t: any;
  locale: any;
  index: number;
}) {
  const statusDisplay = getStatusDisplay(feed.status, t);
  const StatusIcon = statusDisplay.icon;
  const processingTime = formatProcessingTime(feed.processingTime);

  return (
    <div
      className={`rounded-lg border p-4 ${statusDisplay.bgColor} border-border animate-in slide-in-from-bottom-4 duration-500 hover:shadow-md transition-all`}
      style={{ animationDelay: `${index * 100}ms` }}
    >
      <div className="space-y-3">
        {/* Feed Header */}
        <div
          className="flex items-start justify-between gap-2 animate-in slide-in-from-left-2 duration-300"
          style={{ animationDelay: `${index * 100 + 200}ms` }}
        >
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <Rss className="h-4 w-4 text-muted-foreground flex-shrink-0 transition-transform duration-200 hover:scale-110" />
              <h4 className="font-medium text-sm truncate transition-colors duration-200 hover:text-primary">
                {feed.name}
              </h4>
            </div>
            <a
              href={feed.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-muted-foreground hover:text-primary flex items-center gap-1 truncate transition-all duration-200 hover:scale-105"
            >
              <span className="truncate">{feed.url}</span>
              <ExternalLink className="h-3 w-3 flex-shrink-0 transition-transform duration-200 hover:scale-110" />
            </a>
          </div>
          <Badge
            variant={statusDisplay.badge as any}
            className="flex-shrink-0 animate-in zoom-in-50 duration-300"
            style={{ animationDelay: `${index * 100 + 300}ms` }}
          >
            <StatusIcon
              className={`h-3 w-3 mr-1 ${feed.status === 'error' ? 'animate-pulse' : ''}`}
            />
            {statusDisplay.label}
          </Badge>
        </div>

        {/* Feed Metrics */}
        <div className="grid grid-cols-3 gap-3 text-xs">
          <div
            className="space-y-1 animate-in slide-in-from-left-2 duration-300"
            style={{ animationDelay: `${index * 100 + 400}ms` }}
          >
            <div className="text-muted-foreground">{t('ui.last-fetch')}</div>
            <div className="font-medium transition-all duration-200 hover:scale-110">
              {feed.lastFetch
                ? formatDistanceToNow(feed.lastFetch, { addSuffix: true, locale })
                : t('ui.never')}
            </div>
          </div>
          <div
            className="space-y-1 animate-in slide-in-from-bottom-2 duration-300"
            style={{ animationDelay: `${index * 100 + 500}ms` }}
          >
            <div className="text-muted-foreground">{t('ui.articles-processed')}</div>
            <div className="font-medium flex items-center gap-1 transition-all duration-200 hover:scale-110">
              <FileText className="h-3 w-3 transition-transform duration-200 hover:scale-110" />
              {feed.articlesProcessed}
            </div>
          </div>
          <div
            className="space-y-1 animate-in slide-in-from-right-2 duration-300"
            style={{ animationDelay: `${index * 100 + 600}ms` }}
          >
            <div className="text-muted-foreground">{t('ui.processing-time')}</div>
            <div
              className={`font-medium font-mono ${processingTime.color} transition-all duration-200 hover:scale-110`}
            >
              {processingTime.value}
            </div>
          </div>
        </div>

        {/* Next Fetch */}
        {feed.nextFetch && (
          <div
            className="flex items-center gap-2 text-xs text-muted-foreground animate-in slide-in-from-left-2 duration-300"
            style={{ animationDelay: `${index * 100 + 700}ms` }}
          >
            <Clock className="h-3 w-3 transition-transform duration-200 hover:scale-110" />
            <span className="transition-colors duration-200 hover:text-foreground">
              {t('ui.next-fetch')}:{' '}
              {formatDistanceToNow(feed.nextFetch, { addSuffix: true, locale })}
            </span>
          </div>
        )}

        {/* Error Message */}
        {feed.errorMessage && (
          <div
            className="rounded bg-destructive/10 p-2 text-xs text-destructive animate-in slide-in-from-bottom-2 duration-300"
            style={{ animationDelay: `${index * 100 + 800}ms` }}
          >
            <div className="font-medium mb-1 animate-pulse">{t('ui.error-message')}:</div>
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
    <Card className="animate-in fade-in slide-in-from-bottom-4 duration-500 hover:shadow-lg transition-all">
      <CardHeader>
        <div className="flex items-center justify-between animate-in slide-in-from-left-4 duration-500 delay-200">
          <div>
            <CardTitle className="text-xl flex items-center gap-2">
              <div className="p-1 rounded-lg bg-primary/10 text-primary animate-in zoom-in-50 duration-300 delay-300 hover:scale-110 transition-transform">
                <Rss className="h-5 w-5 animate-pulse" />
              </div>
              {t('ui.feed-status')}
            </CardTitle>
            <CardDescription className="animate-in fade-in duration-500 delay-400">
              {t('ui.feed-status-desc')}
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Badge
              variant="default"
              className="bg-green-500 hover:bg-green-600 animate-in zoom-in-50 duration-300 delay-500 transition-all hover:scale-105"
            >
              {statusCounts.healthy} {t('ui.healthy')}
            </Badge>
            {statusCounts.warning > 0 && (
              <Badge
                variant="secondary"
                className="animate-in zoom-in-50 duration-300 delay-600 transition-all hover:scale-105"
              >
                {statusCounts.warning} {t('ui.warning')}
              </Badge>
            )}
            {statusCounts.error > 0 && (
              <Badge
                variant="destructive"
                className="animate-in zoom-in-50 duration-300 delay-700 animate-pulse transition-all hover:scale-105"
              >
                {statusCounts.error} {t('ui.error')}
              </Badge>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent className="animate-in slide-in-from-bottom-4 duration-500 delay-800">
        {feeds.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground animate-in fade-in duration-500 delay-1000">
            <Rss className="h-12 w-12 mx-auto mb-3 opacity-50 animate-pulse" />
            <p>{t('ui.no-feed-data')}</p>
          </div>
        ) : (
          <ScrollArea className="h-[600px] pr-4">
            <div className="space-y-3">
              {sortedFeeds.map((feed, index) => (
                <FeedStatusItem key={feed.id} feed={feed} t={t} locale={dateLocale} index={index} />
              ))}
            </div>
          </ScrollArea>
        )}
      </CardContent>
    </Card>
  );
}
