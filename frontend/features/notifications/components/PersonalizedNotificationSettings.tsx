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
    onError: (error) => {
      console.error('Failed to fetch notification status:', error);
    },
  });

  // Update preferences mutation
  const updateMutation = useMutation({
    mutationFn: (updates: UpdateUserNotificationPreferencesRequest) =>
      updateNotificationPreferences(updates),
    onMutate: () => {
      setIsSaving(true);
    },
    onSuccess: (updatedPreferences) => {
      queryClient.setQueryData(['notificationPreferences'], updatedPreferences);
      queryClient.invalidateQueries({ queryKey: ['notificationStatus'] });
      // Also invalidate legacy notification settings to ensure consistency
      queryClient.invalidateQueries({ queryKey: ['notificationSettings'] });
      toast.success('通知偏好設定已更新');
      // Update preview with new settings
      updatePreview(updatedPreferences);
    },
    onError: (error: any) => {
      toast.error('更新失敗，請稍後再試');
    },
    onSettled: () => {
      setIsSaving(false);
    },
  });

  // Update preview when preferences change
  const updatePreview = async (prefs: UserNotificationPreferences) => {
    if (prefs.frequency === 'disabled') {
      setPreviewData({
        nextNotificationTime: null,
        localTime: null,
        utcTime: null,
        message: '通知已停用',
      });
      return;
    }

    setIsPreviewLoading(true);
    try {
      const preview = await previewNotificationTime(
        prefs.frequency,
        prefs.notificationTime,
        prefs.timezone
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
        return '每日';
      case 'weekly':
        return '每週';
      case 'monthly':
        return '每月';
      case 'disabled':
        return '停用';
      default:
        return frequency;
    }
  };

  const getFrequencyDescription = (frequency: string) => {
    switch (frequency) {
      case 'daily':
        return '每天在指定時間發送通知';
      case 'weekly':
        return '每週在指定時間發送通知';
      case 'monthly':
        return '每月在指定時間發送通知';
      case 'disabled':
        return '不發送定期通知';
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
        message="無法載入通知偏好設定"
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
              <Clock className="h-5 w-5 text-blue-600" />
              <div>
                <CardTitle>個人化通知設定</CardTitle>
                <CardDescription>自訂您的通知頻率、時間和偏好</CardDescription>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {statusLoading ? (
                <div className="flex items-center gap-2 text-blue-500">
                  <LoadingSpinner size="sm" />
                  <span className="text-sm font-medium">檢查中...</span>
                </div>
              ) : statusError ? (
                <div className="flex items-center gap-2 text-yellow-500">
                  <AlertCircle className="h-4 w-4" />
                  <span className="text-sm font-medium">狀態未知</span>
                </div>
              ) : status?.scheduled ? (
                <div className="flex items-center gap-2 text-green-600">
                  <CheckCircle className="h-4 w-4" />
                  <span className="text-sm font-medium">已排程</span>
                </div>
              ) : preferences.frequency === 'disabled' || !preferences.dmEnabled ? (
                <div className="flex items-center gap-2 text-gray-500">
                  <AlertCircle className="h-4 w-4" />
                  <span className="text-sm font-medium">已停用</span>
                </div>
              ) : (
                <div className="flex items-center gap-2 text-orange-500">
                  <AlertCircle className="h-4 w-4" />
                  <span className="text-sm font-medium">未排程</span>
                </div>
              )}
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Notification Channels */}
      <Card>
        <CardHeader>
          <CardTitle>通知管道</CardTitle>
          <CardDescription>選擇您希望接收通知的方式</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <MessageSquare
                className={`h-5 w-5 ${
                  preferences.dmEnabled ? 'text-green-600' : 'text-muted-foreground'
                }`}
              />
              <div>
                <Label htmlFor="dm-enabled" className="font-medium">
                  Discord 私訊
                </Label>
                <p className="text-sm text-muted-foreground">透過 Discord 私訊接收通知</p>
              </div>
            </div>
            <Switch
              id="dm-enabled"
              checked={preferences.dmEnabled}
              onCheckedChange={(checked) => handleUpdate({ dmEnabled: checked })}
              disabled={isSaving}
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Mail className="h-5 w-5 text-muted-foreground" />
              <div>
                <Label htmlFor="email-enabled" className="font-medium">
                  電子郵件
                  <span className="ml-2 text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded">
                    即將推出
                  </span>
                </Label>
                <p className="text-sm text-muted-foreground">透過電子郵件接收通知</p>
              </div>
            </div>
            <Switch
              id="email-enabled"
              checked={preferences.emailEnabled}
              onCheckedChange={(checked) => handleUpdate({ emailEnabled: checked })}
              disabled={true} // Disabled until email functionality is implemented
            />
          </div>

          <div className="pt-4 border-t">
            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={async () => {
                  try {
                    const { sendTestNotification } = await import('@/lib/api/notifications');
                    await sendTestNotification();
                    toast.success('✅ 測試通知已發送！請檢查您的Discord私訊。');
                  } catch (error: any) {
                    console.error('Test notification failed:', error);

                    // 提供更詳細的錯誤信息
                    if (error?.response?.status === 400) {
                      toast.error('❌ 通知設定有誤，請檢查您的設定');
                    } else if (error?.response?.status === 500) {
                      toast.error('❌ 服務器錯誤，請稍後再試');
                    } else if (error?.message?.includes('Network')) {
                      toast.error('❌ 網絡連接錯誤，請檢查網絡');
                    } else {
                      toast.error('❌ 發送失敗，請稍後再試');
                    }
                  }
                }}
                disabled={isSaving || !preferences.dmEnabled}
                className="flex-1"
              >
                <MessageSquare className="mr-2 h-4 w-4" />
                發送測試通知
              </Button>

              {!status?.scheduled &&
                preferences.frequency !== 'disabled' &&
                preferences.dmEnabled && (
                  <Button
                    variant="outline"
                    onClick={async () => {
                      try {
                        const { rescheduleUserNotification } = await import(
                          '@/lib/api/notifications'
                        );
                        const result = await rescheduleUserNotification();

                        if (result.success) {
                          toast.success(result.message);
                          // Refresh status
                          queryClient.invalidateQueries({ queryKey: ['notificationStatus'] });
                        } else {
                          toast.error(result.message);
                        }
                      } catch (error) {
                        toast.error('重新排程失敗，請稍後再試');
                      }
                    }}
                    disabled={isSaving}
                    className="flex-1"
                  >
                    <Clock className="mr-2 h-4 w-4" />
                    重新排程
                  </Button>
                )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Frequency Settings */}
      <Card>
        <CardHeader>
          <CardTitle>通知頻率</CardTitle>
          <CardDescription>選擇您希望接收通知的頻率</CardDescription>
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
              {['daily', 'weekly', 'monthly', 'disabled'].map((freq) => {
                const Icon = getFrequencyIcon(freq);
                return (
                  <SelectItem key={freq} value={freq}>
                    <div className="flex items-center gap-2">
                      <Icon className="h-4 w-4" />
                      <div>
                        <div className="font-medium">{getFrequencyLabel(freq)}</div>
                        <div className="text-xs text-muted-foreground">
                          {getFrequencyDescription(freq)}
                        </div>
                      </div>
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
            <CardTitle>時間設定</CardTitle>
            <CardDescription>設定您希望接收通知的時間和時區</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="notification-time">通知時間</Label>
                <Input
                  id="notification-time"
                  type="time"
                  value={preferences.notificationTime}
                  onChange={(e) => handleUpdate({ notificationTime: e.target.value })}
                  disabled={isSaving || !preferences.dmEnabled}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="timezone">時區</Label>
                <Select
                  value={preferences.timezone}
                  onValueChange={(value) => handleUpdate({ timezone: value })}
                  disabled={isSaving || !preferences.dmEnabled}
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
          </CardContent>
        </Card>
      )}

      {/* Preview Card */}
      <Card>
        <CardHeader>
          <CardTitle>下次通知預覽</CardTitle>
          <CardDescription>根據您的設定，下次通知將在以下時間發送</CardDescription>
        </CardHeader>
        <CardContent>
          {isPreviewLoading ? (
            <div className="flex items-center gap-2">
              <LoadingSpinner size="sm" />
              <span className="text-sm text-muted-foreground">計算中...</span>
            </div>
          ) : previewData ? (
            <div className="space-y-2">
              <p className="text-sm font-medium">{previewData.message}</p>
              {previewData.localTime && (
                <p className="text-xs text-muted-foreground">
                  UTC 時間: {new Date(previewData.utcTime!).toLocaleString()}
                </p>
              )}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">無法計算下次通知時間</p>
          )}
        </CardContent>
      </Card>

      {/* Status Information */}
      {status && (
        <Card>
          <CardHeader>
            <CardTitle>排程狀態</CardTitle>
            <CardDescription>目前的通知排程狀態</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <p className="text-sm">{status.message}</p>
              {status.nextRunTime && (
                <p className="text-xs text-muted-foreground">
                  下次執行: {new Date(status.nextRunTime).toLocaleString()}
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
