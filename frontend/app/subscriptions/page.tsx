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
  const [collapsedCategories, setCollapsedCategories] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/');
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

  const toggleCategoryCollapse = (category: string) => {
    setCollapsedCategories((prev) => {
      const next = new Set(prev);
      if (next.has(category)) {
        next.delete(category);
      } else {
        next.add(category);
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
          <Button variant="outline" onClick={() => router.push('/dashboard')} className="mb-4">
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
                  <CardContent>
                    <div className="space-y-3">
                      {categoryFeeds.map((feed) => (
                        <div
                          key={feed.id}
                          className="flex items-start space-x-3 p-4 rounded-lg hover:bg-muted/50 transition-colors border border-transparent hover:border-muted"
                        >
                          <Checkbox
                            id={feed.id}
                            checked={feed.is_subscribed}
                            onCheckedChange={() => handleToggle(feed.id)}
                            disabled={toggling.has(feed.id)}
                            className="mt-1"
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

                            {/* Feed Health and Statistics */}
                            <div className="mt-3 flex flex-wrap items-center gap-3">
                              {feed.last_updated && (
                                <FeedHealthIndicator
                                  lastUpdateTime={feed.last_updated}
                                  status={feed.health_status || 'unknown'}
                                  errorMessage={feed.error_message}
                                />
                              )}

                              {feed.is_subscribed && (
                                <>
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
                                    <Badge variant="outline" className="text-xs">
                                      平均深度 {feed.average_tinkering_index.toFixed(1)}
                                    </Badge>
                                  )}

                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() =>
                                      toggleNotification(
                                        feed.id,
                                        feed.notification_enabled || false
                                      )
                                    }
                                    className="h-7 gap-1"
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
                                </>
                              )}
                            </div>
                          </div>
                          {toggling.has(feed.id) && (
                            <div className="h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent flex-shrink-0 mt-1" />
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
