'use client';

import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { ErrorMessage } from '@/components/ui/error-message';
import { toast } from '@/lib/toast';
import {
  getNotificationPreferences,
  updateNotificationPreferences,
  previewNotificationTime,
  getSupportedTimezones,
  getNotificationStatus,
  UserNotificationPreferences,
  UpdateUserNotificationPreferencesRequest,
  TimezoneOption,
  NotificationPreviewResponse,
} from '@/lib/api/notifications';
import {
  Clock,
  Globe,
  Calendar,
  CalendarDays,
  CalendarRange,
  BellOff,
  MessageSquare,
  Mail,
  CheckCircle,
  AlertCircle,
  Search,
} from 'lucide-react';
import { useI18n } from '@/contexts/I18nContext';

interface PersonalizedNotificationSettingsProps {
  className?: string;
}

export function PersonalizedNotificationSettings({
  className,
}: PersonalizedNotificationSettingsProps) {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const [isSaving, setIsSaving] = useState(false);
  const [previewData, setPreviewData] = useState<NotificationPreviewResponse | null>(null);
  const [isPreviewLoading, setIsPreviewLoading] = useState(false);
  const [localTime, setLocalTime] = useState<string>(''); // Local state for time input
  const [tzSearchQuery, setTzSearchQuery] = useState<string>('');

  // Fetch notification preferences
  const {
    data: preferences,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['notificationPreferences'],
    queryFn: getNotificationPreferences,
    staleTime: 0,
  });

  // Fetch supported timezones
  const { data: timezones = [] } = useQuery({
    queryKey: ['supportedTimezones'],
    queryFn: getSupportedTimezones,
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
  });

  // Fetch notification status
  const {
    data: status,
    error: statusError,
    isLoading: statusLoading,
  } = useQuery({
    queryKey: ['notificationStatus'],
    queryFn: getNotificationStatus,
    refetchInterval: 30000, // Refetch every 30 seconds
    retry: 3,
  });

  const updateMutation = useMutation({
    mutationFn: (updates: UpdateUserNotificationPreferencesRequest) =>
      updateNotificationPreferences(updates),
    onMutate: () => {
      setIsSaving(true);
    },
    onSuccess: (updatedPreferences) => {
      queryClient.setQueryData(['notificationPreferences'], updatedPreferences);
      queryClient.invalidateQueries({ queryKey: ['notificationStatus'] });
      queryClient.invalidateQueries({ queryKey: ['notificationSettings'] });
      toast.success(t('settings.notifications.test-sent'));
      updatePreview(updatedPreferences);
    },
    onError: () => {
      toast.error(t('settings.notifications.send-failed'));
    },
    onSettled: () => {
      setIsSaving(false);
    },
  });

  const updatePreview = async (prefs: UserNotificationPreferences) => {
    if (prefs.frequency === 'disabled') {
      setPreviewData({
        nextNotificationTime: null,
        localTime: null,
        utcTime: null,
        message: t('settings.notifications.disabled'),
      });
      return;
    }

    setIsPreviewLoading(true);
    try {
      const preview = await previewNotificationTime(
        prefs.frequency,
        prefs.notificationTime,
        prefs.timezone,
        prefs.notificationDayOfWeek,
        prefs.notificationDayOfMonth
      );
      setPreviewData(preview);
    } catch (error) {
      console.error('Failed to update preview:', error);
    } finally {
      setIsPreviewLoading(false);
    }
  };

  // Update preview when preferences change
  useEffect(() => {
    if (preferences) {
      updatePreview(preferences);
      // Initialize local time state
      setLocalTime(preferences.notificationTime);
    }
  }, [preferences]);

  const handleUpdate = (updates: UpdateUserNotificationPreferencesRequest) => {
    updateMutation.mutate(updates);
  };

  const getFrequencyIcon = (frequency: string) => {
    switch (frequency) {
      case 'daily':
        return Calendar;
      case 'weekly':
        return CalendarDays;
      case 'monthly':
        return CalendarRange;
      case 'disabled':
        return BellOff;
      default:
        return Clock;
    }
  };

  const getFrequencyLabel = (frequency: string) => {
    switch (frequency) {
      case 'daily':
        return t('settings.notifications.frequency-daily');
      case 'weekly':
        return t('settings.notifications.frequency-weekly');
      case 'monthly':
        return t('settings.notifications.frequency-monthly');
      case 'disabled':
        return t('settings.notifications.disabled');
      default:
        return frequency;
    }
  };

  const getFrequencyDescription = (frequency: string) => {
    switch (frequency) {
      case 'daily':
        return t('settings.notifications.frequency-daily-desc');
      case 'weekly':
        return t('settings.notifications.frequency-weekly-desc');
      case 'monthly':
        return t('settings.notifications.frequency-monthly-desc');
      case 'disabled':
        return t('settings.notifications.frequency-disabled-desc');
      default:
        return '';
    }
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
      <ErrorMessage
        message={t('settings.notifications.description')}
        onRetry={() => queryClient.invalidateQueries({ queryKey: ['notificationPreferences'] })}
      />
    );
  }

  if (!preferences) {
    return null;
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Status Overview Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Clock className="h-5 w-5 text-muted-foreground" />
              <div>
                <CardTitle>{t('settings.notifications.title')}</CardTitle>
                <CardDescription>{t('settings.notifications.description')}</CardDescription>
              </div>
            </div>
            <div className="flex items-center gap-2 text-sm">
              {statusLoading ? (
                <span className="text-muted-foreground flex items-center gap-1.5">
                  <LoadingSpinner size="sm" />
                </span>
              ) : statusError ? (
                <span className="text-yellow-600 dark:text-yellow-400 flex items-center gap-1.5">
                  <AlertCircle className="h-4 w-4" />
                </span>
              ) : status && 'scheduled' in status && status.scheduled ? (
                <span className="text-green-600 dark:text-green-400 flex items-center gap-1.5">
                  <CheckCircle className="h-4 w-4" />
                  {t('settings.notifications.status-active')}
                </span>
              ) : preferences.frequency === 'disabled' || !preferences.dmEnabled ? (
                <span className="text-muted-foreground flex items-center gap-1.5">
                  <AlertCircle className="h-4 w-4" />
                  {t('settings.notifications.status-inactive')}
                </span>
              ) : (
                <span className="text-orange-600 dark:text-orange-400 flex items-center gap-1.5">
                  <AlertCircle className="h-4 w-4" />
                  {t('settings.notifications.status-inactive')}
                </span>
              )}
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Notification Channels */}
      <Card>
        <CardHeader>
          <CardTitle>{t('settings.notifications.channels')}</CardTitle>
          <CardDescription>{t('settings.notifications.channels-desc')}</CardDescription>
        </CardHeader>
        <CardContent className="divide-y">
          <div className="flex items-center justify-between py-3 first:pt-0 last:pb-0">
            <div className="flex items-center gap-3">
              <MessageSquare className="h-4 w-4 text-muted-foreground flex-shrink-0" />
              <div>
                <Label htmlFor="dm-enabled" className="font-medium cursor-pointer">
                  {t('settings.notifications.channel-discord')}
                </Label>
                <p className="text-xs text-muted-foreground mt-0.5">
                  {t('settings.notifications.discord-dm-desc')}
                </p>
              </div>
            </div>
            <Switch
              id="dm-enabled"
              checked={preferences.dmEnabled}
              onCheckedChange={(checked) => handleUpdate({ dmEnabled: checked })}
              disabled={isSaving}
            />
          </div>

          <div className="flex items-center justify-between py-3 first:pt-0 last:pb-0">
            <div className="flex items-center gap-3">
              <Mail className="h-4 w-4 text-muted-foreground flex-shrink-0" />
              <div>
                <div className="flex items-center gap-2">
                  <Label htmlFor="email-enabled" className="font-medium">
                    {t('settings.notifications.channel-email')}
                  </Label>
                  <span className="text-xs bg-muted text-muted-foreground px-1.5 py-0.5 rounded">
                    {t('settings.notifications.coming-soon')}
                  </span>
                </div>
                <p className="text-xs text-muted-foreground mt-0.5">
                  {t('settings.notifications.email-desc')}
                </p>
              </div>
            </div>
            <Switch
              id="email-enabled"
              checked={preferences.emailEnabled}
              onCheckedChange={(checked) => handleUpdate({ emailEnabled: checked })}
              disabled={true}
            />
          </div>

          <div className="pt-3 flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={async () => {
                try {
                  const { sendTestNotification } = await import('@/lib/api/notifications');
                  await sendTestNotification();
                  toast.success(t('settings.notifications.test-sent'));
                } catch (error: any) {
                  toast.error(t('settings.notifications.send-failed'));
                }
              }}
              disabled={isSaving || !preferences.dmEnabled}
            >
              <MessageSquare className="mr-2 h-4 w-4" />
              {t('settings.notifications.send-test')}
            </Button>

            {!(status && 'scheduled' in status && status.scheduled) &&
              preferences.frequency !== 'disabled' &&
              preferences.dmEnabled && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={async () => {
                    try {
                      const { rescheduleUserNotification } =
                        await import('@/lib/api/notifications');
                      const result = await rescheduleUserNotification();
                      if (result.success) {
                        toast.success(result.message);
                        queryClient.invalidateQueries({ queryKey: ['notificationStatus'] });
                      } else {
                        toast.error(result.message);
                      }
                    } catch {
                      toast.error(t('settings.notifications.send-failed'));
                    }
                  }}
                  disabled={isSaving}
                >
                  <Clock className="mr-2 h-4 w-4" />
                  {t('settings.notifications.reschedule')}
                </Button>
              )}
          </div>
        </CardContent>
      </Card>

      {/* Frequency Settings */}
      <Card>
        <CardHeader>
          <CardTitle>{t('settings.notifications.frequency-title')}</CardTitle>
          <CardDescription>{t('settings.notifications.frequency-desc')}</CardDescription>
        </CardHeader>
        <CardContent>
          <Select
            value={preferences.frequency}
            onValueChange={(value) => handleUpdate({ frequency: value as any })}
            disabled={isSaving || !preferences.dmEnabled}
          >
            <SelectTrigger className="w-full">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {(['daily', 'weekly', 'monthly', 'disabled'] as const).map((freq) => {
                const Icon = getFrequencyIcon(freq);
                return (
                  <SelectItem key={freq} value={freq}>
                    <div className="flex items-center gap-2">
                      <Icon className="h-4 w-4" />
                      <span>{getFrequencyLabel(freq)}</span>
                    </div>
                  </SelectItem>
                );
              })}
            </SelectContent>
          </Select>
        </CardContent>
      </Card>

      {/* Time and Timezone Settings */}
      {preferences.frequency !== 'disabled' && (
        <Card>
          <CardHeader>
            <CardTitle>{t('settings.notifications.time-title')}</CardTitle>
            <CardDescription>{t('settings.notifications.time-desc')}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {preferences.frequency === 'weekly' && (
              <div className="space-y-2">
                <Label htmlFor="day-of-week">{t('settings.notifications.day-of-week')}</Label>
                <Select
                  value={preferences.notificationDayOfWeek?.toString() || '5'}
                  onValueChange={(value) =>
                    handleUpdate({ notificationDayOfWeek: parseInt(value) })
                  }
                  disabled={isSaving || !preferences.dmEnabled}
                >
                  <SelectTrigger id="day-of-week">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {(
                      [
                        ['0', 'settings.notifications.weekday-0'],
                        ['1', 'settings.notifications.weekday-1'],
                        ['2', 'settings.notifications.weekday-2'],
                        ['3', 'settings.notifications.weekday-3'],
                        ['4', 'settings.notifications.weekday-4'],
                        ['5', 'settings.notifications.weekday-5'],
                        ['6', 'settings.notifications.weekday-6'],
                      ] as const
                    ).map(([val, key]) => (
                      <SelectItem key={val} value={val}>
                        {t(key)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}

            {preferences.frequency === 'monthly' && (
              <div className="space-y-2">
                <Label htmlFor="day-of-month">{t('settings.notifications.day-of-month')}</Label>
                <Select
                  value={preferences.notificationDayOfMonth?.toString() || '1'}
                  onValueChange={(value) =>
                    handleUpdate({ notificationDayOfMonth: parseInt(value) })
                  }
                  disabled={isSaving || !preferences.dmEnabled}
                >
                  <SelectTrigger id="day-of-month">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="max-h-[300px]">
                    {Array.from({ length: 31 }, (_, i) => i + 1).map((day) => (
                      <SelectItem key={day} value={day.toString()}>
                        {t('settings.notifications.day-of-month-option', { day })}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground">
                  {t('settings.notifications.day-of-month-hint')}
                </p>
              </div>
            )}

            {/* Upgraded visual layout for Time and Timezone Configuration */}
            <div className="grid grid-cols-1 gap-6 pt-4 border-t border-border mt-4">
              {/* Notification Time Configuration Section */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <Label
                    htmlFor="notification-time"
                    className="text-sm font-semibold flex items-center gap-2"
                  >
                    <Clock className="h-4 w-4 text-emerald-500" />
                    {t('settings.notifications.notification-time')}
                  </Label>
                  <span className="text-[10px] text-muted-foreground bg-secondary px-2 py-0.5 rounded font-mono">
                    24H format
                  </span>
                </div>

                <div className="flex flex-col sm:flex-row gap-4 items-stretch sm:items-center">
                  <div className="relative flex-1">
                    <Input
                      id="notification-time"
                      type="time"
                      value={localTime}
                      onChange={(e) => setLocalTime(e.target.value)}
                      onBlur={(e) => {
                        if (e.target.value && e.target.value !== preferences.notificationTime) {
                          handleUpdate({ notificationTime: e.target.value });
                        }
                      }}
                      disabled={isSaving || !preferences.dmEnabled}
                      className="pl-3 h-10 w-full bg-background border-input ring-offset-background focus-visible:ring-emerald-500 font-medium text-base rounded-md focus:shadow-emerald-500/10 focus:shadow-md transition-all duration-300"
                    />
                  </div>

                  {/* Preset Quick Select Time Pills */}
                  <div className="flex flex-wrap gap-2 items-center">
                    {[
                      { label: '🌅 08:00', time: '08:00' },
                      { label: '🕛 12:00', time: '12:00' },
                      { label: '🌃 20:00', time: '20:00' },
                      { label: '🌙 22:00', time: '22:00' },
                    ].map((preset) => {
                      const isSelected = localTime === preset.time;
                      return (
                        <Button
                          key={preset.time}
                          type="button"
                          variant={isSelected ? 'default' : 'outline'}
                          size="sm"
                          disabled={isSaving || !preferences.dmEnabled}
                          onClick={() => {
                            setLocalTime(preset.time);
                            handleUpdate({ notificationTime: preset.time });
                          }}
                          className={`h-9 px-3 text-xs rounded-full font-medium transition-all duration-300 hover:scale-[1.03] active:scale-95 ${
                            isSelected
                              ? 'bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm shadow-emerald-600/20'
                              : 'hover:bg-secondary hover:border-emerald-500/30'
                          }`}
                        >
                          {preset.label}
                        </Button>
                      );
                    })}
                  </div>
                </div>
                <p className="text-xs text-muted-foreground">
                  {t('settings.notifications.time-hint')}
                </p>
              </div>

              {/* Timezone Configuration Section */}
              <div className="space-y-3 pt-2">
                <Label htmlFor="timezone" className="text-sm font-semibold flex items-center gap-2">
                  <Globe className="h-4 w-4 text-emerald-500" />
                  {t('settings.notifications.timezone')}
                </Label>

                {/* Popular Region Quick-Select Cards */}
                <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
                  {[
                    { flag: '🇹🇼', label: 'Taipei', timezone: 'Asia/Taipei', gmt: 'UTC+8' },
                    { flag: '🇯🇵', label: 'Tokyo', timezone: 'Asia/Tokyo', gmt: 'UTC+9' },
                    { flag: '🇺🇸', label: 'New York', timezone: 'America/New_York', gmt: 'UTC-5' },
                    { flag: '🇬🇧', label: 'London', timezone: 'Europe/London', gmt: 'UTC+0' },
                    { flag: '🌐', label: 'UTC', timezone: 'UTC', gmt: 'UTC+0' },
                  ].map((pop) => {
                    const isSelected = preferences.timezone === pop.timezone;
                    return (
                      <button
                        key={pop.timezone}
                        type="button"
                        disabled={isSaving || !preferences.dmEnabled}
                        onClick={() => handleUpdate({ timezone: pop.timezone })}
                        className={`flex flex-col items-center justify-center p-2.5 rounded-lg border text-center transition-all duration-300 hover:scale-[1.02] active:scale-[0.98] ${
                          isSelected
                            ? 'bg-emerald-500/5 dark:bg-emerald-500/10 border-emerald-500 text-emerald-800 dark:text-emerald-300 font-semibold shadow-sm shadow-emerald-500/10'
                            : 'border-border bg-background hover:bg-secondary hover:border-muted-foreground/20'
                        }`}
                      >
                        <span className="text-lg mb-1 leading-none">{pop.flag}</span>
                        <span className="text-xs truncate max-w-full font-medium">{pop.label}</span>
                        <span className="text-[10px] text-muted-foreground mt-0.5">{pop.gmt}</span>
                      </button>
                    );
                  })}
                </div>

                {/* Real-time Searchable Timezone Dropdown Select */}
                <div className="relative">
                  <Select
                    value={preferences.timezone}
                    onValueChange={(value) => handleUpdate({ timezone: value })}
                    disabled={isSaving || !preferences.dmEnabled}
                  >
                    <SelectTrigger className="w-full h-10 font-medium hover:border-emerald-500/30 transition-all duration-300">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="max-h-80 overflow-y-auto">
                      {/* Search Bar inside Select Dropdown */}
                      <div className="flex items-center gap-2 px-3 py-2 border-b sticky top-0 bg-popover z-10">
                        <Search className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                        <input
                          placeholder="搜尋時區 (e.g. Taipei, UTC)..."
                          value={tzSearchQuery}
                          onChange={(e) => setTzSearchQuery(e.target.value)}
                          onClick={(e) => e.stopPropagation()} // Prevent closing select on click
                          onKeyDown={(e) => e.stopPropagation()} // Prevent selecting item on keys
                          className="bg-transparent border-none outline-none w-full text-sm placeholder:text-muted-foreground"
                        />
                      </div>

                      {(() => {
                        const filtered = timezones.filter(
                          (tz) =>
                            tz.label.toLowerCase().includes(tzSearchQuery.toLowerCase()) ||
                            tz.value.toLowerCase().includes(tzSearchQuery.toLowerCase()) ||
                            tz.offset.toLowerCase().includes(tzSearchQuery.toLowerCase())
                        );
                        return filtered.length > 0 ? (
                          filtered.map((tz) => (
                            <SelectItem key={tz.value} value={tz.value}>
                              <div className="flex items-center gap-2">
                                <Globe className="h-4 w-4 text-muted-foreground" />
                                <span>{tz.label}</span>
                                <span className="text-xs text-muted-foreground bg-secondary px-1.5 py-0.5 rounded">
                                  {tz.offset}
                                </span>
                              </div>
                            </SelectItem>
                          ))
                        ) : (
                          <div className="text-xs text-muted-foreground p-3 text-center">
                            查無匹配時區
                          </div>
                        );
                      })()}
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Preview Card */}
      <Card>
        <CardHeader>
          <CardTitle>{t('settings.notifications.preview-title')}</CardTitle>
          <CardDescription>{t('settings.notifications.preview-desc')}</CardDescription>
        </CardHeader>
        <CardContent>
          {isPreviewLoading ? (
            <div className="flex items-center gap-2">
              <LoadingSpinner size="sm" />
              <span className="text-sm text-muted-foreground">
                {t('settings.notifications.sending')}
              </span>
            </div>
          ) : previewData ? (
            <div className="space-y-2">
              <p className="text-sm font-medium">{previewData.message}</p>
              {previewData.localTime && (
                <p className="text-xs text-muted-foreground">
                  UTC: {new Date(previewData.utcTime!).toLocaleString()}
                </p>
              )}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">
              {t('settings.notifications.no-preview')}
            </p>
          )}
        </CardContent>
      </Card>

      {/* Status Information */}
      {status && (
        <Card>
          <CardHeader>
            <CardTitle>{t('settings.notifications.status')}</CardTitle>
            <CardDescription>{t('settings.notifications.status-desc')}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <p className="text-sm">{status.message}</p>
              {status.nextRunTime && (
                <p className="text-xs text-muted-foreground">
                  {new Date(status.nextRunTime).toLocaleString()}
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
