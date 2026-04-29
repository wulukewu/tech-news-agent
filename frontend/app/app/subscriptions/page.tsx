'use client';
import { logger } from '@/lib/utils/logger';

import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import {
  fetchFeeds,
  toggleSubscription,
  batchSubscribe,
  addCustomFeed,
  previewFeed,
  deleteFeed,
  updateFeedNotificationPreference,
} from '@/lib/api/feeds';
import type { Feed } from '@/types/feed';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { ChevronDown, ChevronRight, Star, Bell, BellOff, Trash2 } from 'lucide-react';
import { toast } from '@/lib/toast';
import { FeedHealthIndicator } from '@/features/subscriptions/components/FeedHealthIndicator';
import { FeedStatistics } from '@/features/subscriptions/components/FeedStatistics';
import { AddCustomFeedDialog } from '@/features/subscriptions/components/AddCustomFeedDialog';
import { OPMLImportExport } from '@/features/subscriptions/components/OPMLImportExport';
import { FeedSearch } from '@/features/subscriptions/components/FeedSearch';
import type { OPMLOutline } from '@/features/subscriptions/utils/opml';
import { useI18n } from '@/contexts/I18nContext';

/** Reusable health stats grid — avoids duplication across tabs */
function HealthStatsGrid({ feeds, subscribed }: { feeds: Feed[]; subscribed?: boolean }) {
  const { t } = useI18n();
  const filtered = subscribed ? feeds.filter((f) => f.is_subscribed) : feeds;
  const stats = [
    { key: 'healthy', label: t('ui.health-healthy'), dot: 'bg-green-500' },
    { key: 'warning', label: t('ui.health-stale'), dot: 'bg-yellow-500' },
    { key: 'error', label: t('ui.health-error'), dot: 'bg-red-500' },
    { key: 'unknown', label: t('ui.health-unknown'), dot: 'bg-muted-foreground' },
  ] as const;

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
      {stats.map(({ key, label, dot }) => (
        <Card key={key}>
          <CardContent className="p-3">
            <div className="flex items-center gap-2">
              <div className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${dot}`} />
              <div className="min-w-0">
                <div className="text-xs text-muted-foreground truncate">{label}</div>
                <div className="text-lg font-semibold tabular-nums">
                  {
                    filtered.filter((f) =>
                      key === 'unknown'
                        ? f.health_status === 'unknown' || !f.health_status
                        : f.health_status === key
                    ).length
                  }
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

export default function SubscriptionsPage() {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const router = useRouter();
  const { t } = useI18n();
  const [feeds, setFeeds] = useState<Feed[]>([]);
  const [filteredFeeds, setFilteredFeeds] = useState<Feed[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [toggling, setToggling] = useState<Set<string>>(new Set());
  const [currentTab, setCurrentTab] = useState<'subscriptions' | 'explore'>('subscriptions');
  const [collapsedCategories, setCollapsedCategories] = useState<Set<string>>(() => {
    // Load collapsed state from localStorage
    if (typeof window !== 'undefined') {
      try {
        const saved = localStorage.getItem('subscriptions-collapsed-categories');
        return saved ? new Set(JSON.parse(saved)) : new Set();
      } catch {
        return new Set();
      }
    }
    return new Set();
  });

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, authLoading, router]);

  useEffect(() => {
    if (isAuthenticated) {
      loadFeeds();
    }
  }, [isAuthenticated]);

  const loadFeeds = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchFeeds();
      setFeeds(data || []);
      setFilteredFeeds(data || []);

      // Auto-collapse non-recommended categories
      const nonRecommendedCategories = new Set(
        (data || []).filter((feed) => !feed.is_recommended).map((feed) => feed.category)
      );
      setCollapsedCategories(nonRecommendedCategories);
    } catch (err) {
      console.error('Failed to load feeds:', err);
      setError(t('errors.server-error'));
      setFeeds([]);
      setFilteredFeeds([]);
    } finally {
      setLoading(false);
    }
  };

  const handleToggle = async (feedId: string) => {
    try {
      setToggling((prev) => new Set(prev).add(feedId));
      const result = await toggleSubscription(feedId);

      // Update local state — use feedId (string) directly to avoid UUID vs string mismatch
      setFeeds((prev) =>
        prev.map((feed) =>
          feed.id === feedId ? { ...feed, is_subscribed: result.is_subscribed } : feed
        )
      );
    } catch (err) {
      console.error('Failed to toggle subscription:', err);
      toast.error(t('errors.server-error'));
    } finally {
      setToggling((prev) => {
        const next = new Set(prev);
        next.delete(feedId);
        return next;
      });
    }
  };

  const handleCategoryToggle = async (category: string, subscribe: boolean) => {
    const categoryFeeds = filteredFeeds.filter((f) => f.category === category);
    const feedsToToggle = categoryFeeds.filter((f) => f.is_subscribed !== subscribe);

    if (feedsToToggle.length === 0) return;

    const updater = (prev: Feed[]) =>
      prev.map((feed) =>
        feed.category === category ? { ...feed, is_subscribed: subscribe } : feed
      );
    setFeeds(updater);
    setFilteredFeeds(updater);

    try {
      if (subscribe) {
        await batchSubscribe(feedsToToggle.map((f) => f.id));
      } else {
        await Promise.all(feedsToToggle.map((feed) => toggleSubscription(feed.id)));
      }
      toast.success(
        subscribe
          ? t('subscriptions.subscribed', { count: feedsToToggle.length })
          : t('subscriptions.unsubscribed', { count: feedsToToggle.length })
      );
    } catch (err) {
      const reverter = (prev: Feed[]) =>
        prev.map((feed) =>
          feed.category === category ? { ...feed, is_subscribed: !subscribe } : feed
        );
      setFeeds(reverter);
      setFilteredFeeds(reverter);
      console.error('Failed to toggle category:', err);
      toast.error(t('subscriptions.batch-operation-failed'));
    }
  };

  const handleToggleAll = async (subscribe: boolean) => {
    const feedsToToggle = filteredFeeds.filter((f) => f.is_subscribed !== subscribe);

    if (feedsToToggle.length === 0) return;

    // Optimistic update — update both feeds and filteredFeeds
    const updater = (prev: Feed[]) => prev.map((feed) => ({ ...feed, is_subscribed: subscribe }));
    setFeeds(updater);
    setFilteredFeeds(updater);

    try {
      if (subscribe) {
        await batchSubscribe(feedsToToggle.map((f) => f.id));
      } else {
        await Promise.all(feedsToToggle.map((feed) => toggleSubscription(feed.id)));
      }
      toast.success(
        subscribe
          ? t('subscriptions.subscribed', { count: feedsToToggle.length })
          : t('subscriptions.unsubscribed', { count: feedsToToggle.length })
      );
    } catch (err) {
      // Revert only the feeds that were changed
      const toggledIds = new Set(feedsToToggle.map((f) => f.id));
      const reverter = (prev: Feed[]) =>
        prev.map((feed) =>
          toggledIds.has(feed.id) ? { ...feed, is_subscribed: !subscribe } : feed
        );
      setFeeds(reverter);
      setFilteredFeeds(reverter);
      console.error('Failed to toggle all:', err);
      toast.error(t('subscriptions.batch-operation-failed'));
    }
  };

  const handleSubscribeRecommended = async () => {
    const recommendedFeeds = feeds.filter((f) => f.is_recommended && !f.is_subscribed);

    if (recommendedFeeds.length === 0) {
      toast.info(t('subscriptions.already-subscribed-all-recommended'));
      return;
    }

    const updater = (prev: Feed[]) =>
      prev.map((feed) => (feed.is_recommended ? { ...feed, is_subscribed: true } : feed));
    setFeeds(updater);
    setFilteredFeeds(updater);

    try {
      await batchSubscribe(recommendedFeeds.map((f) => f.id));
      toast.success(t('subscriptions.subscribed-recommended', { count: recommendedFeeds.length }));
    } catch (err) {
      const toggledIds = new Set(recommendedFeeds.map((f) => f.id));
      const reverter = (prev: Feed[]) =>
        prev.map((feed) => (toggledIds.has(feed.id) ? { ...feed, is_subscribed: false } : feed));
      setFeeds(reverter);
      setFilteredFeeds(reverter);
      console.error('Failed to subscribe recommended:', err);
      toast.error(t('subscriptions.subscribe-recommended-failed'));
    }
  };

  const handleRetryFailedFeeds = async () => {
    const failedFeeds = feeds.filter((f) => f.health_status === 'error');

    if (failedFeeds.length === 0) {
      toast.info(t('subscriptions.no-failed-feeds'));
      return;
    }

    try {
      setToggling((prev) => {
        const next = new Set(prev);
        failedFeeds.forEach((f) => next.add(f.id));
        return next;
      });

      // Here you would call an API to retry failed feeds
      // For now, we'll simulate the retry by reloading feeds
      await loadFeeds();

      toast.success(t('subscriptions.retried-feeds', { count: failedFeeds.length }));
    } catch (err) {
      console.error('Failed to retry feeds:', err);
      toast.error(t('subscriptions.retry-failed-error'));
    } finally {
      setToggling((prev) => {
        const next = new Set(prev);
        failedFeeds.forEach((f) => next.delete(f.id));
        return next;
      });
    }
  };

  const toggleCategoryCollapse = (category: string) => {
    setCollapsedCategories((prev) => {
      const next = new Set(prev);
      if (next.has(category)) {
        next.delete(category);
      } else {
        next.add(category);
      }

      // Persist to localStorage
      if (typeof window !== 'undefined') {
        try {
          localStorage.setItem('subscriptions-collapsed-categories', JSON.stringify([...next]));
        } catch (error) {
          logger.warn('Failed to save collapsed categories to localStorage:', error);
        }
      }

      return next;
    });
  };

  const handleAddCustomFeed = async (url: string, name?: string, category?: string) => {
    await addCustomFeed(url, name, category);
    await loadFeeds(); // Reload feeds after adding
  };

  const handlePreviewFeed = async (url: string) => {
    return await previewFeed(url);
  };

  const handleOPMLImport = async (opmlFeeds: OPMLOutline[]) => {
    // Import feeds from OPML
    const importPromises = opmlFeeds.map((feed) =>
      addCustomFeed(feed.xmlUrl!, feed.text, feed.category)
    );

    await Promise.allSettled(importPromises);
    await loadFeeds(); // Reload feeds after import
  };

  const handleFilteredFeedsChange = useCallback((filtered: Feed[]) => {
    setFilteredFeeds((prev) => {
      // Only update if the filtered feeds actually changed
      if (prev.length !== filtered.length) {
        return filtered;
      }
      // Check if the feed IDs are the same
      const prevIds = prev.map((f) => f.id).join(',');
      const filteredIds = filtered.map((f) => f.id).join(',');
      if (prevIds !== filteredIds) {
        return filtered;
      }
      // Check if subscription status changed for any feed
      const hasSubscriptionChange = prev.some((prevFeed, index) => {
        const currentFeed = filtered[index];
        return currentFeed && prevFeed.is_subscribed !== currentFeed.is_subscribed;
      });
      if (hasSubscriptionChange) {
        return filtered;
      }
      // No change, return previous state to prevent re-render
      return prev;
    });
  }, []);

  const toggleNotification = async (feedId: string, currentState: boolean) => {
    try {
      await updateFeedNotificationPreference(feedId, !currentState);
      setFeeds((prev) =>
        prev.map((feed) =>
          feed.id === feedId ? { ...feed, notification_enabled: !currentState } : feed
        )
      );
      setFilteredFeeds((prev) =>
        prev.map((feed) =>
          feed.id === feedId ? { ...feed, notification_enabled: !currentState } : feed
        )
      );
      toast.success(
        t('subscriptions.notification-toggled', {
          status: !currentState ? t('subscriptions.enabled') : t('subscriptions.disabled'),
        })
      );
    } catch {
      toast.error(t('errors.server-error'));
    }
  };

  const handleDeleteFeed = async (feedId: string, feedName: string) => {
    if (!confirm(t('subscriptions.confirm-delete', { name: feedName }))) return;
    try {
      await deleteFeed(feedId);
      setFeeds((prev) => prev.filter((f) => f.id !== feedId));
      toast.success(t('subscriptions.feed-deleted', { name: feedName }));
    } catch {
      toast.error(t('errors.server-error'));
    }
  };

  if (authLoading || loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">{t('messages.loading')}</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  // Group feeds by category - filter based on current tab
  const displayFeeds =
    currentTab === 'subscriptions'
      ? (filteredFeeds || []).filter((f) => f.is_subscribed)
      : filteredFeeds || [];

  const feedsByCategory = displayFeeds.reduce(
    (acc, feed) => {
      if (!acc[feed.category]) {
        acc[feed.category] = [];
      }
      acc[feed.category].push(feed);
      return acc;
    },
    {} as Record<string, Feed[]>
  );

  // Sort feeds within each category by health status (healthy first, errors last)
  Object.keys(feedsByCategory).forEach((category) => {
    feedsByCategory[category].sort((a, b) => {
      const healthOrder = { healthy: 0, warning: 1, unknown: 2, error: 3 };
      const aHealth = a.health_status || 'unknown';
      const bHealth = b.health_status || 'unknown';

      const healthDiff = healthOrder[aHealth] - healthOrder[bHealth];
      if (healthDiff !== 0) return healthDiff;

      // If health status is the same, sort by name
      return a.name.localeCompare(b.name);
    });
  });

  // Sort categories: recommended first
  const sortedCategories = Object.keys(feedsByCategory).sort((a, b) => {
    const aHasRecommended = feedsByCategory[a].some((f) => f.is_recommended);
    const bHasRecommended = feedsByCategory[b].some((f) => f.is_recommended);

    if (aHasRecommended && !bHasRecommended) return -1;
    if (!aHasRecommended && bHasRecommended) return 1;
    return a.localeCompare(b);
  });

  const totalSubscribed = (feeds || []).filter((f) => f.is_subscribed).length;
  const totalRecommended = (feeds || []).filter((f) => f.is_recommended).length;
  const recommendedSubscribed = (feeds || []).filter(
    (f) => f.is_recommended && f.is_subscribed
  ).length;
  const allSubscribed = totalSubscribed === (feeds || []).length;
  const noneSubscribed = totalSubscribed === 0;
  const allRecommendedSubscribed = recommendedSubscribed === totalRecommended;

  // Calculate overall statistics
  const totalArticles = feeds.reduce((sum, feed) => sum + (feed.total_articles || 0), 0);
  const totalArticlesThisWeek = feeds.reduce(
    (sum, feed) => sum + (feed.articles_this_week || 0),
    0
  );
  const avgTinkeringIndex =
    feeds.reduce((sum, feed) => sum + (feed.average_tinkering_index || 0), 0) / feeds.length || 0;

  return (
    <div className="max-w-6xl mx-auto py-6 space-y-6">
      <div className="flex flex-col gap-1">
        <h1 className="text-3xl font-bold">{t('subscriptions.title')}</h1>
        <p className="text-muted-foreground">
          {t('subscriptions.description', {
            subscribed: totalSubscribed,
            total: (feeds || []).length,
          })}
        </p>
      </div>

      <Tabs
        value={currentTab}
        onValueChange={(value) => setCurrentTab(value as 'subscriptions' | 'explore')}
      >
        <TabsList>
          <TabsTrigger value="subscriptions">{t('subscriptions.my-subscriptions')}</TabsTrigger>
          <TabsTrigger value="explore">{t('subscriptions.explore')}</TabsTrigger>
        </TabsList>

        <TabsContent value="subscriptions" className="space-y-4 mt-4">
          <FeedStatistics
            totalArticles={totalArticles}
            articlesThisWeek={totalArticlesThisWeek}
            averageTinkeringIndex={avgTinkeringIndex}
          />
          <HealthStatsGrid feeds={feeds} subscribed />
          <FeedSearch
            feeds={feeds.filter((f) => f.is_subscribed)}
            onFilteredFeedsChange={handleFilteredFeedsChange}
          />
        </TabsContent>

        <TabsContent value="explore" className="space-y-4 mt-4">
          <FeedStatistics
            totalArticles={totalArticles}
            articlesThisWeek={totalArticlesThisWeek}
            averageTinkeringIndex={avgTinkeringIndex}
          />
          <HealthStatsGrid feeds={feeds} />

          {/* Recommended feeds quick-subscribe banner */}
          {!allRecommendedSubscribed && (
            <Card className="border-primary/30 bg-primary/5">
              <CardContent className="p-4 flex flex-col sm:flex-row sm:items-center gap-3">
                <div className="flex-1">
                  <p className="font-medium flex items-center gap-2">
                    <Star className="w-4 h-4 text-yellow-500 fill-yellow-500" />
                    {t('subscriptions.recommended-banner-title')}
                  </p>
                  <p className="text-sm text-muted-foreground mt-0.5">
                    {t('subscriptions.recommended-banner-desc', {
                      count: totalRecommended - recommendedSubscribed,
                    })}
                  </p>
                </div>
                <Button
                  onClick={handleSubscribeRecommended}
                  disabled={toggling.size > 0}
                  className="shrink-0"
                >
                  {t('subscriptions.subscribe-all-recommended')}
                </Button>
              </CardContent>
            </Card>
          )}

          <div className="flex flex-wrap items-center gap-2">
            <Button
              variant="outline"
              onClick={() => handleToggleAll(true)}
              disabled={allSubscribed || toggling.size > 0}
            >
              {t('subscriptions.subscribe-all')}
            </Button>
            <Button
              variant="outline"
              onClick={() => handleToggleAll(false)}
              disabled={noneSubscribed || toggling.size > 0}
            >
              {t('subscriptions.unsubscribe-all')}
            </Button>
            <Button
              variant="outline"
              onClick={handleRetryFailedFeeds}
              disabled={
                feeds.filter((f) => f.health_status === 'error').length === 0 || toggling.size > 0
              }
              className="gap-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                />
              </svg>
              {t('subscriptions.retry-failed')}
            </Button>
            <div className="flex-1" />
            {/* Advanced: manual add & OPML import */}
            <AddCustomFeedDialog
              onAddFeed={handleAddCustomFeed}
              onPreviewFeed={handlePreviewFeed}
            />
            <OPMLImportExport feeds={feeds} onImport={handleOPMLImport} />
          </div>
          <FeedSearch feeds={feeds} onFilteredFeedsChange={handleFilteredFeedsChange} />
        </TabsContent>
      </Tabs>

      {error && (
        <div className="p-4 bg-destructive/10 border border-destructive/20 rounded-lg text-destructive text-sm">
          {error}
        </div>
      )}

      <div className="space-y-4">
        {sortedCategories.map((category) => {
          const categoryFeeds = feedsByCategory[category];
          const subscribedCount = categoryFeeds.filter((f) => f.is_subscribed).length;
          const allCategorySubscribed = subscribedCount === categoryFeeds.length;
          const noneCategorySubscribed = subscribedCount === 0;
          const isCollapsed = collapsedCategories.has(category);
          const hasRecommended = categoryFeeds.some((f) => f.is_recommended);

          return (
            <Card key={category}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <button
                    onClick={() => toggleCategoryCollapse(category)}
                    className="flex items-center gap-2 flex-1 text-left hover:opacity-80 transition-opacity"
                  >
                    {isCollapsed ? (
                      <ChevronRight className="w-5 h-5" />
                    ) : (
                      <ChevronDown className="w-5 h-5" />
                    )}
                    <div>
                      <div className="flex items-center gap-2">
                        <CardTitle>{category}</CardTitle>
                        {hasRecommended && (
                          <Badge variant="secondary" className="gap-1">
                            <Star className="w-3 h-3" />
                            {t('ui.recommended')}
                          </Badge>
                        )}
                      </div>
                      <CardDescription>
                        {subscribedCount} / {categoryFeeds.length}{' '}
                        {t('subscriptions.subscribed-simple')}
                      </CardDescription>
                    </div>
                  </button>
                  {!isCollapsed && (
                    <div className="flex gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleCategoryToggle(category, true)}
                        disabled={allCategorySubscribed || toggling.size > 0}
                      >
                        {t('ui.select-all')}
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleCategoryToggle(category, false)}
                        disabled={noneCategorySubscribed || toggling.size > 0}
                      >
                        {t('ui.deselect-all')}
                      </Button>
                    </div>
                  )}
                </div>
              </CardHeader>
              {!isCollapsed && (
                <CardContent className="animate-in slide-in-from-top-2 duration-300">
                  <div className="space-y-3">
                    {categoryFeeds.map((feed) => (
                      <div
                        key={feed.id}
                        className="flex flex-col sm:flex-row sm:items-start space-y-3 sm:space-y-0 sm:space-x-3 p-4 rounded-lg hover:bg-muted/50 transition-colors border border-transparent hover:border-muted"
                      >
                        <div className="flex items-start space-x-3 flex-1">
                          <Checkbox
                            id={feed.id}
                            checked={feed.is_subscribed}
                            onCheckedChange={() => handleToggle(feed.id)}
                            disabled={toggling.has(feed.id)}
                            className="mt-1 flex-shrink-0"
                          />
                          <div className="flex-1 min-w-0">
                            <label htmlFor={feed.id} className="cursor-pointer block">
                              <div className="flex items-center gap-2 flex-wrap">
                                <span className="font-medium">{feed.name}</span>
                                {feed.is_recommended && (
                                  <Badge variant="outline" className="text-xs">
                                    {t('ui.recommended')}
                                  </Badge>
                                )}
                                {feed.is_custom && (
                                  <Badge variant="secondary" className="text-xs">
                                    {t('subscriptions.custom-feed')}
                                  </Badge>
                                )}
                                {feed.tags && feed.tags.length > 0 && (
                                  <>
                                    {feed.tags.map((tag) => (
                                      <Badge key={tag} variant="secondary" className="text-xs">
                                        {tag}
                                      </Badge>
                                    ))}
                                  </>
                                )}
                              </div>
                              {feed.description && (
                                <div className="text-sm text-muted-foreground mt-1">
                                  {feed.description}
                                </div>
                              )}
                              <div className="text-sm text-muted-foreground mt-1 break-all">
                                {feed.url}
                              </div>
                            </label>

                            {/* Feed Health and Statistics - Stacked on mobile */}
                            <div className="mt-3 flex flex-col sm:flex-row sm:flex-wrap sm:items-center gap-2 sm:gap-3">
                              {feed.health_status && (
                                <FeedHealthIndicator
                                  lastUpdateTime={feed.last_updated ?? undefined}
                                  status={feed.health_status || 'unknown'}
                                  errorMessage={feed.error_message}
                                />
                              )}

                              {feed.is_subscribed && (
                                <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-3">
                                  <div className="flex flex-wrap gap-2">
                                    {feed.total_articles !== undefined && (
                                      <Badge variant="outline" className="text-xs">
                                        {feed.total_articles} {t('ui.articles')}
                                      </Badge>
                                    )}
                                    {feed.articles_this_week !== undefined && (
                                      <Badge variant="outline" className="text-xs">
                                        {t('ui.articles-this-week', {
                                          count: feed.articles_this_week,
                                        })}
                                      </Badge>
                                    )}
                                    {feed.average_tinkering_index !== undefined && (
                                      <Badge
                                        variant="outline"
                                        className="text-xs flex items-center gap-1"
                                      >
                                        <div className="flex">
                                          {Array.from({ length: 5 }).map((_, i) => (
                                            <Star
                                              key={i}
                                              className={`w-2.5 h-2.5 ${
                                                i < Math.floor(feed.average_tinkering_index!)
                                                  ? 'fill-yellow-400 text-yellow-400'
                                                  : 'text-gray-300'
                                              }`}
                                            />
                                          ))}
                                        </div>
                                        {feed.average_tinkering_index.toFixed(1)}
                                      </Badge>
                                    )}
                                  </div>

                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() =>
                                      toggleNotification(
                                        feed.id,
                                        feed.notification_enabled || false
                                      )
                                    }
                                    className="h-7 gap-1 self-start sm:self-auto"
                                  >
                                    {feed.notification_enabled ? (
                                      <>
                                        <Bell className="w-3 h-3" />
                                        <span className="text-xs">
                                          {t('subscriptions.notification-enabled')}
                                        </span>
                                      </>
                                    ) : (
                                      <>
                                        <BellOff className="w-3 h-3" />
                                        <span className="text-xs">
                                          {t('subscriptions.enable-notification')}
                                        </span>
                                      </>
                                    )}
                                  </Button>
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                        {toggling.has(feed.id) ? (
                          <div className="h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent flex-shrink-0 mt-1 self-start sm:self-auto" />
                        ) : feed.is_custom ? (
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-7 w-7 text-muted-foreground hover:text-destructive flex-shrink-0"
                            onClick={() => handleDeleteFeed(feed.id, feed.name)}
                            aria-label={t('subscriptions.delete-feed')}
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </Button>
                        ) : null}
                      </div>
                    ))}
                  </div>
                </CardContent>
              )}
            </Card>
          );
        })}
      </div>

      {filteredFeeds.length === 0 && !loading && (
        <div className="text-center py-12">
          <p className="text-muted-foreground">{t('subscriptions.no-feeds-found')}</p>
        </div>
      )}
    </div>
  );
}
