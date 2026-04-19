'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { ErrorMessage } from '@/components/ui/error-message';
import { toast } from '@/lib/toast';
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
import { Bell, Mail, MessageSquare } from 'lucide-react';

import { useI18n } from '@/contexts/I18nContext';

export default function NotificationSettingsPage() {
  const { t } = useI18n();
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
      toast.success(t('success.settings-saved'));
    },
    onError: (error: any) => {
      toast.error(t('errors.server-error'));
    },
    onSettled: () => {
      setIsSaving(false);
    },
  });

  // Test notification mutation
  const testMutation = useMutation({
    mutationFn: sendTestNotification,
    onSuccess: () => {
      toast.success(t('settings.notifications.test-sent'));
    },
    onError: (error: any) => {
      toast.error(t('settings.notifications.send-failed'));
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
          <h1 className="text-3xl font-bold tracking-tight">{t('settings.notifications.title')}</h1>
          <p className="text-muted-foreground">{t('settings.notifications.description')}</p>
        </div>
        <ErrorMessage
          message={(error as Error).message || t('errors.server-error')}
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
        <h1 className="text-3xl font-bold tracking-tight">{t('settings.notifications.title')}</h1>
        <p className="text-muted-foreground">{t('settings.notifications.description')}</p>
      </div>

      {/* Main Settings Grid */}
      <div className="grid gap-6">
        {/* Global Status Card */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Bell className="h-5 w-5 text-blue-600" />
                <div>
                  <CardTitle>{t('settings.notifications.status')}</CardTitle>
                  <CardDescription>{t('settings.notifications.status-desc')}</CardDescription>
                </div>
              </div>
              {/* Show overall notification status */}
              <div
                className={`text-sm font-medium ${
                  settings.dmEnabled ? 'text-green-600' : 'text-gray-500'
                }`}
              >
                {settings.dmEnabled
                  ? t('settings.notifications.enabled')
                  : t('settings.notifications.disabled')}
              </div>
            </div>
          </CardHeader>
        </Card>

        {/* Notification Channels Card */}
        <Card>
          <CardHeader>
            <CardTitle>{t('settings.notifications.channels')}</CardTitle>
            <CardDescription>{t('settings.notifications.channels-desc')}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                {settings.dmEnabled ? (
                  <MessageSquare className="h-5 w-5 text-green-600" />
                ) : (
                  <MessageSquare className="h-5 w-5 text-muted-foreground" />
                )}
                <div>
                  <Label htmlFor="dm-enabled" className="font-medium">
                    {t('settings.notifications.discord-dm')}
                  </Label>
                  <p className="text-sm text-muted-foreground">
                    {t('settings.notifications.discord-dm-desc')}
                  </p>
                </div>
              </div>
              <Switch
                id="dm-enabled"
                checked={settings.dmEnabled}
                onCheckedChange={(checked) => handleToggle('dmEnabled', checked)}
                disabled={isSaving}
              />
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Mail className="h-5 w-5 text-muted-foreground" />
                <div>
                  <Label htmlFor="email-enabled" className="font-medium">
                    {t('settings.notifications.email')}
                    <span className="ml-2 text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded">
                      {t('settings.notifications.coming-soon')}
                    </span>
                  </Label>
                  <p className="text-sm text-muted-foreground">
                    {t('settings.notifications.email-desc')}
                  </p>
                </div>
              </div>
              <Switch id="email-enabled" checked={false} disabled={true} />
            </div>

            <div className="pt-4 border-t">
              <Button
                variant="outline"
                onClick={() => testMutation.mutate()}
                disabled={testMutation.isPending || !settings.dmEnabled}
                className="w-full"
              >
                {testMutation.isPending ? (
                  <>
                    <LoadingSpinner size="sm" className="mr-2" />
                    {t('settings.notifications.sending')}
                  </>
                ) : (
                  <>
                    <Bell className="mr-2 h-4 w-4" />
                    {t('settings.notifications.send-test')}
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
          disabled={isSaving || !settings.dmEnabled}
        />

        {/* Quiet Hours */}
        <QuietHoursSettings
          quietHours={settings.quietHours}
          onQuietHoursChange={(quietHours) => handleUpdate({ quietHours })}
          disabled={isSaving || !settings.dmEnabled}
        />

        {/* Tinkering Index Threshold */}
        <TinkeringIndexThreshold
          threshold={settings.minTinkeringIndex}
          onThresholdChange={(minTinkeringIndex) => handleUpdate({ minTinkeringIndex })}
          disabled={isSaving || !settings.dmEnabled}
        />

        {/* Feed-specific Notification Settings */}
        <FeedNotificationSettings
          feedSettings={settings.feedSettings}
          onFeedSettingsChange={(feedSettings) => handleUpdate({ feedSettings })}
          disabled={isSaving || !settings.dmEnabled}
        />

        {/* Notification Preview */}
        <NotificationPreview settings={settings} />

        {/* Notification History */}
        <NotificationHistoryPanel />
      </div>
    </div>
  );
}
