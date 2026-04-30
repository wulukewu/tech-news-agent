'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { ErrorMessage } from '@/components/ui/error-message';
import { toast } from '@/lib/toast';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import {
  getNotificationSettings,
  updateNotificationSettings,
  getNotificationStatus,
} from '@/lib/api/notifications';
import { NotificationSettings } from '@/types/notification';
import { QuietHoursSettings } from '@/features/notifications/components/QuietHoursSettings';
import { TinkeringIndexThreshold } from '@/features/notifications/components/TinkeringIndexThreshold';
import { FeedNotificationSettings } from '@/features/notifications/components/FeedNotificationSettings';
import { NotificationPreview } from '@/features/notifications/components/NotificationPreview';
import { PersonalizedNotificationSettings } from '@/features/notifications/components/PersonalizedNotificationSettings';
import { ProactiveFrequencySettings } from '@/features/notifications/components/ProactiveFrequencySettings';
import { Bell, Moon, Brain, Rss, CheckCircle, AlertCircle } from 'lucide-react';
import { useI18n } from '@/contexts/I18nContext';

export default function NotificationSettingsPage() {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const [isSaving, setIsSaving] = useState(false);

  const {
    data: settings,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['notificationSettings'],
    queryFn: getNotificationSettings,
    staleTime: 0,
  });

  const { data: status } = useQuery({
    queryKey: ['notificationStatus'],
    queryFn: getNotificationStatus,
    refetchInterval: 30000,
    retry: 3,
  });

  const updateMutation = useMutation({
    mutationFn: (updates: Partial<NotificationSettings>) => updateNotificationSettings(updates),
    onMutate: () => setIsSaving(true),
    onSuccess: (updatedSettings) => {
      queryClient.setQueryData(['notificationSettings'], updatedSettings);
      queryClient.invalidateQueries({ queryKey: ['notificationPreferences'] });
      queryClient.invalidateQueries({ queryKey: ['notificationStatus'] });
      toast.success(t('success.settings-saved'));
    },
    onError: () => toast.error(t('errors.server-error')),
    onSettled: () => setIsSaving(false),
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
        <ErrorMessage
          message={(error as Error).message || t('errors.server-error')}
          onRetry={() => queryClient.invalidateQueries({ queryKey: ['notificationSettings'] })}
        />
      </div>
    );
  }

  if (!settings) return null;

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4 animate-in fade-in-50 slide-in-from-top-2 duration-500">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">{t('settings.notifications.title')}</h1>
          <p className="text-muted-foreground mt-1">{t('settings.notifications.description')}</p>
        </div>
        <div className="flex-shrink-0 mt-1 animate-in zoom-in-50 duration-500 delay-200">
          {status && typeof status === 'object' && 'scheduled' in status && status.scheduled ? (
            <Badge
              variant="outline"
              className="text-green-600 border-green-300 dark:border-green-700 gap-1.5 hover:scale-[1.02] transition-transform duration-200"
            >
              <CheckCircle className="h-3.5 w-3.5 animate-pulse" />
              {t('settings.notifications.status-active')}
            </Badge>
          ) : status !== undefined ? (
            <Badge
              variant="outline"
              className="text-muted-foreground gap-1.5 hover:scale-[1.02] transition-transform duration-200"
            >
              <AlertCircle className="h-3.5 w-3.5" />
              {t('settings.notifications.status-inactive')}
            </Badge>
          ) : null}
        </div>
      </div>

      <Tabs
        defaultValue="schedule"
        className="space-y-4 animate-in fade-in-50 slide-in-from-bottom-4 duration-500 delay-300"
      >
        <TabsList className="grid w-full grid-cols-4 h-auto">
          {[
            { value: 'schedule', icon: Bell, label: t('settings.notifications.tab-schedule') },
            {
              value: 'quiet-hours',
              icon: Moon,
              label: t('settings.notifications.tab-quiet-hours'),
            },
            { value: 'filters', icon: Brain, label: t('settings.notifications.tab-filters') },
            { value: 'feeds', icon: Rss, label: t('settings.notifications.tab-feeds') },
          ].map((tab, index) => (
            <TabsTrigger
              key={tab.value}
              value={tab.value}
              className="flex items-center gap-1.5 py-2 text-xs sm:text-sm transition-all duration-300 hover:scale-[1.02] animate-in slide-in-from-top-2"
              style={{ animationDelay: `${400 + index * 100}ms` }}
            >
              <tab.icon className="h-3.5 w-3.5 flex-shrink-0 transition-transform duration-300 hover:scale-[1.05]" />
              <span className="hidden sm:inline">{tab.label}</span>
              <span className="sm:hidden">{tab.label}</span>
            </TabsTrigger>
          ))}
        </TabsList>

        <TabsContent
          value="schedule"
          className="space-y-4 animate-in fade-in-50 slide-in-from-right-4 duration-500"
        >
          <PersonalizedNotificationSettings />
          <ProactiveFrequencySettings />
          {settings && <NotificationPreview settings={settings} />}
        </TabsContent>

        <TabsContent
          value="quiet-hours"
          className="animate-in fade-in-50 slide-in-from-right-4 duration-500"
        >
          <QuietHoursSettings
            quietHours={
              settings && typeof settings === 'object' && 'quietHours' in settings
                ? settings.quietHours
                : undefined
            }
            onQuietHoursChange={(quietHours) => handleUpdate({ quietHours })}
            disabled={isSaving}
          />
        </TabsContent>

        <TabsContent
          value="filters"
          className="animate-in fade-in-50 slide-in-from-right-4 duration-500"
        >
          <TinkeringIndexThreshold
            threshold={
              settings && typeof settings === 'object' && 'minTinkeringIndex' in settings
                ? settings.minTinkeringIndex
                : undefined
            }
            onThresholdChange={(minTinkeringIndex) => handleUpdate({ minTinkeringIndex })}
            disabled={isSaving}
          />
        </TabsContent>

        <TabsContent
          value="feeds"
          className="animate-in fade-in-50 slide-in-from-right-4 duration-500"
        >
          <FeedNotificationSettings
            feedSettings={
              settings && typeof settings === 'object' && 'feedSettings' in settings
                ? settings.feedSettings
                : undefined
            }
            onFeedSettingsChange={(feedSettings) => handleUpdate({ feedSettings })}
            disabled={isSaving}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
}
