'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { fetchFeeds, toggleSubscription } from '@/lib/api/feeds';
import type { Feed } from '@/types/feed';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';

export default function SubscriptionsPage() {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const router = useRouter();
  const [feeds, setFeeds] = useState<Feed[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [toggling, setToggling] = useState<string | null>(null);

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
      setFeeds(data);
    } catch (err) {
      console.error('Failed to load feeds:', err);
      setError('無法載入訂閱來源');
    } finally {
      setLoading(false);
    }
  };

  const handleToggle = async (feedId: string) => {
    try {
      setToggling(feedId);
      const result = await toggleSubscription(feedId);

      // Update local state
      setFeeds(
        feeds.map((feed) =>
          feed.id === result.feed_id
            ? { ...feed, is_subscribed: result.is_subscribed }
            : feed,
        ),
      );
    } catch (err) {
      console.error('Failed to toggle subscription:', err);
      setError('訂閱操作失敗');
    } finally {
      setToggling(null);
    }
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
  const feedsByCategory = feeds.reduce(
    (acc, feed) => {
      if (!acc[feed.category]) {
        acc[feed.category] = [];
      }
      acc[feed.category].push(feed);
      return acc;
    },
    {} as Record<string, Feed[]>,
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-background to-muted p-4">
      <div className="max-w-4xl mx-auto py-8">
        <div className="mb-8">
          <Button
            variant="outline"
            onClick={() => router.push('/dashboard')}
            className="mb-4"
          >
            ← 返回 Dashboard
          </Button>
          <h1 className="text-3xl font-bold">訂閱管理</h1>
          <p className="text-muted-foreground mt-2">
            選擇您想要訂閱的 RSS 來源
          </p>
        </div>

        {error && (
          <div className="mb-4 p-4 bg-destructive/10 border border-destructive/20 rounded-lg text-destructive">
            {error}
          </div>
        )}

        <div className="space-y-6">
          {Object.entries(feedsByCategory).map(([category, categoryFeeds]) => (
            <Card key={category}>
              <CardHeader>
                <CardTitle>{category}</CardTitle>
                <CardDescription>
                  {categoryFeeds.filter((f) => f.is_subscribed).length} /{' '}
                  {categoryFeeds.length} 已訂閱
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {categoryFeeds.map((feed) => (
                    <div
                      key={feed.id}
                      className="flex items-center space-x-3 p-3 rounded-lg hover:bg-muted/50 transition-colors"
                    >
                      <Checkbox
                        id={feed.id}
                        checked={feed.is_subscribed}
                        onCheckedChange={() => handleToggle(feed.id)}
                        disabled={toggling === feed.id}
                      />
                      <label
                        htmlFor={feed.id}
                        className="flex-1 cursor-pointer"
                      >
                        <div className="font-medium">{feed.name}</div>
                        <div className="text-sm text-muted-foreground">
                          {feed.url}
                        </div>
                      </label>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}
