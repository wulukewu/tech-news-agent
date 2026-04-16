/**
 * Notification Settings Page
 *
 * Displays notification preferences settings with DM toggle,
 * granular settings per feed/category, frequency options,
 * time preferences, and notification history.
 *
 * Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9, 6.10
 */

'use client';

import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Button } from '@/components/ui/button';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { ErrorMessage } from '@/components/ui/error-message';
import { toast } from '@/lib/toast';
import {
  getNotificationSettings,
  updateNotificationSettings,
  sendTestNotification,
} from '@/lib/api/notifications';
import {
  NotificationSettings,
  DEFAULT_NOTIFICATION_SETTINGS,
  FeedNotificationSettings,
  NotificationFrequency,
} from '@/types/notification';
import {
  FeedNotificationSettings as FeedSettingsComponent,
  NotificationFrequencySelector,
  NotificationHistoryPanel,
  QuietHoursSettings,
  TinkeringIndexThreshold,
} from '@/features/notifications/components';
import { Bell, BellOff, TestTube, Save, Mail, MessageSquare } from 'lucide-react';

/**
 * Notification Settings Page Component
 *
 * Main page for notification preferences, displaying:
 * - Global notification toggle (Requirement 6.1, 6.2)
 * - DM notification toggle (Requirement 6.3)
 * - Notification frequency selector (Requirement 6.5)
 * - Quiet hours settings (Requirement 6.6)
 * - Minimum tinkering index threshold (Requirement 6.7)
 * - Per-feed notification settings (Requirement 6.4)
 * - Email notification options (Requirement 6.8)
 * - Notification history and delivery status (Requirement 6.9)
 * - Immediate save with visual confirmation (Requirement 6.10)
 */
