'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { RefreshButton } from '@/components/ui/refresh-button';
import { Skeleton } from '@/components/ui/skeleton';
import { BookMarked, Rss, BarChart3, TrendingUp, Calendar, Target } from 'lucide-react';
import { apiClient } from '@/lib/api/client';
import { useI18n } from '@/contexts/I18nContext';
import { AnimatedCounter } from '@/components/ui/animated-counter';

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
      <div className="flex items-center justify-between animate-in fade-in slide-in-from-top-2 duration-300">
        <div>
          <h1 className="text-2xl font-bold">{t('pages.analytics.title')}</h1>
          <p className="text-muted-foreground text-sm">{t('pages.analytics.description')}</p>
        </div>
        <RefreshButton isLoading={loading} onClick={loadStats}>
          {t('pages.analytics.refresh')}
        </RefreshButton>
      </div>

      {loading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <Card
              key={i}
              className="animate-in fade-in duration-300"
              style={{ animationDelay: `${i * 50}ms` }}
            >
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
            {[
              {
                title: t('pages.analytics.total-subscriptions'),
                value: stats?.subscriptions_count || 0,
                desc: t('pages.analytics.rss-sources'),
                icon: Rss,
                suffix: '',
              },
              {
                title: t('pages.analytics.reading-list'),
                value: stats?.reading_list_count || 0,
                desc: t('pages.analytics.saved-articles'),
                icon: BookMarked,
                suffix: '',
              },
              {
                title: t('pages.analytics.articles-read'),
                value: stats?.articles_read_count || 0,
                desc: t('pages.analytics.completed-reading'),
                icon: BarChart3,
                suffix: '',
              },
              {
                title: t('pages.analytics.reading-completion-rate'),
                value: readingRate,
                desc: t('pages.analytics.articles-progress', {
                  total: stats?.reading_list_count || 0,
                  read: stats?.articles_read_count || 0,
                }),
                icon: TrendingUp,
                suffix: '%',
              },
            ].map((metric, index) => {
              const Icon = metric.icon;
              return (
                <Card
                  key={index}
                  className="animate-in fade-in slide-in-from-bottom-2 duration-300 hover-spring active-tap"
                  style={{ animationDelay: `${index * 50}ms` }}
                >
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">{metric.title}</CardTitle>
                    <div className="p-1 rounded-lg bg-primary/10 text-primary transition-transform duration-200 group-hover:scale-[1.1]">
                      <Icon className="h-4 w-4 animate-pulse [animation-duration:3s]" />
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold transition-colors duration-200 group-hover:text-primary">
                      <AnimatedCounter value={metric.value} suffix={metric.suffix} />
                    </div>
                    <p className="text-xs text-muted-foreground">{metric.desc}</p>
                  </CardContent>
                </Card>
              );
            })}
          </div>

          {/* Reading Insights */}
          <div className="grid gap-4 md:grid-cols-2">
            <Card className="animate-in fade-in slide-in-from-bottom-2 duration-300 delay-75 hover-spring active-tap">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <div className="p-1 rounded-lg bg-primary/10 text-primary transition-transform duration-200 group-hover:scale-[1.1]">
                    <Target className="h-5 w-5" />
                  </div>
                  {t('pages.analytics.reading-goals')}
                </CardTitle>
                <CardDescription>{t('pages.analytics.reading-habits-analysis')}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>{t('pages.analytics.reading-progress')}</span>
                    <span className="font-medium">
                      <AnimatedCounter value={readingRate} suffix="%" />
                    </span>
                  </div>
                  <div className="w-full bg-secondary rounded-full h-2 overflow-hidden">
                    <div
                      className="bg-primary h-2 rounded-full transition-all duration-1000 ease-out"
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

            <Card className="animate-in fade-in slide-in-from-bottom-2 duration-300 delay-100 hover-spring active-tap">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <div className="p-1 rounded-lg bg-primary/10 text-primary transition-transform duration-200 group-hover:scale-[1.1]">
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
                      value: stats?.subscriptions_count || 0,
                      suffix: ` ${t('pages.analytics.sources-unit')}`,
                    },
                    {
                      label: t('pages.analytics.saved-articles-count'),
                      value: stats?.reading_list_count || 0,
                      suffix: ` ${t('pages.analytics.articles-unit')}`,
                    },
                    {
                      label: t('pages.analytics.completed-reading-count'),
                      value: stats?.articles_read_count || 0,
                      suffix: ` ${t('pages.analytics.articles-unit')}`,
                    },
                  ].map((item, index) => (
                    <div key={index} className="flex items-center justify-between">
                      <span className="text-sm">{item.label}</span>
                      <span className="font-medium">
                        <AnimatedCounter value={item.value} suffix={item.suffix} />
                      </span>
                    </div>
                  ))}
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
          <Card className="animate-in fade-in slide-in-from-bottom-2 duration-300 delay-150 hover-spring active-tap">
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
                    className="hover:text-foreground transition-colors cursor-default"
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
