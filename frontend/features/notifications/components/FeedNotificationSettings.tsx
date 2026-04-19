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
import { useI18n } from '@/contexts/I18nContext';

interface FeedNotificationSettingsProps {
  feedSettings?: FeedSettings[];
  onFeedSettingsChange: (feedSettings: FeedSettings[]) => void;
  disabled?: boolean;
}

export function FeedNotificationSettings({
  feedSettings,
  onFeedSettingsChange,
  disabled = false,
}: FeedNotificationSettingsProps) {
  const { t } = useI18n();
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  // Provide default value if feedSettings is undefined
  const safeFeedSettings = feedSettings || [];

  const { data: availableFeeds, isLoading } = useQuery({
    queryKey: ['availableFeeds'],
    queryFn: getAvailableFeeds,
  });

  const handleToggleFeed = (feedId: string, enabled: boolean) => {
    const existingIndex = safeFeedSettings.findIndex((s) => s.feedId === feedId);

    if (existingIndex >= 0) {
      const updated = [...safeFeedSettings];
      updated[existingIndex] = { ...updated[existingIndex], enabled };
      onFeedSettingsChange(updated);
    } else {
      onFeedSettingsChange([...safeFeedSettings, { feedId, enabled, minTinkeringIndex: 3 }]);
    }
  };

  const handleUpdateThreshold = (feedId: string, minTinkeringIndex: number) => {
    const existingIndex = safeFeedSettings.findIndex((s) => s.feedId === feedId);

    if (existingIndex >= 0) {
      const updated = [...safeFeedSettings];
      updated[existingIndex] = { ...updated[existingIndex], minTinkeringIndex };
      onFeedSettingsChange(updated);
    }
  };

  const handleRemoveFeed = (feedId: string) => {
    onFeedSettingsChange(safeFeedSettings.filter((s) => s.feedId !== feedId));
  };

  const getFeedSetting = (feedId: string) => {
    return safeFeedSettings.find((s) => s.feedId === feedId);
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
          {t('settings.notifications.feed-settings-title')}
        </CardTitle>
        <CardDescription>{t('settings.notifications.feed-settings-desc')}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Configured Feeds */}
        {safeFeedSettings.length > 0 ? (
          <div className="space-y-3">
            {safeFeedSettings.map((setting) => {
              if (!setting.feedId) return null;

              return (
                <div
                  key={setting.feedId}
                  className="rounded-lg border p-4 space-y-3 hover:bg-accent/50 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 flex-1">
                      <Label className="font-medium cursor-pointer">
                        {getFeedName(setting.feedId)}
                      </Label>
                      {getFeedCategory(setting.feedId) && (
                        <Badge variant="secondary" className="text-xs">
                          {getFeedCategory(setting.feedId)}
                        </Badge>
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
                        className="h-9 w-9"
                        title={t('settings.notifications.remove-feed-setting')}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>

                  {setting.enabled && setting.minTinkeringIndex !== undefined && (
                    <div className="space-y-2 pl-1">
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <span>{t('settings.notifications.min-technical-depth')}</span>
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
              );
            })}
          </div>
        ) : (
          <div className="text-center py-8 text-muted-foreground">
            <Rss className="h-12 w-12 mx-auto mb-2 opacity-50" />
            <p className="font-medium">{t('settings.notifications.no-feed-settings-title')}</p>
            <p className="text-sm mt-1">{t('settings.notifications.no-feed-settings-desc')}</p>
          </div>
        )}

        {/* Add Feed Dialog */}
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button variant="outline" className="w-full" disabled={disabled}>
              <Plus className="mr-2 h-4 w-4" />
              {t('settings.notifications.add-feed-setting')}
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl max-h-[80vh] overflow-hidden flex flex-col">
            <DialogHeader>
              <DialogTitle>{t('settings.notifications.select-rss-source')}</DialogTitle>
              <DialogDescription>
                {t('settings.notifications.select-source-desc')}
              </DialogDescription>
            </DialogHeader>

            <div className="flex-1 overflow-y-auto pr-2">
              {isLoading ? (
                <div className="flex items-center justify-center py-8">
                  <LoadingSpinner size="lg" />
                </div>
              ) : (
                <div className="space-y-2">
                  {Array.isArray(availableFeeds) && availableFeeds.length > 0 ? (
                    availableFeeds.map((feed) => {
                      const isConfigured = safeFeedSettings.some((s) => s.feedId === feed.id);

                      return (
                        <div
                          key={feed.id}
                          className="flex items-center justify-between rounded-lg border p-3 hover:bg-accent/50 transition-colors"
                        >
                          <div className="flex-1 min-w-0">
                            <p className="font-medium truncate">{feed.name}</p>
                            {feed.category && (
                              <p className="text-sm text-muted-foreground">{feed.category}</p>
                            )}
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
                            {isConfigured
                              ? t('settings.notifications.configured')
                              : t('settings.notifications.add')}
                          </Button>
                        </div>
                      );
                    })
                  ) : (
                    <div className="text-center py-8 text-muted-foreground">
                      <Rss className="h-12 w-12 mx-auto mb-2 opacity-50" />
                      <p>{t('settings.notifications.no-available-sources')}</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          </DialogContent>
        </Dialog>
      </CardContent>
    </Card>
  );
}
