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
      <div className="flex items-center justify-between animate-in fade-in slide-in-from-top-4 duration-500">
        <div>
          <h1 className="text-2xl font-bold">{t('pages.analytics.title')}</h1>
          <p className="text-muted-foreground text-sm">{t('pages.analytics.description')}</p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={loadStats}
          disabled={loading}
          className="transition-all duration-200 hover:scale-105 hover:shadow-md animate-in slide-in-from-right-4 duration-500 delay-200"
        >
          <RefreshCw
            className={`h-4 w-4 mr-2 transition-transform duration-200 ${loading ? 'animate-spin' : 'hover:rotate-180'}`}
          />
          {t('pages.analytics.refresh')}
        </Button>
      </div>

      {loading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <Card
              key={i}
              className="animate-in fade-in duration-500"
              style={{ animationDelay: `${i * 100}ms` }}
            >
              <CardContent className="pt-6">
                <Skeleton className="h-16 w-full animate-pulse" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <>
          {/* Key Metrics */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {[
              {
                title: t('pages.analytics.total-subscriptions'),
                value: stats?.subscriptions_count || 0,
                desc: t('pages.analytics.rss-sources'),
                icon: Rss,
              },
              {
                title: t('pages.analytics.reading-list'),
                value: stats?.reading_list_count || 0,
                desc: t('pages.analytics.saved-articles'),
                icon: BookMarked,
              },
              {
                title: t('pages.analytics.articles-read'),
                value: stats?.articles_read_count || 0,
                desc: t('pages.analytics.completed-reading'),
                icon: BarChart3,
              },
              {
                title: t('pages.analytics.reading-completion-rate'),
                value: `${readingRate}%`,
                desc: t('pages.analytics.articles-progress', {
                  total: stats?.reading_list_count || 0,
                  read: stats?.articles_read_count || 0,
                }),
                icon: TrendingUp,
              },
            ].map((metric, index) => {
              const Icon = metric.icon;
              return (
                <Card
                  key={index}
                  className="animate-in fade-in slide-in-from-bottom-4 duration-500 hover:shadow-lg hover:-translate-y-1 transition-all group"
                  style={{ animationDelay: `${300 + index * 150}ms` }}
                >
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">{metric.title}</CardTitle>
                    <div className="p-1 rounded-lg bg-primary/10 text-primary group-hover:scale-110 transition-transform duration-200">
                      <Icon className="h-4 w-4 animate-pulse" />
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold transition-colors duration-200 group-hover:text-primary">
                      {metric.value}
                    </div>
                    <p className="text-xs text-muted-foreground">{metric.desc}</p>
                  </CardContent>
                </Card>
              );
            })}
          </div>

          {/* Reading Insights */}
          <div className="grid gap-4 md:grid-cols-2">
            <Card className="animate-in fade-in slide-in-from-left-4 duration-500 delay-700 hover:shadow-lg transition-all">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <div className="p-1 rounded-lg bg-primary/10 text-primary animate-in zoom-in-50 duration-300 delay-800 hover:scale-110 transition-transform">
                    <Target className="h-5 w-5" />
                  </div>
                  {t('pages.analytics.reading-goals')}
                </CardTitle>
                <CardDescription>{t('pages.analytics.reading-habits-analysis')}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2 animate-in slide-in-from-bottom-2 duration-500 delay-900">
                  <div className="flex justify-between text-sm">
                    <span>{t('pages.analytics.reading-progress')}</span>
                    <span className="font-medium">{readingRate}%</span>
                  </div>
                  <div className="w-full bg-secondary rounded-full h-2 overflow-hidden">
                    <div
                      className="bg-primary h-2 rounded-full transition-all duration-1000 animate-in slide-in-from-left-full"
                      style={{ width: `${Math.min(readingRate, 100)}%`, animationDelay: '1000ms' }}
                    />
                  </div>
                </div>

                <div className="text-sm text-muted-foreground animate-in fade-in duration-500 delay-1100">
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

            <Card className="animate-in fade-in slide-in-from-right-4 duration-500 delay-800 hover:shadow-lg transition-all">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <div className="p-1 rounded-lg bg-primary/10 text-primary animate-in zoom-in-50 duration-300 delay-900 hover:scale-110 transition-transform">
                    <Calendar className="h-5 w-5" />
                  </div>
                  {t('pages.analytics.activity-summary')}
                </CardTitle>
                <CardDescription>{t('pages.analytics.platform-usage')}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  {[
                    {
                      label: t('pages.analytics.subscription-sources'),
                      value: `${stats?.subscriptions_count || 0} ${t('pages.analytics.sources-unit')}`,
                    },
                    {
                      label: t('pages.analytics.saved-articles-count'),
                      value: `${stats?.reading_list_count || 0} ${t('pages.analytics.articles-unit')}`,
                    },
                    {
                      label: t('pages.analytics.completed-reading-count'),
                      value: `${stats?.articles_read_count || 0} ${t('pages.analytics.articles-unit')}`,
                    },
                  ].map((item, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between animate-in slide-in-from-right-2 duration-300"
                      style={{ animationDelay: `${1000 + index * 100}ms` }}
                    >
                      <span className="text-sm">{item.label}</span>
                      <span className="font-medium">{item.value}</span>
                    </div>
                  ))}
                </div>

                <div className="pt-2 border-t animate-in fade-in duration-500 delay-1300">
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
          <Card className="animate-in fade-in slide-in-from-bottom-4 duration-500 delay-1000 hover:shadow-lg transition-all">
            <CardHeader>
              <CardTitle>{t('pages.analytics.advanced-features')}</CardTitle>
              <CardDescription>{t('pages.analytics.coming-soon-features')}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3 text-sm text-muted-foreground">
                {[
                  t('pages.analytics.reading-time-trends'),
                  t('pages.analytics.category-preferences'),
                  t('pages.analytics.weekly-monthly-reports'),
                  t('pages.analytics.personalized-recommendations'),
                  t('pages.analytics.reading-time-analysis'),
                  t('pages.analytics.trending-articles'),
                ].map((feature, index) => (
                  <div
                    key={index}
                    className="animate-in slide-in-from-left-2 duration-300 hover:text-foreground transition-colors cursor-default"
                    style={{ animationDelay: `${1200 + index * 100}ms` }}
                  >
                    • {feature}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
