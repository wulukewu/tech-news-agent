'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { NotificationSettings } from '@/types/notification';
import { Bell, MessageSquare, Mail, Star, Clock } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { zhTW } from 'date-fns/locale';

interface NotificationPreviewProps {
  settings: NotificationSettings;
}

export function NotificationPreview({ settings }: NotificationPreviewProps) {
  // Mock article data for preview
  const mockArticle = {
    title: 'Next.js 15 發布：全新的 App Router 功能與效能提升',
    source: 'Vercel Blog',
    category: 'Web Dev',
    tinkeringIndex: 4,
    publishedAt: new Date(Date.now() - 1000 * 60 * 30), // 30 minutes ago
  };

  const getChannelIcon = (channel: string) => {
    switch (channel) {
      case 'dm':
        return <MessageSquare className="h-4 w-4" />;
      case 'email':
        return <Mail className="h-4 w-4" />;
      default:
        return <Bell className="h-4 w-4" />;
    }
  };

  const getChannelName = (channel: string) => {
    switch (channel) {
      case 'dm':
        return 'Discord DM';
      case 'email':
        return '電子郵件';
      default:
        return '應用內通知';
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category.toLowerCase()) {
      case 'web dev':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300';
      case 'ai/ml':
        return 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300';
      case 'tech news':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300';
      case 'devops':
        return 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-300';
      case 'security':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300';
    }
  };

  const getStarColor = (index: number, tinkeringIndex: number) => {
    if (index < tinkeringIndex) {
      if (tinkeringIndex <= 2) return 'text-gray-400 fill-gray-400';
      if (tinkeringIndex === 3) return 'text-yellow-400 fill-yellow-400';
      return 'text-orange-400 fill-orange-400';
    }
    return 'text-muted-foreground';
  };

  // Check if notification would be sent based on settings
  const wouldSendNotification = () => {
    if (!settings.enabled) return false;
    if (mockArticle.tinkeringIndex < settings.minTinkeringIndex) return false;

    // Check quiet hours
    if (settings.quietHours.enabled) {
      const now = new Date();
      const currentTime = `${now.getHours().toString().padStart(2, '0')}:${now
        .getMinutes()
        .toString()
        .padStart(2, '0')}`;
      const { start, end } = settings.quietHours;

      // Simple time range check (doesn't handle overnight ranges properly, but good for preview)
      if (start <= end) {
        if (currentTime >= start && currentTime <= end) return false;
      } else {
        if (currentTime >= start || currentTime <= end) return false;
      }
    }

    return true;
  };

  const shouldSend = wouldSendNotification();
  const activeChannels = [];
  if (settings.dmEnabled) activeChannels.push('dm');
  if (settings.emailEnabled) activeChannels.push('email');

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Bell className="h-5 w-5" />
          通知預覽
        </CardTitle>
        <CardDescription>根據您的設定，以下是通知的外觀預覽</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Notification Status */}
        <div
          className={`flex items-center gap-3 p-4 rounded-lg ${
            shouldSend
              ? 'bg-green-50 dark:bg-green-950/20 border border-green-200 dark:border-green-900'
              : 'bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-900'
          }`}
        >
          <div
            className={`h-3 w-3 rounded-full flex-shrink-0 ${
              shouldSend ? 'bg-green-500' : 'bg-red-500'
            }`}
          />
          <span
            className={`text-sm font-medium ${
              shouldSend ? 'text-green-900 dark:text-green-100' : 'text-red-900 dark:text-red-100'
            }`}
          >
            {shouldSend ? '✓ 此文章會觸發通知' : '✗ 此文章不會觸發通知'}
          </span>
        </div>

        {!shouldSend && (
          <div className="text-sm space-y-2 p-4 rounded-lg bg-muted/50">
            <p className="font-medium">原因：</p>
            <ul className="space-y-1.5 ml-2">
              {!settings.enabled && (
                <li className="flex items-start gap-2">
                  <span className="text-muted-foreground mt-0.5">•</span>
                  <span>全域通知已停用</span>
                </li>
              )}
              {settings.enabled && mockArticle.tinkeringIndex < settings.minTinkeringIndex && (
                <li className="flex items-start gap-2">
                  <span className="text-muted-foreground mt-0.5">•</span>
                  <span>
                    技術深度 ({mockArticle.tinkeringIndex}) 低於閾值 ({settings.minTinkeringIndex})
                  </span>
                </li>
              )}
              {settings.enabled && settings.quietHours.enabled && (
                <li className="flex items-start gap-2">
                  <span className="text-muted-foreground mt-0.5">•</span>
                  <span>目前在勿擾時段內</span>
                </li>
              )}
            </ul>
          </div>
        )}

        {shouldSend && (
          <div className="space-y-4">
            {/* Active Channels */}
            <div>
              <p className="text-sm font-medium mb-2">發送渠道：</p>
              <div className="flex gap-2">
                {activeChannels.map((channel) => (
                  <div
                    key={channel}
                    className="flex items-center gap-2 px-3 py-2 rounded-lg bg-primary/10 text-primary"
                  >
                    {getChannelIcon(channel)}
                    <span className="text-sm">{getChannelName(channel)}</span>
                  </div>
                ))}
                {activeChannels.length === 0 && (
                  <span className="text-sm text-muted-foreground">無啟用的通知渠道</span>
                )}
              </div>
            </div>

            {/* Notification Preview */}
            <div className="border rounded-lg p-4 space-y-3">
              <div className="flex items-start gap-3">
                <div className="mt-1">
                  <Bell className="h-5 w-5 text-primary" />
                </div>
                <div className="flex-1 space-y-2">
                  <div className="flex items-center gap-2">
                    <h4 className="font-semibold text-sm">新文章通知</h4>
                    <Badge variant="secondary" className="text-xs">
                      {settings.frequency === 'immediate'
                        ? '即時'
                        : settings.frequency === 'daily'
                          ? '每日摘要'
                          : '每週摘要'}
                    </Badge>
                  </div>

                  <h3 className="font-medium line-clamp-2">{mockArticle.title}</h3>

                  <div className="flex items-center gap-3 text-sm text-muted-foreground">
                    <span>{mockArticle.source}</span>
                    <Badge className={getCategoryColor(mockArticle.category)}>
                      {mockArticle.category}
                    </Badge>
                    <div className="flex items-center gap-1">
                      {Array.from({ length: 5 }).map((_, i) => (
                        <Star
                          key={i}
                          className={`h-3 w-3 ${getStarColor(i, mockArticle.tinkeringIndex)}`}
                        />
                      ))}
                    </div>
                  </div>

                  <div className="flex items-center gap-1 text-xs text-muted-foreground">
                    <Clock className="h-3 w-3" />
                    <span>
                      {formatDistanceToNow(mockArticle.publishedAt, {
                        addSuffix: true,
                        locale: zhTW,
                      })}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Frequency Info */}
            <div className="text-sm text-muted-foreground">
              <p>
                {settings.frequency === 'immediate' && '通知將立即發送'}
                {settings.frequency === 'daily' && '通知將包含在每日摘要中'}
                {settings.frequency === 'weekly' && '通知將包含在每週摘要中'}
              </p>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
