'use client';

import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { fetchFeeds, toggleSubscription, addCustomFeed, previewFeed } from '@/lib/api/feeds';
import type { Feed } from '@/types/feed';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import { ChevronDown, ChevronRight, Star, Bell, BellOff } from 'lucide-react';
import { toast } from '@/lib/toast';
import { FeedHealthIndicator } from '@/features/subscriptions/components/FeedHealthIndicator';
import { FeedStatistics } from '@/features/subscriptions/components/FeedStatistics';
import { AddCustomFeedDialog } from '@/features/subscriptions/components/AddCustomFeedDialog';
import { OPMLImportExport } from '@/features/subscriptions/components/OPMLImportExport';
import { FeedSearch } from '@/features/subscriptions/components/FeedSearch';
import type { OPMLOutline } from '@/features/subscriptions/utils/opml';

export default function SubscriptionsPage() {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const router = useRouter();
  const [feeds, setFeeds] = useState<Feed[]>([]);
  const [filteredFeeds, setFilteredFeeds] = useState<Feed[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [toggling, setToggling] = useState<Set<string>>(new Set());
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
      setError('無法載入訂閱來源');
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

      // Update local state
      setFeeds(
        feeds.map((feed) =>
          feed.id === result.feed_id ? { ...feed, is_subscribed: result.is_subscribed } : feed
        )
      );
    } catch (err) {
      console.error('Failed to toggle subscription:', err);
      toast.error('訂閱操作失敗');
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

    try {
      setToggling((prev) => {
        const next = new Set(prev);
        feedsToToggle.forEach((f) => next.add(f.id));
        return next;
      });

      // Toggle all feeds in parallel
      await Promise.all(feedsToToggle.map((feed) => toggleSubscription(feed.id)));

      // Update local state
      setFeeds(
        feeds.map((feed) =>
          feed.category === category ? { ...feed, is_subscribed: subscribe } : feed
        )
      );

      toast.success(`已${subscribe ? '訂閱' : '取消訂閱'} ${feedsToToggle.length} 個來源`);
    } catch (err) {
      console.error('Failed to toggle category:', err);
      toast.error('批量操作失敗');
    } finally {
      setToggling((prev) => {
        const next = new Set(prev);
        feedsToToggle.forEach((f) => next.delete(f.id));
        return next;
      });
    }
  };

  const handleToggleAll = async (subscribe: boolean) => {
    const feedsToToggle = filteredFeeds.filter((f) => f.is_subscribed !== subscribe);

    if (feedsToToggle.length === 0) return;

    try {
      setToggling((prev) => {
        const next = new Set(prev);
        feedsToToggle.forEach((f) => next.add(f.id));
        return next;
      });

      // Toggle all feeds in parallel
      await Promise.all(feedsToToggle.map((feed) => toggleSubscription(feed.id)));

      // Update local state
      setFeeds(feeds.map((feed) => ({ ...feed, is_subscribed: subscribe })));

      toast.success(`已${subscribe ? '訂閱' : '取消訂閱'} ${feedsToToggle.length} 個來源`);
    } catch (err) {
      console.error('Failed to toggle all:', err);
      toast.error('批量操作失敗');
    } finally {
      setToggling(new Set());
    }
  };

  const handleSubscribeRecommended = async () => {
    const recommendedFeeds = feeds.filter((f) => f.is_recommended && !f.is_subscribed);

    if (recommendedFeeds.length === 0) {
      toast.info('您已訂閱所有推薦來源');
      return;
    }

    try {
      setToggling((prev) => {
        const next = new Set(prev);
        recommendedFeeds.forEach((f) => next.add(f.id));
        return next;
      });

      // Toggle all recommended feeds in parallel
      await Promise.all(recommendedFeeds.map((feed) => toggleSubscription(feed.id)));

      // Update local state
      setFeeds(
        feeds.map((feed) => (feed.is_recommended ? { ...feed, is_subscribed: true } : feed))
      );

      toast.success(`已訂閱 ${recommendedFeeds.length} 個推薦來源`);
    } catch (err) {
      console.error('Failed to subscribe recommended:', err);
      toast.error('訂閱推薦來源失敗');
    } finally {
      setToggling((prev) => {
        const next = new Set(prev);
        recommendedFeeds.forEach((f) => next.delete(f.id));
        return next;
      });
    }
  };

  const handleRetryFailedFeeds = async () => {
    const failedFeeds = feeds.filter((f) => f.health_status === 'error');

    if (failedFeeds.length === 0) {
      toast.info('沒有需要重試的失敗來源');
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

      toast.success(`已重試 ${failedFeeds.length} 個失敗的來源`);
    } catch (err) {
      console.error('Failed to retry feeds:', err);
      toast.error('重試失敗來源時發生錯誤');
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
          console.warn('Failed to save collapsed categories to localStorage:', error);
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
    setFilteredFeeds(filtered);
  }, []);

  const toggleNotification = async (feedId: string, currentState: boolean) => {
    // This would call the API to update notification preferences
    // For now, just update local state
    setFeeds(
      feeds.map((feed) =>
        feed.id === feedId ? { ...feed, notification_enabled: !currentState } : feed
      )
    );
    toast.success(`已${!currentState ? '啟用' : '停用'}通知`);
  };

  if (authLoading || loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">載入中...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  // Group feeds by category
  const feedsByCategory = (filteredFeeds || []).reduce(
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
    <div className="min-h-screen bg-gradient-to-br from-background to-muted p-4">
      <div className="max-w-6xl mx-auto py-8">
        <div className="mb-8">
          <Button
            variant="outline"
            onClick={() => router.push('/dashboard/articles')}
            className="mb-4"
          >
            ← 返回 Dashboard
          </Button>

          <div className="flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold">訂閱管理</h1>
                <p className="text-muted-foreground mt-2">
                  選擇您想要訂閱的 RSS 來源 ({totalSubscribed} / {(feeds || []).length} 已訂閱)
                </p>
              </div>
            </div>

            {/* Overall Statistics */}
            <FeedStatistics
              totalArticles={totalArticles}
              articlesThisWeek={totalArticlesThisWeek}
              averageTinkeringIndex={avgTinkeringIndex}
            />

            {/* Health Statistics Summary */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <Card className="border-green-200 dark:border-green-800">
                <CardContent className="p-3">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-green-500"></div>
                    <div>
                      <div className="text-xs text-muted-foreground">健康</div>
                      <div className="text-lg font-semibold text-green-600 dark:text-green-400">
                        {feeds.filter((f) => f.health_status === 'healthy').length}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
              <Card className="border-yellow-200 dark:border-yellow-800">
                <CardContent className="p-3">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                    <div>
                      <div className="text-xs text-muted-foreground">過時</div>
                      <div className="text-lg font-semibold text-yellow-600 dark:text-yellow-400">
                        {feeds.filter((f) => f.health_status === 'warning').length}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
              <Card className="border-red-200 dark:border-red-800">
                <CardContent className="p-3">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-red-500"></div>
                    <div>
                      <div className="text-xs text-muted-foreground">錯誤</div>
                      <div className="text-lg font-semibold text-red-600 dark:text-red-400">
                        {feeds.filter((f) => f.health_status === 'error').length}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
              <Card className="border-gray-200 dark:border-gray-800">
                <CardContent className="p-3">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-gray-500"></div>
                    <div>
                      <div className="text-xs text-muted-foreground">未知</div>
                      <div className="text-lg font-semibold text-gray-600 dark:text-gray-400">
                        {
                          feeds.filter((f) => f.health_status === 'unknown' || !f.health_status)
                            .length
                        }
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Action Bar */}
            <div className="flex flex-wrap items-center gap-2">
              <Button
                variant="default"
                onClick={handleSubscribeRecommended}
                disabled={allRecommendedSubscribed || toggling.size > 0}
                className="gap-2"
              >
                <Star className="w-4 h-4" />
                訂閱所有推薦
              </Button>
              <Button
                variant="outline"
                onClick={() => handleToggleAll(true)}
                disabled={allSubscribed || toggling.size > 0}
              >
                全部訂閱
              </Button>
              <Button
                variant="outline"
                onClick={() => handleToggleAll(false)}
                disabled={noneSubscribed || toggling.size > 0}
              >
                全部取消
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
                重試失敗來源
              </Button>

              <div className="flex-1" />

              <AddCustomFeedDialog
                onAddFeed={handleAddCustomFeed}
                onPreviewFeed={handlePreviewFeed}
              />

              <OPMLImportExport feeds={feeds} onImport={handleOPMLImport} />
            </div>

            {/* Search Bar */}
            <FeedSearch feeds={feeds} onFilteredFeedsChange={handleFilteredFeedsChange} />
          </div>
        </div>

        {error && (
          <div className="mb-4 p-4 bg-destructive/10 border border-destructive/20 rounded-lg text-destructive">
            {error}
          </div>
        )}

        <div className="space-y-6">
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
                              推薦
                            </Badge>
                          )}
                        </div>
                        <CardDescription>
                          {subscribedCount} / {categoryFeeds.length} 已訂閱
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
                          全選
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleCategoryToggle(category, false)}
                          disabled={noneCategorySubscribed || toggling.size > 0}
                        >
                          全不選
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
                                      推薦
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
                                {feed.last_updated && (
                                  <FeedHealthIndicator
                                    lastUpdateTime={feed.last_updated}
                                    status={feed.health_status || 'unknown'}
                                    errorMessage={feed.error_message}
                                  />
                                )}

                                {feed.is_subscribed && (
                                  <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-3">
                                    <div className="flex flex-wrap gap-2">
                                      {feed.total_articles !== undefined && (
                                        <Badge variant="outline" className="text-xs">
                                          {feed.total_articles} 篇文章
                                        </Badge>
                                      )}
                                      {feed.articles_this_week !== undefined && (
                                        <Badge variant="outline" className="text-xs">
                                          本週 {feed.articles_this_week} 篇
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
                                          <span className="text-xs">通知已啟用</span>
                                        </>
                                      ) : (
                                        <>
                                          <BellOff className="w-3 h-3" />
                                          <span className="text-xs">啟用通知</span>
                                        </>
                                      )}
                                    </Button>
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                          {toggling.has(feed.id) && (
                            <div className="h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent flex-shrink-0 mt-1 self-start sm:self-auto" />
                          )}
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
            <p className="text-muted-foreground">沒有找到符合條件的 Feed</p>
          </div>
        )}
      </div>
    </div>
  );
}
