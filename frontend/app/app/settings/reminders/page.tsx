'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { Button } from '@/components/ui/button';
import { BookmarkPlus, Star, Clock, Zap, Send, History } from 'lucide-react';
import { toast } from '@/lib/toast';
import { useI18n } from '@/contexts/I18nContext';
import {
  getReminderSettings,
  updateReminderSettings,
  getReminderStats,
  testReminder,
  type ReminderSettings,
  type ReminderStats,
} from '@/lib/api/reminders';

export default function RemindersSettingsPage() {
  const { t } = useI18n();
  const queryClient = useQueryClient();

  // Local state for sliders to provide smooth UX
  const [localCooldown, setLocalCooldown] = useState<number | null>(null);
  const [localSimilarity, setLocalSimilarity] = useState<number | null>(null);
  const [isTestingReminder, setIsTestingReminder] = useState(false);

  const { data: settings, isLoading } = useQuery({
    queryKey: ['reminder-settings'],
    queryFn: getReminderSettings,
  });

  const { data: stats } = useQuery({
    queryKey: ['reminder-stats'],
    queryFn: getReminderStats,
    enabled: !!settings?.reminder_enabled,
  });

  const mutation = useMutation({
    mutationFn: updateReminderSettings,
    onSuccess: (data) => {
      queryClient.setQueryData(['reminder-settings'], data);
      // Clear local state after successful update
      setLocalCooldown(null);
      setLocalSimilarity(null);
      toast.success('Settings saved');
    },
    onError: (e: any) => {
      // Reset local state on error
      setLocalCooldown(null);
      setLocalSimilarity(null);
      toast.error(e?.response?.data?.detail || 'Failed to save settings');
    },
  });

  const update = (patch: Partial<ReminderSettings>) => {
    if (!settings) return;
    mutation.mutate({ ...settings, ...patch });
  };

  const handleTestReminder = async () => {
    setIsTestingReminder(true);
    try {
      const result = await testReminder();
      toast.success(result.message);
    } catch (error: any) {
      toast.error(error?.response?.data?.detail || 'Failed to send test reminder');
    } finally {
      setIsTestingReminder(false);
    }
  };

  if (isLoading || !settings) {
    return (
      <div className="h-40 flex items-center justify-center text-muted-foreground">Loading...</div>
    );
  }

  const displayCooldown = localCooldown ?? settings.reminder_cooldown_hours;
  const displaySimilarity = localSimilarity ?? Math.round(settings.reminder_min_similarity * 100);

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h2 className="text-lg font-semibold">{t('pages.reminders.title')}</h2>
        <p className="text-sm text-muted-foreground mt-1">{t('pages.reminders.description')}</p>
      </div>

      {/* Statistics Card */}
      {settings?.reminder_enabled && stats && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">本週統計</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-muted-foreground">發送次數</p>
                <p className="text-lg font-semibold">{stats.week_sent_count}</p>
              </div>
              <div>
                <p className="text-muted-foreground">點擊率</p>
                <p className="text-lg font-semibold">{stats.click_rate}%</p>
              </div>
            </div>
            {stats.last_reminder_at && (
              <p className="text-xs text-muted-foreground mt-3">
                最近提醒：{new Date(stats.last_reminder_at).toLocaleString('zh-TW')}
                {stats.last_reminder_type === 'add' ? '（加入文章）' : '（評分觸發）'}
              </p>
            )}
            <div className="mt-4 flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleTestReminder}
                disabled={isTestingReminder}
                className="flex-1"
              >
                <Send className="w-4 h-4 mr-2" />
                {isTestingReminder ? '發送中...' : '測試提醒'}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => (window.location.href = '/app/settings/reminders/history')}
                className="flex-1"
              >
                <History className="w-4 h-4 mr-2" />
                查看歷史
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Master toggle */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Zap className="h-5 w-5 text-primary" />
              <div>
                <p className="font-medium">{t('pages.reminders.enable')}</p>
                <p className="text-sm text-muted-foreground">{t('pages.reminders.enable-desc')}</p>
              </div>
            </div>
            <Switch
              checked={settings.reminder_enabled}
              onCheckedChange={(v) => update({ reminder_enabled: v })}
              disabled={mutation.isPending}
            />
          </div>
        </CardContent>
      </Card>

      {/* Triggers */}
      <Card className={!settings.reminder_enabled ? 'opacity-50 pointer-events-none' : ''}>
        <CardHeader>
          <CardTitle className="text-base">{t('pages.reminders.triggers')}</CardTitle>
          <CardDescription>{t('pages.reminders.triggers-desc')}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <BookmarkPlus className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-sm font-medium">{t('pages.reminders.on-add')}</p>
                <p className="text-xs text-muted-foreground">{t('pages.reminders.on-add-desc')}</p>
              </div>
            </div>
            <Switch
              checked={settings.reminder_on_add}
              onCheckedChange={(v) => update({ reminder_on_add: v })}
              disabled={mutation.isPending}
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Star className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-sm font-medium">{t('pages.reminders.on-rate')}</p>
                <p className="text-xs text-muted-foreground">{t('pages.reminders.on-rate-desc')}</p>
              </div>
            </div>
            <Switch
              checked={settings.reminder_on_rate}
              onCheckedChange={(v) => update({ reminder_on_rate: v })}
              disabled={mutation.isPending}
            />
          </div>
        </CardContent>
      </Card>

      {/* Advanced */}
      <Card className={!settings.reminder_enabled ? 'opacity-50 pointer-events-none' : ''}>
        <CardHeader>
          <CardTitle className="text-base">{t('pages.reminders.advanced')}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4 text-muted-foreground" />
                <Label>{t('pages.reminders.cooldown')}</Label>
              </div>
              <span className="text-sm font-medium tabular-nums">
                {displayCooldown === 0
                  ? t('pages.reminders.cooldown-value-none')
                  : t('pages.reminders.cooldown-value', { hours: displayCooldown })}
              </span>
            </div>
            <Slider
              min={0}
              max={24}
              step={1}
              value={[displayCooldown]}
              onValueChange={([v]) => setLocalCooldown(v)}
              onValueCommit={([v]) => {
                update({ reminder_cooldown_hours: v });
              }}
              disabled={mutation.isPending}
            />
            <p className="text-xs text-muted-foreground">{t('pages.reminders.cooldown-desc')}</p>
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Label>{t('pages.reminders.similarity')}</Label>
              <span className="text-sm font-medium tabular-nums">{displaySimilarity}%</span>
            </div>
            <Slider
              min={50}
              max={95}
              step={5}
              value={[displaySimilarity]}
              onValueChange={([v]) => setLocalSimilarity(v)}
              onValueCommit={([v]) => {
                update({ reminder_min_similarity: v / 100 });
              }}
              disabled={mutation.isPending}
            />
            <p className="text-xs text-muted-foreground">{t('pages.reminders.similarity-desc')}</p>
          </div>
        </CardContent>
      </Card>

      <p className="text-xs text-muted-foreground">
        {t('pages.reminders.dm-note', { link: '' }).split('{link}')[0]}
        <a href="/app/settings/notifications" className="underline">
          {t('pages.reminders.dm-note-link')}
        </a>
        {t('pages.reminders.dm-note', { link: '' }).split('{link}')[1]}
      </p>
    </div>
  );
}
