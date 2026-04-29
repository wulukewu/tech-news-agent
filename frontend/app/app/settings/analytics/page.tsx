'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { RefreshCw, BookMarked, Rss, BarChart3, TrendingUp, Calendar, Target } from 'lucide-react';
import { apiClient } from '@/lib/api/client';
import { useI18n } from '@/contexts/I18nContext';

interface UserStats {
  reading_list_count: number;
  subscriptions_count: number;
  articles_read_count: number;
}

export default function AnalyticsSettingsPage() {
  const { t } = useI18n();
  const [stats, setStats] = useState<UserStats | null>(null);
  const [loading, setLoading] = useState(true);

  const loadStats = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get<UserStats>('/api/auth/me/stats');
      setStats(response.data);
    } catch (error) {
      console.error('Failed to load stats:', error);
      setStats({ reading_list_count: 0, subscriptions_count: 0, articles_read_count: 0 });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStats();
  }, []);

  const readingRate = stats
    ? stats.reading_list_count > 0
      ? Math.round((stats.articles_read_count / stats.reading_list_count) * 100)
      : 0
    : 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{t('pages.analytics.title')}</h1>
          <p className="text-muted-foreground text-sm">{t('pages.analytics.description')}</p>
        </div>
        <Button variant="outline" size="sm" onClick={loadStats} disabled={loading}>
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          {t('pages.analytics.refresh')}
        </Button>
      </div>

      {loading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <Card key={i}>
              <CardContent className="pt-6">
                <Skeleton className="h-16 w-full" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <>
          {/* Key Metrics */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  {t('pages.analytics.total-subscriptions')}
                </CardTitle>
                <Rss className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats?.subscriptions_count || 0}</div>
                <p className="text-xs text-muted-foreground">{t('pages.analytics.rss-sources')}</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  {t('pages.analytics.reading-list')}
                </CardTitle>
                <BookMarked className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats?.reading_list_count || 0}</div>
                <p className="text-xs text-muted-foreground">
                  {t('pages.analytics.saved-articles')}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  {t('pages.analytics.articles-read')}
                </CardTitle>
                <BarChart3 className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats?.articles_read_count || 0}</div>
                <p className="text-xs text-muted-foreground">
                  {t('pages.analytics.completed-reading')}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  {t('pages.analytics.reading-completion-rate')}
                </CardTitle>
                <TrendingUp className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{readingRate}%</div>
                <p className="text-xs text-muted-foreground">
                  {t('pages.analytics.articles-progress', {
                    total: stats?.reading_list_count || 0,
                    read: stats?.articles_read_count || 0,
                  })}
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Reading Insights */}
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Target className="h-5 w-5" />
                  {t('pages.analytics.reading-goals')}
                </CardTitle>
                <CardDescription>{t('pages.analytics.reading-habits-analysis')}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>{t('pages.analytics.reading-progress')}</span>
                    <span>{readingRate}%</span>
                  </div>
                  <div className="w-full bg-secondary rounded-full h-2">
                    <div
                      className="bg-primary h-2 rounded-full transition-all duration-300"
                      style={{ width: `${Math.min(readingRate, 100)}%` }}
                    />
                  </div>
                </div>

                <div className="text-sm text-muted-foreground">
                  {readingRate >= 80 ? (
                    <p>{t('pages.analytics.excellent-completion')}</p>
                  ) : readingRate >= 50 ? (
                    <p>{t('pages.analytics.good-progress')}</p>
                  ) : readingRate > 0 ? (
                    <p>{t('pages.analytics.getting-started')}</p>
                  ) : (
                    <p>{t('pages.analytics.start-journey')}</p>
                  )}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Calendar className="h-5 w-5" />
                  {t('pages.analytics.activity-summary')}
                </CardTitle>
                <CardDescription>{t('pages.analytics.platform-usage')}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm">{t('pages.analytics.subscription-sources')}</span>
                    <span className="font-medium">
                      {stats?.subscriptions_count || 0} {t('pages.analytics.sources-unit')}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">{t('pages.analytics.saved-articles-count')}</span>
                    <span className="font-medium">
                      {stats?.reading_list_count || 0} {t('pages.analytics.articles-unit')}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">{t('pages.analytics.completed-reading-count')}</span>
                    <span className="font-medium">
                      {stats?.articles_read_count || 0} {t('pages.analytics.articles-unit')}
                    </span>
                  </div>
                </div>

                <div className="pt-2 border-t">
                  <p className="text-xs text-muted-foreground">
                    {t('pages.analytics.average-per-source', {
                      count: stats?.subscriptions_count
                        ? Math.round((stats.reading_list_count || 0) / stats.subscriptions_count)
                        : 0,
                    })}
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Future Features */}
          <Card>
            <CardHeader>
              <CardTitle>{t('pages.analytics.advanced-features')}</CardTitle>
              <CardDescription>{t('pages.analytics.coming-soon-features')}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3 text-sm text-muted-foreground">
                <div>{t('pages.analytics.reading-time-trends')}</div>
                <div>{t('pages.analytics.category-preferences')}</div>
                <div>{t('pages.analytics.weekly-monthly-reports')}</div>
                <div>{t('pages.analytics.personalized-recommendations')}</div>
                <div>{t('pages.analytics.reading-time-analysis')}</div>
                <div>{t('pages.analytics.trending-articles')}</div>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
