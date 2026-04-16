'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { FeedNotificationSettings as FeedSettings } from '@/types/notification';
import { getAvailableFeeds } from '@/lib/api/notifications';
import { Rss, Plus, X, Star } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Slider } from '@/components/ui/slider';

interface FeedNotificationSettingsProps {
  feedSettings: FeedSettings[];
  onFeedSettingsChange: (feedSettings: FeedSettings[]) => void;
  disabled?: boolean;
}

export function FeedNotificationSettings({
  feedSettings,
  onFeedSettingsChange,
  disabled = false,
}: FeedNotificationSettingsProps) {
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  const { data: availableFeeds, isLoading } = useQuery({
    queryKey: ['availableFeeds'],
    queryFn: getAvailableFeeds,
  });

  const handleToggleFeed = (feedId: string, enabled: boolean) => {
    const existingIndex = feedSettings.findIndex((s) => s.feedId === feedId);

    if (existingIndex >= 0) {
      const updated = [...feedSettings];
      updated[existingIndex] = { ...updated[existingIndex], enabled };
      onFeedSettingsChange(updated);
    } else {
      onFeedSettingsChange([...feedSettings, { feedId, enabled, minTinkeringIndex: 3 }]);
    }
  };

  const handleUpdateThreshold = (feedId: string, minTinkeringIndex: number) => {
    const existingIndex = feedSettings.findIndex((s) => s.feedId === feedId);

    if (existingIndex >= 0) {
      const updated = [...feedSettings];
      updated[existingIndex] = { ...updated[existingIndex], minTinkeringIndex };
      onFeedSettingsChange(updated);
    }
  };

  const handleRemoveFeed = (feedId: string) => {
    onFeedSettingsChange(feedSettings.filter((s) => s.feedId !== feedId));
  };

  const getFeedSetting = (feedId: string) => {
    return feedSettings.find((s) => s.feedId === feedId);
  };

  const getFeedName = (feedId: string) => {
    return availableFeeds?.find((f) => f.id === feedId)?.name || feedId;
  };

  const getFeedCategory = (feedId: string) => {
    return availableFeeds?.find((f) => f.id === feedId)?.category || '';
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Rss className="h-5 w-5" />
          個別來源通知設定
        </CardTitle>
        <CardDescription>為特定 RSS 來源或分類設定通知偏好</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Configured Feeds */}
        {feedSettings.length > 0 ? (
          <div className="space-y-3">
            {feedSettings.map((setting) => {
              if (!setting.feedId) return null;

              return (
                <div
                  key={setting.feedId}
                  className="flex items-center justify-between rounded-lg border p-4"
                >
                  <div className="flex-1 space-y-2">
                    <div className="flex items-center gap-2">
                      <Label className="font-medium">{getFeedName(setting.feedId)}</Label>
                      {getFeedCategory(setting.feedId) && (
                        <Badge variant="secondary" className="text-xs">
                          {getFeedCategory(setting.feedId)}
                        </Badge>
                      )}
                    </div>

                    {setting.enabled && setting.minTinkeringIndex !== undefined && (
                      <div className="space-y-2">
                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                          <span>最低技術深度:</span>
                          <div className="flex items-center gap-1">
                            {Array.from({ length: setting.minTinkeringIndex }).map((_, i) => (
                              <Star key={i} className="h-3 w-3 fill-yellow-400 text-yellow-400" />
                            ))}
                          </div>
                        </div>
                        <Slider
                          value={[setting.minTinkeringIndex]}
                          onValueChange={([value]) => handleUpdateThreshold(setting.feedId!, value)}
                          min={1}
                          max={5}
                          step={1}
                          disabled={disabled}
                          className="w-full max-w-xs"
                        />
                      </div>
                    )}
                  </div>

                  <div className="flex items-center gap-2">
                    <Switch
                      checked={setting.enabled}
                      onCheckedChange={(checked) => handleToggleFeed(setting.feedId!, checked)}
                      disabled={disabled}
                    />
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleRemoveFeed(setting.feedId!)}
                      disabled={disabled}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="text-center py-8 text-muted-foreground">
            <Rss className="h-12 w-12 mx-auto mb-2 opacity-50" />
            <p>尚未設定個別來源通知</p>
            <p className="text-sm">點擊下方按鈕新增來源</p>
          </div>
        )}

        {/* Add Feed Dialog */}
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button variant="outline" className="w-full" disabled={disabled}>
              <Plus className="mr-2 h-4 w-4" />
              新增來源通知設定
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>選擇 RSS 來源</DialogTitle>
              <DialogDescription>為特定來源設定通知偏好</DialogDescription>
            </DialogHeader>

            {isLoading ? (
              <div className="flex items-center justify-center py-8">
                <LoadingSpinner size="lg" />
              </div>
            ) : (
              <div className="space-y-2">
                {availableFeeds?.map((feed) => {
                  const isConfigured = feedSettings.some((s) => s.feedId === feed.id);

                  return (
                    <div
                      key={feed.id}
                      className="flex items-center justify-between rounded-lg border p-3 hover:bg-accent/50 transition-colors"
                    >
                      <div className="flex-1">
                        <p className="font-medium">{feed.name}</p>
                        <p className="text-sm text-muted-foreground">{feed.category}</p>
                      </div>
                      <Button
                        variant={isConfigured ? 'secondary' : 'default'}
                        size="sm"
                        onClick={() => {
                          if (!isConfigured) {
                            handleToggleFeed(feed.id, true);
                          }
                          setIsDialogOpen(false);
                        }}
                        disabled={isConfigured}
                      >
                        {isConfigured ? '已設定' : '新增'}
                      </Button>
                    </div>
                  );
                })}
              </div>
            )}
          </DialogContent>
        </Dialog>
      </CardContent>
    </Card>
  );
}
