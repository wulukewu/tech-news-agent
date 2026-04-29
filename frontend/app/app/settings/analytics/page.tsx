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
          <h1 className="text-2xl font-bold">{t('nav.analytics')}</h1>
          <p className="text-muted-foreground text-sm">查看您的閱讀統計和活動分析</p>
        </div>
        <Button variant="outline" size="sm" onClick={loadStats} disabled={loading}>
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          重新整理
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
                <CardTitle className="text-sm font-medium">總訂閱數</CardTitle>
                <Rss className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats?.subscriptions_count || 0}</div>
                <p className="text-xs text-muted-foreground">RSS 來源</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">閱讀清單</CardTitle>
                <BookMarked className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats?.reading_list_count || 0}</div>
                <p className="text-xs text-muted-foreground">已收藏文章</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">已讀文章</CardTitle>
                <BarChart3 className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats?.articles_read_count || 0}</div>
                <p className="text-xs text-muted-foreground">完成閱讀</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">閱讀完成率</CardTitle>
                <TrendingUp className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{readingRate}%</div>
                <p className="text-xs text-muted-foreground">
                  {stats?.reading_list_count || 0} 篇中已讀 {stats?.articles_read_count || 0} 篇
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
                  閱讀目標
                </CardTitle>
                <CardDescription>您的閱讀習慣分析</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>閱讀進度</span>
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
                    <p>優秀！您的閱讀完成率很高</p>
                  ) : readingRate >= 50 ? (
                    <p>不錯！繼續保持閱讀習慣</p>
                  ) : readingRate > 0 ? (
                    <p>開始閱讀了！試著完成更多文章</p>
                  ) : (
                    <p>開始您的閱讀之旅吧</p>
                  )}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Calendar className="h-5 w-5" />
                  活動摘要
                </CardTitle>
                <CardDescription>您的平台使用情況</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm">訂閱來源</span>
                    <span className="font-medium">{stats?.subscriptions_count || 0} 個</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">收藏文章</span>
                    <span className="font-medium">{stats?.reading_list_count || 0} 篇</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">完成閱讀</span>
                    <span className="font-medium">{stats?.articles_read_count || 0} 篇</span>
                  </div>
                </div>

                <div className="pt-2 border-t">
                  <p className="text-xs text-muted-foreground">
                    平均每個來源收藏{' '}
                    {stats?.subscriptions_count
                      ? Math.round((stats.reading_list_count || 0) / stats.subscriptions_count)
                      : 0}{' '}
                    篇文章
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Future Features */}
          <Card>
            <CardHeader>
              <CardTitle>進階分析功能</CardTitle>
              <CardDescription>即將推出的功能</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3 text-sm text-muted-foreground">
                <div>閱讀時間趨勢</div>
                <div>分類偏好分析</div>
                <div>每週/每月報告</div>
                <div>個人化推薦</div>
                <div>閱讀時段分析</div>
                <div>熱門文章追蹤</div>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
