'use client';

import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
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
import { Moon, Clock, Globe, Calendar, AlertCircle, CheckCircle } from 'lucide-react';
import {
  getQuietHours,
  updateQuietHours,
  getQuietHoursStatus,
  getSupportedTimezones,
  QuietHoursSettings as QuietHoursSettingsType,
  QuietHoursStatus,
} from '@/lib/api/notifications';

interface QuietHoursSettingsProps {
  quietHours?: {
    enabled: boolean;
    start: string;
    end: string;
  };
  onQuietHoursChange?: (quietHours: { enabled: boolean; start: string; end: string }) => void;
  disabled?: boolean;
}

export function QuietHoursSettings({
  quietHours: legacyQuietHours,
  onQuietHoursChange: legacyOnChange,
  disabled: legacyDisabled = false,
}: QuietHoursSettingsProps) {
  const queryClient = useQueryClient();
  const [isSaving, setIsSaving] = useState(false);

  // Fetch quiet hours settings
  const {
    data: quietHours,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['quietHours'],
    queryFn: getQuietHours,
    staleTime: 0,
  });

  // Fetch quiet hours status
  const { data: status, isLoading: statusLoading } = useQuery({
    queryKey: ['quietHoursStatus'],
    queryFn: getQuietHoursStatus,
    refetchInterval: 60000, // Refetch every minute
    staleTime: 30000,
  });

  // Fetch supported timezones
  const { data: timezones = [] } = useQuery({
    queryKey: ['supportedTimezones'],
    queryFn: getSupportedTimezones,
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
  });

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: updateQuietHours,
    onMutate: () => {
      setIsSaving(true);
    },
    onSuccess: (updatedSettings) => {
      queryClient.setQueryData(['quietHours'], updatedSettings);
      queryClient.invalidateQueries({ queryKey: ['quietHoursStatus'] });
      toast.success('勿擾時段設定已更新');

      // Call legacy callback if provided
      if (legacyOnChange) {
        legacyOnChange({
          enabled: updatedSettings.enabled,
          start: updatedSettings.start_time.substring(0, 5), // HH:MM format
          end: updatedSettings.end_time.substring(0, 5),
        });
      }
    },
    onError: (error: any) => {
      toast.error('更新失敗，請稍後再試');
    },
    onSettled: () => {
      setIsSaving(false);
    },
  });

  const handleUpdate = (updates: Partial<QuietHoursSettingsType>) => {
    updateMutation.mutate(updates);
  };

  const getWeekdayLabel = (day: number) => {
    const labels = ['', '週一', '週二', '週三', '週四', '週五', '週六', '週日'];
    return labels[day];
  };

  const formatTime = (timeStr: string) => {
    return timeStr.substring(0, 5); // Convert HH:MM:SS to HH:MM
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Moon className="h-5 w-5" />
            勿擾時段
          </CardTitle>
          <CardDescription>設定您不希望接收通知的時段</CardDescription>
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
            勿擾時段
          </CardTitle>
          <CardDescription>設定您不希望接收通知的時段</CardDescription>
        </CardHeader>
        <CardContent>
          <ErrorMessage
            message="無法載入勿擾時段設定"
            onRetry={() => queryClient.invalidateQueries({ queryKey: ['quietHours'] })}
          />
        </CardContent>
      </Card>
    );
  }

  if (!quietHours) {
    return null;
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Moon className="h-5 w-5 text-muted-foreground" />
            <div>
              <CardTitle>勿擾時段</CardTitle>
              <CardDescription>設定您不希望接收通知的時段</CardDescription>
            </div>
          </div>
          <div className="flex items-center gap-2 text-sm">
            {statusLoading ? (
              <span className="text-muted-foreground flex items-center gap-1.5">
                <LoadingSpinner size="sm" />
                檢查中...
              </span>
            ) : status?.is_in_quiet_hours ? (
              <span className="text-orange-600 dark:text-orange-400 flex items-center gap-1.5">
                <Moon className="h-4 w-4" />
                勿擾中
              </span>
            ) : quietHours.enabled ? (
              <span className="text-green-600 dark:text-green-400 flex items-center gap-1.5">
                <CheckCircle className="h-4 w-4" />
                已啟用
              </span>
            ) : (
              <span className="text-muted-foreground flex items-center gap-1.5">
                <AlertCircle className="h-4 w-4" />
                已停用
              </span>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Enable/Disable Switch */}
        <div className="flex items-center justify-between">
          <div className="space-y-0.5">
            <Label htmlFor="quiet-hours-enabled">啟用勿擾時段</Label>
            <p className="text-sm text-muted-foreground">在指定時段內暫停通知</p>
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
            {/* Time Range */}
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="quiet-hours-start">開始時間</Label>
                  <Input
                    id="quiet-hours-start"
                    type="time"
                    value={formatTime(quietHours.start_time)}
                    onChange={(e) => handleUpdate({ start_time: e.target.value + ':00' })}
                    disabled={isSaving || legacyDisabled}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="quiet-hours-end">結束時間</Label>
                  <Input
                    id="quiet-hours-end"
                    type="time"
                    value={formatTime(quietHours.end_time)}
                    onChange={(e) => handleUpdate({ end_time: e.target.value + ':00' })}
                    disabled={isSaving || legacyDisabled}
                  />
                </div>
              </div>

              {/* Timezone */}
              <div className="space-y-2">
                <Label htmlFor="quiet-hours-timezone">時區</Label>
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
            </div>

            {/* Weekdays */}
            <div className="space-y-3">
              <Label>適用日期</Label>
              <div className="grid grid-cols-7 gap-2">
                {[1, 2, 3, 4, 5, 6, 7].map((day) => (
                  <div key={day} className="flex items-center space-x-2">
                    <Checkbox
                      id={`weekday-${day}`}
                      checked={quietHours.weekdays.includes(day)}
                      onCheckedChange={(checked) => {
                        const newWeekdays = checked
                          ? [...quietHours.weekdays, day].sort()
                          : quietHours.weekdays.filter((d) => d !== day);
                        handleUpdate({ weekdays: newWeekdays });
                      }}
                      disabled={isSaving || legacyDisabled}
                    />
                    <Label
                      htmlFor={`weekday-${day}`}
                      className="text-sm font-normal cursor-pointer"
                    >
                      {getWeekdayLabel(day)}
                    </Label>
                  </div>
                ))}
              </div>
            </div>

            {/* Status Information */}
            {status && (
              <div className="p-4 bg-muted rounded-lg space-y-2">
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm font-medium">目前狀態</span>
                </div>
                <p className="text-sm text-muted-foreground">{status.message}</p>
                <p className="text-xs text-muted-foreground">目前時間: {status.current_time}</p>
                {status.next_notification_time && (
                  <p className="text-xs text-muted-foreground">
                    下次可發送通知: {new Date(status.next_notification_time).toLocaleString()}
                  </p>
                )}
              </div>
            )}

            {/* Preview */}
            <div className="p-3 bg-muted rounded-lg">
              <p className="text-sm text-muted-foreground">
                通知將在 {formatTime(quietHours.start_time)} 至 {formatTime(quietHours.end_time)}{' '}
                期間暫停
                {quietHours.weekdays.length < 7 && (
                  <span className="block mt-1">
                    適用於: {quietHours.weekdays.map(getWeekdayLabel).join('、')}
                  </span>
                )}
              </p>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
