'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { ErrorMessage } from '@/components/ui/error-message';
import { toast } from 'sonner';
import {
  getNotificationSettings,
  updateNotificationSettings,
  sendTestNotification,
} from '@/lib/api/notifications';
import { NotificationSettings } from '@/types/notification';
import { NotificationFrequencySelector } from '@/features/notifications/components/NotificationFrequencySelector';
import { QuietHoursSettings } from '@/features/notifications/components/QuietHoursSettings';
import { TinkeringIndexThreshold } from '@/features/notifications/components/TinkeringIndexThreshold';
import { FeedNotificationSettings } from '@/features/notifications/components/FeedNotificationSettings';
import { NotificationHistoryPanel } from '@/features/notifications/components/NotificationHistoryPanel';
import { NotificationPreview } from '@/features/notifications/components/NotificationPreview';
import { Bell, BellOff, Mail, MessageSquare, Check } from 'lucide-react';

export default function NotificationSettingsPage() {
  const queryClient = useQueryClient();
  const [isSaving, setIsSaving] = useState(false);

  // Fetch notification settings
  const {
    data: settings,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['notificationSettings'],
    queryFn: getNotificationSettings,
    staleTime: 0, // Always fetch fresh data
  });

  // Update notification settings mutation
  const updateMutation = useMutation({
    mutationFn: (updates: Partial<NotificationSettings>) => updateNotificationSettings(updates),
    onMutate: () => {
      setIsSaving(true);
    },
    onSuccess: (updatedSettings) => {
      queryClient.setQueryData(['notificationSettings'], updatedSettings);
      toast.success('設定已儲存', {
        description: '您的通知偏好設定已成功更新',
        icon: <Check className="h-4 w-4" />,
      });
    },
    onError: (error: any) => {
      toast.error('儲存失敗', {
        description: error.message || '無法儲存通知設定，請稍後再試',
      });
    },
    onSettled: () => {
      setIsSaving(false);
    },
  });

  // Test notification mutation
  const testMutation = useMutation({
    mutationFn: sendTestNotification,
    onSuccess: () => {
      toast.success('測試通知已發送', {
        description: '請檢查您的通知渠道',
      });
    },
    onError: (error: any) => {
      toast.error('發送失敗', {
        description: error.message || '無法發送測試通知',
      });
    },
  });

  const handleToggle = (field: keyof NotificationSettings, value: boolean) => {
    updateMutation.mutate({ [field]: value });
  };

  const handleUpdate = (updates: Partial<NotificationSettings>) => {
    updateMutation.mutate(updates);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">通知偏好設定</h1>
          <p className="text-muted-foreground">管理您的通知偏好和頻率設定</p>
        </div>
        <ErrorMessage
          message={(error as Error).message || '無法載入通知設定'}
          onRetry={() => queryClient.invalidateQueries({ queryKey: ['notificationSettings'] })}
        />
      </div>
    );
  }

  if (!settings) {
    return null;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">通知偏好設定</h1>
        <p className="text-muted-foreground">管理您的通知偏好和頻率設定</p>
      </div>

      {/* Main Settings Grid */}
      <div className="grid gap-6">
        {/* Global Status Card */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                {settings.enabled ? (
                  <Bell className="h-5 w-5 text-green-600" />
                ) : (
                  <BellOff className="h-5 w-5 text-muted-foreground" />
                )}
                <div>
                  <CardTitle>通知狀態</CardTitle>
                  <CardDescription>
                    {settings.enabled ? '通知功能已啟用' : '通知功能已停用'}
                  </CardDescription>
                </div>
              </div>
              <Switch
                id="notifications-enabled"
                checked={settings.enabled}
                onCheckedChange={(checked) => handleToggle('enabled', checked)}
                disabled={isSaving}
              />
            </div>
          </CardHeader>
        </Card>

        {/* Notification Channels Card */}
        <Card>
          <CardHeader>
            <CardTitle>通知渠道</CardTitle>
            <CardDescription>選擇您希望接收通知的方式</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <MessageSquare className="h-5 w-5 text-muted-foreground" />
                <div>
                  <Label htmlFor="dm-enabled" className="font-medium">
                    Discord DM 通知
                  </Label>
                  <p className="text-sm text-muted-foreground">透過 Discord 私訊接收通知</p>
                </div>
              </div>
              <Switch
                id="dm-enabled"
                checked={settings.dmEnabled}
                onCheckedChange={(checked) => handleToggle('dmEnabled', checked)}
                disabled={isSaving || !settings.enabled}
              />
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Mail className="h-5 w-5 text-muted-foreground" />
                <div>
                  <Label htmlFor="email-enabled" className="font-medium">
                    電子郵件通知
                  </Label>
                  <p className="text-sm text-muted-foreground">透過電子郵件接收通知</p>
                </div>
              </div>
              <Switch
                id="email-enabled"
                checked={settings.emailEnabled}
                onCheckedChange={(checked) => handleToggle('emailEnabled', checked)}
                disabled={isSaving || !settings.enabled}
              />
            </div>

            <div className="pt-4 border-t">
              <Button
                variant="outline"
                onClick={() => testMutation.mutate()}
                disabled={testMutation.isPending || !settings.enabled}
                className="w-full"
              >
                {testMutation.isPending ? (
                  <>
                    <LoadingSpinner size="sm" className="mr-2" />
                    發送中...
                  </>
                ) : (
                  <>
                    <Bell className="mr-2 h-4 w-4" />
                    發送測試通知
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Notification Frequency */}
        <NotificationFrequencySelector
          frequency={settings.frequency}
          onFrequencyChange={(frequency) => handleUpdate({ frequency })}
          disabled={isSaving || !settings.enabled}
        />

        {/* Quiet Hours */}
        <QuietHoursSettings
          quietHours={settings.quietHours}
          onQuietHoursChange={(quietHours) => handleUpdate({ quietHours })}
          disabled={isSaving || !settings.enabled}
        />

        {/* Tinkering Index Threshold */}
        <TinkeringIndexThreshold
          threshold={settings.minTinkeringIndex}
          onThresholdChange={(minTinkeringIndex) => handleUpdate({ minTinkeringIndex })}
          disabled={isSaving || !settings.enabled}
        />

        {/* Feed-specific Notification Settings */}
        <FeedNotificationSettings
          feedSettings={settings.feedSettings}
          onFeedSettingsChange={(feedSettings) => handleUpdate({ feedSettings })}
          disabled={isSaving || !settings.enabled}
        />

        {/* Notification Preview */}
        <NotificationPreview settings={settings} />

        {/* Notification History */}
        <NotificationHistoryPanel />
      </div>
    </div>
  );
}
