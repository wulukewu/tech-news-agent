'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { ErrorMessage } from '@/components/ui/error-message';
import { toast } from '@/lib/toast';
import { Moon, Clock, Globe, AlertCircle, CheckCircle } from 'lucide-react';
import {
  getQuietHours,
  updateQuietHours,
  getQuietHoursStatus,
  getSupportedTimezones,
  QuietHoursSettings as QuietHoursSettingsType,
} from '@/lib/api/notifications';
import { useI18n } from '@/contexts/I18nContext';

interface QuietHoursSettingsProps {
  quietHours?: { enabled: boolean; start: string; end: string };
  onQuietHoursChange?: (quietHours: { enabled: boolean; start: string; end: string }) => void;
  disabled?: boolean;
}

export function QuietHoursSettings({
  onQuietHoursChange: legacyOnChange,
  disabled: legacyDisabled = false,
}: QuietHoursSettingsProps) {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const [isSaving, setIsSaving] = useState(false);

  const {
    data: quietHours,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['quietHours'],
    queryFn: getQuietHours,
    staleTime: 0,
  });

  const { data: status, isLoading: statusLoading } = useQuery({
    queryKey: ['quietHoursStatus'],
    queryFn: getQuietHoursStatus,
    refetchInterval: 60000,
    staleTime: 30000,
  });

  const { data: timezones = [] } = useQuery({
    queryKey: ['supportedTimezones'],
    queryFn: getSupportedTimezones,
    staleTime: 5 * 60 * 1000,
  });

  const updateMutation = useMutation({
    mutationFn: updateQuietHours,
    onMutate: () => setIsSaving(true),
    onSuccess: (updated) => {
      queryClient.setQueryData(['quietHours'], updated);
      queryClient.invalidateQueries({ queryKey: ['quietHoursStatus'] });
      toast.success(t('settings.notifications.quiet-hours-updated'));
      if (legacyOnChange) {
        legacyOnChange({
          enabled: updated.enabled,
          start: updated.start_time.substring(0, 5),
          end: updated.end_time.substring(0, 5),
        });
      }
    },
    onError: () => toast.error(t('settings.notifications.send-failed')),
    onSettled: () => setIsSaving(false),
  });

  const handleUpdate = (updates: Partial<QuietHoursSettingsType>) => updateMutation.mutate(updates);
  const formatTime = (t: string) => t.substring(0, 5);

  const weekdays = [
    ['1', 'settings.notifications.weekday-1'],
    ['2', 'settings.notifications.weekday-2'],
    ['3', 'settings.notifications.weekday-3'],
    ['4', 'settings.notifications.weekday-4'],
    ['5', 'settings.notifications.weekday-5'],
    ['6', 'settings.notifications.weekday-6'],
    ['7', 'settings.notifications.weekday-0'],
  ] as const;

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Moon className="h-5 w-5" />
            {t('settings.notifications.quiet-hours-title')}
          </CardTitle>
          <CardDescription>{t('settings.notifications.quiet-hours-desc')}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <LoadingSpinner size="lg" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Moon className="h-5 w-5" />
            {t('settings.notifications.quiet-hours-title')}
          </CardTitle>
          <CardDescription>{t('settings.notifications.quiet-hours-desc')}</CardDescription>
        </CardHeader>
        <CardContent>
          <ErrorMessage
            message={t('settings.notifications.quiet-hours-load-error')}
            onRetry={() => queryClient.invalidateQueries({ queryKey: ['quietHours'] })}
          />
        </CardContent>
      </Card>
    );
  }

  if (!quietHours) return null;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Moon className="h-5 w-5 text-muted-foreground" />
            <div>
              <CardTitle>{t('settings.notifications.quiet-hours-title')}</CardTitle>
              <CardDescription>{t('settings.notifications.quiet-hours-desc')}</CardDescription>
            </div>
          </div>
          <div className="flex items-center gap-2 text-sm">
            {statusLoading ? (
              <span className="text-muted-foreground flex items-center gap-1.5">
                <LoadingSpinner size="sm" />
              </span>
            ) : status?.is_in_quiet_hours ? (
              <span className="text-orange-600 dark:text-orange-400 flex items-center gap-1.5">
                <Moon className="h-4 w-4" />
                {t('settings.notifications.quiet-hours-active')}
              </span>
            ) : quietHours.enabled ? (
              <span className="text-green-600 dark:text-green-400 flex items-center gap-1.5">
                <CheckCircle className="h-4 w-4" />
                {t('settings.notifications.status-active')}
              </span>
            ) : (
              <span className="text-muted-foreground flex items-center gap-1.5">
                <AlertCircle className="h-4 w-4" />
                {t('settings.notifications.status-inactive')}
              </span>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="flex items-center justify-between">
          <div className="space-y-0.5">
            <Label htmlFor="quiet-hours-enabled">
              {t('settings.notifications.quiet-hours-enable')}
            </Label>
            <p className="text-sm text-muted-foreground">
              {t('settings.notifications.quiet-hours-enable-desc')}
            </p>
          </div>
          <Switch
            id="quiet-hours-enabled"
            checked={quietHours.enabled}
            onCheckedChange={(enabled) => handleUpdate({ enabled })}
            disabled={isSaving || legacyDisabled}
          />
        </div>

        {quietHours.enabled && (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="quiet-hours-start">
                  {t('settings.notifications.quiet-hours-start')}
                </Label>
                <Input
                  id="quiet-hours-start"
                  type="time"
                  value={formatTime(quietHours.start_time)}
                  onChange={(e) => handleUpdate({ start_time: e.target.value + ':00' })}
                  disabled={isSaving || legacyDisabled}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="quiet-hours-end">
                  {t('settings.notifications.quiet-hours-end')}
                </Label>
                <Input
                  id="quiet-hours-end"
                  type="time"
                  value={formatTime(quietHours.end_time)}
                  onChange={(e) => handleUpdate({ end_time: e.target.value + ':00' })}
                  disabled={isSaving || legacyDisabled}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="quiet-hours-timezone">{t('settings.notifications.timezone')}</Label>
              <Select
                value={quietHours.timezone}
                onValueChange={(timezone) => handleUpdate({ timezone })}
                disabled={isSaving || legacyDisabled}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {timezones.map((tz) => (
                    <SelectItem key={tz.value} value={tz.value}>
                      <div className="flex items-center gap-2">
                        <Globe className="h-4 w-4" />
                        <span>{tz.label}</span>
                        <span className="text-xs text-muted-foreground">{tz.offset}</span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-3">
              <Label>{t('settings.notifications.quiet-hours-weekdays')}</Label>
              <div className="grid grid-cols-7 gap-2">
                {weekdays.map(([val, key]) => {
                  const day = parseInt(val);
                  return (
                    <div key={val} className="flex flex-col items-center gap-1">
                      <Checkbox
                        id={`weekday-${val}`}
                        checked={quietHours.weekdays.includes(day)}
                        onCheckedChange={(checked) => {
                          const next = checked
                            ? [...quietHours.weekdays, day].sort()
                            : quietHours.weekdays.filter((d) => d !== day);
                          handleUpdate({ weekdays: next });
                        }}
                        disabled={isSaving || legacyDisabled}
                      />
                      <Label
                        htmlFor={`weekday-${val}`}
                        className="text-xs font-normal cursor-pointer"
                      >
                        {t(key).slice(0, 1)}
                      </Label>
                    </div>
                  );
                })}
              </div>
            </div>

            {status && (
              <div className="p-4 bg-muted rounded-lg space-y-1">
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm font-medium">
                    {t('settings.notifications.quiet-hours-status')}
                  </span>
                </div>
                <p className="text-sm text-muted-foreground">{status.message}</p>
                {status.next_notification_time && (
                  <p className="text-xs text-muted-foreground">
                    {new Date(status.next_notification_time).toLocaleString()}
                  </p>
                )}
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}
