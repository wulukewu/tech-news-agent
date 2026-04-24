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
import { NotificationHistoryPanel } from '@/features/notifications/components/NotificationHistoryPanel';
import { NotificationPreview } from '@/features/notifications/components/NotificationPreview';
import { PersonalizedNotificationSettings } from '@/features/notifications/components/PersonalizedNotificationSettings';
import { Bell, Moon, Brain, Rss, History, CheckCircle, AlertCircle } from 'lucide-react';
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
        <PageHeader status={status} />
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
      <PageHeader status={status} />

      <Tabs defaultValue="schedule" className="space-y-4">
        <TabsList className="grid w-full grid-cols-5 h-auto">
          <TabsTrigger
            value="schedule"
            className="flex items-center gap-1.5 py-2 text-xs sm:text-sm"
          >
            <Bell className="h-3.5 w-3.5 flex-shrink-0" />
            <span className="hidden sm:inline">{t('settings.notifications.tab-schedule')}</span>
            <span className="sm:hidden">排程</span>
          </TabsTrigger>
          <TabsTrigger
            value="quiet-hours"
            className="flex items-center gap-1.5 py-2 text-xs sm:text-sm"
          >
            <Moon className="h-3.5 w-3.5 flex-shrink-0" />
            <span className="hidden sm:inline">{t('settings.notifications.tab-quiet-hours')}</span>
            <span className="sm:hidden">勿擾</span>
          </TabsTrigger>
          <TabsTrigger
            value="filters"
            className="flex items-center gap-1.5 py-2 text-xs sm:text-sm"
          >
            <Brain className="h-3.5 w-3.5 flex-shrink-0" />
            <span className="hidden sm:inline">{t('settings.notifications.tab-filters')}</span>
            <span className="sm:hidden">篩選</span>
          </TabsTrigger>
          <TabsTrigger value="feeds" className="flex items-center gap-1.5 py-2 text-xs sm:text-sm">
            <Rss className="h-3.5 w-3.5 flex-shrink-0" />
            <span className="hidden sm:inline">{t('settings.notifications.tab-feeds')}</span>
            <span className="sm:hidden">來源</span>
          </TabsTrigger>
          <TabsTrigger
            value="history"
            className="flex items-center gap-1.5 py-2 text-xs sm:text-sm"
          >
            <History className="h-3.5 w-3.5 flex-shrink-0" />
            <span className="hidden sm:inline">{t('settings.notifications.tab-history')}</span>
            <span className="sm:hidden">歷史</span>
          </TabsTrigger>
        </TabsList>

        {/* Schedule Tab */}
        <TabsContent value="schedule" className="space-y-4">
          <PersonalizedNotificationSettings />
          {settings && <NotificationPreview settings={settings} />}
        </TabsContent>

        {/* Quiet Hours Tab */}
        <TabsContent value="quiet-hours">
          <QuietHoursSettings
            quietHours={settings?.quietHours}
            onQuietHoursChange={(quietHours) => handleUpdate({ quietHours })}
            disabled={isSaving}
          />
        </TabsContent>

        {/* Filters Tab */}
        <TabsContent value="filters">
          <TinkeringIndexThreshold
            threshold={settings?.minTinkeringIndex}
            onThresholdChange={(minTinkeringIndex) => handleUpdate({ minTinkeringIndex })}
            disabled={isSaving}
          />
        </TabsContent>

        {/* Feeds Tab */}
        <TabsContent value="feeds">
          <FeedNotificationSettings
            feedSettings={settings?.feedSettings}
            onFeedSettingsChange={(feedSettings) => handleUpdate({ feedSettings })}
            disabled={isSaving}
          />
        </TabsContent>

        {/* History Tab */}
        <TabsContent value="history">
          <NotificationHistoryPanel />
        </TabsContent>
      </Tabs>
    </div>
  );
}

function PageHeader({ status }: { status: any }) {
  const { t } = useI18n();

  const isActive = status?.scheduled;
  const isDisabled = !status?.scheduled && status !== undefined;

  return (
    <div className="flex items-start justify-between gap-4">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">{t('settings.notifications.title')}</h1>
        <p className="text-muted-foreground mt-1">{t('settings.notifications.description')}</p>
      </div>
      <div className="flex-shrink-0 mt-1">
        {isActive ? (
          <Badge
            variant="outline"
            className="text-green-600 border-green-300 dark:border-green-700 gap-1.5"
          >
            <CheckCircle className="h-3.5 w-3.5" />
            {t('settings.notifications.status-active')}
          </Badge>
        ) : isDisabled ? (
          <Badge variant="outline" className="text-muted-foreground gap-1.5">
            <AlertCircle className="h-3.5 w-3.5" />
            {t('settings.notifications.status-inactive')}
          </Badge>
        ) : null}
      </div>
    </div>
  );
}
