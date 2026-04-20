'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { ErrorMessage } from '@/components/ui/error-message';
import { toast } from '@/lib/toast';
import {
  getNotificationSettings,
  updateNotificationSettings,
  sendTestNotification,
} from '@/lib/api/notifications';
import { NotificationSettings } from '@/types/notification';
import { QuietHoursSettings } from '@/features/notifications/components/QuietHoursSettings';
import { TinkeringIndexThreshold } from '@/features/notifications/components/TinkeringIndexThreshold';
import { FeedNotificationSettings } from '@/features/notifications/components/FeedNotificationSettings';
import { NotificationHistoryPanel } from '@/features/notifications/components/NotificationHistoryPanel';
import { NotificationPreview } from '@/features/notifications/components/NotificationPreview';
import { PersonalizedNotificationSettings } from '@/features/notifications/components/PersonalizedNotificationSettings';

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
      // Also invalidate personalized preferences to ensure consistency
      queryClient.invalidateQueries({ queryKey: ['notificationPreferences'] });
      queryClient.invalidateQueries({ queryKey: ['notificationStatus'] });
      toast.success(t('success.settings-saved'));
    },
    onError: () => {
      toast.error(t('errors.server-error'));
    },
    onSettled: () => {
      setIsSaving(false);
    },
  });

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
        {/* Personalized Notification Settings - Main Interface */}
        <PersonalizedNotificationSettings />

        {/* Additional Legacy Features */}
        <div className="space-y-6">
          <div className="border-t pt-6">
            <h2 className="text-xl font-semibold mb-4">進階功能</h2>
            <p className="text-sm text-muted-foreground mb-6">額外的通知功能和設定選項</p>
          </div>

          {/* Quiet Hours - Only if not covered in PersonalizedNotificationSettings */}
          <QuietHoursSettings
            quietHours={settings?.quietHours}
            onQuietHoursChange={(quietHours) => handleUpdate({ quietHours })}
            disabled={isSaving}
          />

          {/* Tinkering Index Threshold */}
          <TinkeringIndexThreshold
            threshold={settings?.minTinkeringIndex}
            onThresholdChange={(minTinkeringIndex) => handleUpdate({ minTinkeringIndex })}
            disabled={isSaving}
          />

          {/* Feed-specific Notification Settings */}
          <FeedNotificationSettings
            feedSettings={settings?.feedSettings}
            onFeedSettingsChange={(feedSettings) => handleUpdate({ feedSettings })}
            disabled={isSaving}
          />

          {/* Notification Preview */}
          {settings && <NotificationPreview settings={settings} />}

          {/* Notification History */}
          <NotificationHistoryPanel />
        </div>
      </div>
    </div>
  );
}
