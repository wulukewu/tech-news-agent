'use client';

import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { ErrorMessage } from '@/components/ui/error-message';
import { getNotificationHistory } from '@/lib/api/notifications';
import { History, CheckCircle, XCircle, Clock, Mail, MessageSquare } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { zhTW } from 'date-fns/locale';

export function NotificationHistoryPanel() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['notificationHistory'],
    queryFn: () => getNotificationHistory(20),
    refetchInterval: 30000, // Refetch every 30 seconds
  });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'sent':
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-600" />;
      case 'pending':
        return <Clock className="h-4 w-4 text-yellow-600" />;
      default:
        return null;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'sent':
        return (
          <Badge variant="default" className="bg-green-600">
            已發送
          </Badge>
        );
      case 'failed':
        return <Badge variant="destructive">失敗</Badge>;
      case 'pending':
        return <Badge variant="secondary">待發送</Badge>;
      default:
        return null;
    }
  };

  const getChannelIcon = (channel: string) => {
    switch (channel) {
      case 'dm':
        return <MessageSquare className="h-4 w-4" />;
      case 'email':
        return <Mail className="h-4 w-4" />;
      default:
        return null;
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <History className="h-5 w-5" />
          通知歷史記錄
        </CardTitle>
        <CardDescription>查看最近的通知發送狀態</CardDescription>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <LoadingSpinner size="lg" />
          </div>
        ) : error ? (
          <ErrorMessage message={(error as Error).message || '無法載入通知歷史記錄'} />
        ) : !data || !data.recentHistory || data.recentHistory.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <History className="h-12 w-12 mx-auto mb-2 opacity-50" />
            <p>尚無通知記錄</p>
          </div>
        ) : (
          <div className="space-y-4">
            {/* Summary Stats */}
            <div className="grid grid-cols-2 gap-4 p-4 rounded-lg bg-muted/50">
              <div className="text-center">
                <p className="text-sm text-muted-foreground mb-1">總發送數</p>
                <p className="text-2xl font-bold">{data.totalSent}</p>
              </div>
              <div className="text-center">
                <p className="text-sm text-muted-foreground mb-1">失敗數</p>
                <p className="text-2xl font-bold text-red-600">{data.totalFailed}</p>
              </div>
            </div>

            {/* Recent History */}
            <div className="space-y-2">
              <p className="text-sm font-medium">最近通知</p>
              <div className="space-y-2 max-h-[400px] overflow-y-auto pr-2">
                {data.recentHistory.map((entry) => (
                  <div
                    key={entry.id}
                    className="flex items-start gap-3 rounded-lg border p-3 hover:bg-accent/50 transition-colors"
                  >
                    <div className="mt-1 flex-shrink-0">{getStatusIcon(entry.status)}</div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1 flex-wrap">
                        <p className="font-medium truncate flex-1 min-w-0">{entry.articleTitle}</p>
                        {getStatusBadge(entry.status)}
                      </div>
                      <div className="flex items-center gap-3 text-sm text-muted-foreground flex-wrap">
                        <div className="flex items-center gap-1">
                          {getChannelIcon(entry.channel)}
                          <span className="capitalize">{entry.channel}</span>
                        </div>
                        <span className="hidden sm:inline">•</span>
                        <span>
                          {formatDistanceToNow(new Date(entry.sentAt), {
                            addSuffix: true,
                            locale: zhTW,
                          })}
                        </span>
                      </div>
                      {entry.errorMessage && (
                        <p className="text-sm text-red-600 mt-2 p-2 bg-red-50 dark:bg-red-950/20 rounded">
                          {entry.errorMessage}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