export default function NotificationSettingsPage() {
  const [settings, setSettings] = useState<NotificationSettings>(DEFAULT_NOTIFICATION_SETTINGS);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const queryClient = useQueryClient();

  // Fetch current notification settings
  const {
    data: currentSettings,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['notificationSettings'],
    queryFn: getNotificationSettings,
  });

  // Update settings mutation
  const updateMutation = useMutation({
    mutationFn: updateNotificationSettings,
    onSuccess: (updatedSettings) => {
      queryClient.setQueryData(['notificationSettings'], updatedSettings);
      setSettings(updatedSettings);
      setHasUnsavedChanges(false);
      toast.success('通知設定已儲存');
    },
    onError: (error: Error) => {
      toast.error(`儲存失敗: ${error.message}`);
    },
  });

  // Test notification mutation
  const testMutation = useMutation({
    mutationFn: sendTestNotification,
    onSuccess: () => {
      toast.success('測試通知已發送');
    },
    onError: (error: Error) => {
      toast.error(`測試通知失敗: ${error.message}`);
    },
  });

  // Initialize settings when data is loaded
  useEffect(() => {
    if (currentSettings) {
      setSettings(currentSettings);
    }
  }, [currentSettings]);

  // Auto-save settings when they change (Requirement 6.10)
  useEffect(() => {
    if (hasUnsavedChanges && settings) {
      const timeoutId = setTimeout(() => {
        updateMutation.mutate(settings);
      }, 1000); // Auto-save after 1 second of inactivity

      return () => clearTimeout(timeoutId);
    }
  }, [settings, hasUnsavedChanges, updateMutation]);

  const handleSettingsChange = (newSettings: Partial<NotificationSettings>) => {
    setSettings((prev) => ({ ...prev, ...newSettings }));
    setHasUnsavedChanges(true);
  };

  const handleGlobalToggle = (enabled: boolean) => {
    handleSettingsChange({ enabled });
  };

  const handleDmToggle = (dmEnabled: boolean) => {
    handleSettingsChange({ dmEnabled });
  };

  const handleEmailToggle = (emailEnabled: boolean) => {
    handleSettingsChange({ emailEnabled });
  };

  const handleFrequencyChange = (frequency: NotificationFrequency) => {
    handleSettingsChange({ frequency });
  };

  const handleQuietHoursChange = (quietHours: { enabled: boolean; start: string; end: string }) => {
    handleSettingsChange({ quietHours });
  };

  const handleThresholdChange = (minTinkeringIndex: number) => {
    handleSettingsChange({ minTinkeringIndex });
  };

  const handleFeedSettingsChange = (feedSettings: FeedNotificationSettings[]) => {
    handleSettingsChange({ feedSettings });
  };

  const handleManualSave = () => {
    updateMutation.mutate(settings);
  };

  const handleTestNotification = () => {
    testMutation.mutate();
  };

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-6 max-w-4xl">
        <div className="space-y-6">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">通知設定</h1>
            <p className="text-muted-foreground">管理您的通知偏好和接收設定</p>
          </div>
          <div className="flex items-center justify-center py-12">
            <LoadingSpinner size="lg" />
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-6 max-w-4xl">
        <div className="space-y-6">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">通知設定</h1>
            <p className="text-muted-foreground">管理您的通知偏好和接收設定</p>
          </div>
          <ErrorMessage error={error as Error} />
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-6 max-w-4xl">
      <div className="space-y-6">
        {/* Page Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">通知設定</h1>
            <p className="text-muted-foreground">管理您的通知偏好和接收設定</p>
          </div>
          <div className="flex items-center gap-2">
            {hasUnsavedChanges && (
              <Button onClick={handleManualSave} disabled={updateMutation.isPending} size="sm">
                <Save className="mr-2 h-4 w-4" />
                {updateMutation.isPending ? '儲存中...' : '儲存'}
              </Button>
            )}
            <Button
              variant="outline"
              onClick={handleTestNotification}
              disabled={testMutation.isPending || !settings.enabled}
              size="sm"
            >
              <TestTube className="mr-2 h-4 w-4" />
              {testMutation.isPending ? '發送中...' : '測試通知'}
            </Button>
          </div>
        </div>

        {/* Auto-save indicator */}
        {hasUnsavedChanges && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <div className="h-2 w-2 bg-yellow-500 rounded-full animate-pulse" />
            <span>設定將自動儲存...</span>
          </div>
        )}

        <div className="grid gap-6">
          {/* Global Notification Settings */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                {settings.enabled ? <Bell className="h-5 w-5" /> : <BellOff className="h-5 w-5" />}
                通知總開關
              </CardTitle>
              <CardDescription>控制所有通知的啟用狀態</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label htmlFor="global-notifications">啟用通知</Label>
                  <p className="text-sm text-muted-foreground">
                    {settings.enabled ? '您將接收新文章通知' : '所有通知已停用'}
                  </p>
                </div>
                <Switch
                  id="global-notifications"
                  checked={settings.enabled}
                  onCheckedChange={handleGlobalToggle}
                />
              </div>

              {/* Channel Settings */}
              {settings.enabled && (
                <div className="space-y-4 pt-4 border-t">
                  <p className="text-sm font-medium">通知管道</p>

                  {/* DM Notifications */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <MessageSquare className="h-4 w-4 text-muted-foreground" />
                      <div className="space-y-0.5">
                        <Label htmlFor="dm-notifications">Discord 私訊通知</Label>
                        <p className="text-sm text-muted-foreground">透過 Discord 私訊接收通知</p>
                      </div>
                    </div>
                    <Switch
                      id="dm-notifications"
                      checked={settings.dmEnabled}
                      onCheckedChange={handleDmToggle}
                    />
                  </div>

                  {/* Email Notifications */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Mail className="h-4 w-4 text-muted-foreground" />
                      <div className="space-y-0.5">
                        <Label htmlFor="email-notifications">電子郵件通知</Label>
                        <p className="text-sm text-muted-foreground">
                          透過電子郵件接收通知 (如果後端支援)
                        </p>
                      </div>
                    </div>
                    <Switch
                      id="email-notifications"
                      checked={settings.emailEnabled}
                      onCheckedChange={handleEmailToggle}
                    />
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Notification Frequency */}
          {settings.enabled && (
            <NotificationFrequencySelector
              frequency={settings.frequency}
              onFrequencyChange={handleFrequencyChange}
            />
          )}

          {/* Quiet Hours */}
          {settings.enabled && (
            <QuietHoursSettings
              quietHours={settings.quietHours}
              onQuietHoursChange={handleQuietHoursChange}
            />
          )}

          {/* Tinkering Index Threshold */}
          {settings.enabled && (
            <TinkeringIndexThreshold
              threshold={settings.minTinkeringIndex}
              onThresholdChange={handleThresholdChange}
            />
          )}

          {/* Per-Feed Notification Settings */}
          {settings.enabled && (
            <FeedSettingsComponent
              feedSettings={settings.feedSettings}
              onFeedSettingsChange={handleFeedSettingsChange}
            />
          )}

          {/* Notification History */}
          <NotificationHistoryPanel />
        </div>
      </div>
    </div>
  );
}
