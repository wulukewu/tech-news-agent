'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useI18n } from '@/contexts/I18nContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Bell, BellOff, Clock, CheckCircle, X } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';
import {
  getPendingReminders,
  getIntelligentReminderSettings,
  updateIntelligentReminderSettings,
  markReminderAsRead,
  dismissReminder,
  type IntelligentReminder,
  type IntelligentReminderSettings,
} from '@/lib/api/reminders';

export default function RemindersPage() {
  const { isAuthenticated } = useAuth();
  const { t } = useI18n();
  const [reminders, setReminders] = useState<IntelligentReminder[]>([]);
  const [loading, setLoading] = useState(true);
  const [settings, setSettings] = useState<IntelligentReminderSettings>({
    enabled: true,
    max_daily_reminders: 5,
    preferred_channels: ['discord'],
    timezone: 'UTC',
    reminder_frequency: 'smart',
  });

  useEffect(() => {
    if (isAuthenticated) {
      loadReminders();
      loadSettings();
    }
  }, [isAuthenticated]);

  const loadReminders = async () => {
    try {
      console.log('Loading reminders...');
      const data = await getPendingReminders();
      console.log('Reminders loaded:', data);

      // 去重：根據文章標題去重
      const seen = new Set<string>();
      const uniqueReminders = data.filter((reminder) => {
        const title = reminder.reminder_context.title;
        if (seen.has(title)) return false;
        seen.add(title);
        return true;
      });

      // 限制顯示最多 10 個
      setReminders(uniqueReminders.slice(0, 10));
    } catch (error) {
      console.error('Failed to load reminders:', error);
      // Show user-friendly error
      if (error instanceof Error) {
        console.error('Error details:', error.message);
      }
    } finally {
      setLoading(false);
    }
  };

  const loadSettings = async () => {
    try {
      console.log('Loading settings...');
      const data = await getIntelligentReminderSettings();
      console.log('Settings loaded:', data);
      setSettings(data);
    } catch (error) {
      console.error('Failed to load settings:', error);
      if (error instanceof Error) {
        console.error('Settings error details:', error.message);
      }
    }
  };

  const markAsRead = async (reminderId: string) => {
    try {
      await markReminderAsRead(reminderId);
      setReminders((prev) => prev.map((r) => (r.id === reminderId ? { ...r, status: 'read' } : r)));
    } catch (error) {
      console.error('Failed to mark as read:', error);
    }
  };

  const dismissReminderAction = async (reminderId: string) => {
    try {
      await dismissReminder(reminderId);
      setReminders((prev) =>
        prev.map((r) => (r.id === reminderId ? { ...r, status: 'dismissed' } : r))
      );
    } catch (error) {
      console.error('Failed to dismiss reminder:', error);
    }
  };

  const toggleSettings = async (key: keyof IntelligentReminderSettings, value: any) => {
    try {
      console.log(`Updating setting ${key} to:`, value);
      const updatedSettings = { ...settings, [key]: value };
      setSettings(updatedSettings);

      const result = await updateIntelligentReminderSettings({ [key]: value });
      console.log('Settings update result:', result);
    } catch (error) {
      console.error('Failed to update settings:', error);
      console.error('Error details:', error);
      // Revert on error
      setSettings(settings);
    }
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto py-6 space-y-6">
        <Skeleton className="h-8 w-64" />
        <div className="grid gap-4">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
      </div>
    );
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'read':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'dismissed':
        return <X className="w-4 h-4 text-gray-500" />;
      default:
        return <Clock className="w-4 h-4 text-blue-500" />;
    }
  };

  const getTypeLabel = (type: string) => {
    switch (type) {
      case 'article_relation':
      case 'personalized_article':
        return '相關文章';
      case 'version_update':
        return '版本更新';
      case 'learning_path':
        return '學習路徑';
      default:
        return type;
    }
  };

  return (
    <div className="max-w-4xl mx-auto py-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">{t('pages.reminders.page.title')}</h1>
        <p className="text-muted-foreground">{t('pages.reminders.page.description')}</p>
      </div>

      {/* Settings Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bell className="w-5 h-5" />
            {t('pages.reminders.settings.title')}
          </CardTitle>
          <CardDescription>{t('pages.reminders.settings.description')}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">{t('pages.reminders.settings.enable')}</p>
              <p className="text-sm text-muted-foreground">
                {t('pages.reminders.settings.enable-desc')}
              </p>
            </div>
            <Button
              variant={settings.enabled ? 'default' : 'outline'}
              size="sm"
              onClick={() => toggleSettings('enabled', !settings.enabled)}
            >
              {settings.enabled ? <Bell className="w-4 h-4" /> : <BellOff className="w-4 h-4" />}
              {settings.enabled ? t('common.enabled') : t('common.disabled')}
            </Button>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">{t('pages.reminders.settings.daily-limit')}</p>
              <p className="text-sm text-muted-foreground">
                {t('pages.reminders.settings.daily-limit-desc')}
              </p>
            </div>
            <Badge variant="outline">
              {t('pages.reminders.settings.daily-limit-value', {
                count: settings.max_daily_reminders,
              })}
            </Badge>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">{t('pages.reminders.settings.frequency')}</p>
              <p className="text-sm text-muted-foreground">
                {t('pages.reminders.settings.frequency-desc')}
              </p>
            </div>
            <Badge variant="outline">
              {t(`pages.reminders.frequency.${settings.reminder_frequency}` as any)}
            </Badge>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">{t('pages.reminders.settings.channels')}</p>
              <p className="text-sm text-muted-foreground">
                {t('pages.reminders.settings.channels-desc')}
              </p>
            </div>
            <div className="flex gap-1">
              {settings.preferred_channels.map((channel) => (
                <Badge key={channel} variant="secondary">
                  {channel}
                </Badge>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Reminders List */}
      <div className="space-y-4">
        <h2 className="text-xl font-semibold">{t('pages.reminders.list.title')}</h2>

        {reminders.length === 0 ? (
          <Card>
            <CardContent className="py-8 text-center">
              <Bell className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
              <p className="text-muted-foreground">{t('pages.reminders.list.empty')}</p>
              <p className="text-sm text-muted-foreground mt-2">
                {t('pages.reminders.list.empty-desc')}
              </p>

              {/* Usage Guide */}
              <div className="mt-6 p-4 bg-muted/50 rounded-lg text-left">
                <h3 className="font-semibold mb-3">{t('pages.reminders.usage-guide.title')}</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex items-start gap-2">
                    <span className="text-primary">1.</span>
                    <span>{t('pages.reminders.usage-guide.step-1')}</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <span className="text-primary">2.</span>
                    <span>{t('pages.reminders.usage-guide.step-2')}</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <span className="text-primary">3.</span>
                    <span>{t('pages.reminders.usage-guide.step-3')}</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <span className="text-primary">4.</span>
                    <span>{t('pages.reminders.usage-guide.step-4')}</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ) : (
          reminders.map((reminder) => (
            <Card key={reminder.id} className="transition-all hover:shadow-md">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      {getStatusIcon(reminder.status)}
                      <Badge variant="outline">{getTypeLabel(reminder.reminder_type)}</Badge>
                      <Badge variant="secondary">{reminder.channel}</Badge>
                    </div>
                    <CardTitle className="text-lg">{reminder.reminder_context.title}</CardTitle>
                    <CardDescription>{reminder.reminder_context.description}</CardDescription>
                  </div>

                  {reminder.status === 'sent' && (
                    <div className="flex gap-2">
                      <Button size="sm" variant="outline" onClick={() => markAsRead(reminder.id)}>
                        {t('pages.reminders.actions.mark-read')}
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => dismissReminderAction(reminder.id)}
                      >
                        {t('pages.reminders.actions.dismiss')}
                      </Button>
                    </div>
                  )}
                </div>
              </CardHeader>

              {reminder.reminder_context.related_articles && (
                <CardContent>
                  <div className="space-y-2">
                    <p className="font-medium text-sm">{t('pages.reminders.related-articles')}:</p>
                    {reminder.reminder_context.related_articles.map((article, idx) => (
                      <div key={idx} className="flex items-center gap-2">
                        <span className="text-sm">•</span>
                        <a
                          href={article.url || '#'}
                          className="text-sm text-blue-600 hover:underline"
                        >
                          {article.title}
                        </a>
                        {article.confidence && (
                          <Badge variant="outline" className="text-xs">
                            {t('pages.reminders.match-percentage', {
                              percentage: Math.round(article.confidence * 100),
                            })}
                          </Badge>
                        )}
                      </div>
                    ))}
                    {reminder.reminder_context.reading_time_estimate && (
                      <p className="text-xs text-muted-foreground mt-2">
                        {t('pages.reminders.reading-time', {
                          minutes: reminder.reminder_context.reading_time_estimate,
                        })}
                      </p>
                    )}
                  </div>
                </CardContent>
              )}

              {reminder.reminder_context.version_info && (
                <CardContent>
                  <div className="space-y-2">
                    <p className="font-medium text-sm">{t('pages.reminders.version-update')}:</p>
                    <div className="flex items-center gap-2">
                      <Badge variant="outline">
                        {reminder.reminder_context.version_info.technology}
                      </Badge>
                      <span className="text-sm">
                        {reminder.reminder_context.version_info.old_version} →{' '}
                        {reminder.reminder_context.version_info.new_version}
                      </span>
                      {reminder.reminder_context.version_info.breaking_changes && (
                        <Badge variant="destructive" className="text-xs">
                          {t('pages.reminders.breaking-changes')}
                        </Badge>
                      )}
                    </div>
                  </div>
                </CardContent>
              )}
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
