'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useI18n } from '@/contexts/I18nContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Bell,
  BellOff,
  Clock,
  CheckCircle,
  X,
  Filter,
  ArrowUpDown,
  CheckSquare,
} from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  getPendingReminders,
  getIntelligentReminderSettings,
  getIntelligentReminderStats,
  updateIntelligentReminderSettings,
  markReminderAsRead,
  markReminderAsUnread,
  dismissReminder,
  batchOperation,
  type IntelligentReminder,
  type IntelligentReminderSettings,
  type IntelligentReminderStats,
} from '@/lib/api/reminders';

export default function RemindersPage() {
  const { isAuthenticated } = useAuth();
  const { t } = useI18n();
  // Helper to bypass TypeScript strict checking for dynamic translation keys
  const tr = (key: string, params?: Record<string, any>) => t(key as any, params);
  const [reminders, setReminders] = useState<IntelligentReminder[]>([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<IntelligentReminderStats | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [sortBy, setSortBy] = useState<string>('sent_at');
  const [sortOrder, setSortOrder] = useState<string>('desc');
  const [settings, setSettings] = useState<IntelligentReminderSettings>({
    enabled: true,
    max_daily_reminders: 5,
    preferred_channels: ['discord'],
    timezone: 'UTC',
    reminder_frequency: 'smart',
  });

  useEffect(() => {
    if (isAuthenticated) {
      loadData();
    }
  }, [isAuthenticated, statusFilter, sortBy, sortOrder]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [remindersData, settingsData, statsData] = await Promise.all([
        getPendingReminders(statusFilter, sortBy, sortOrder),
        getIntelligentReminderSettings(),
        getIntelligentReminderStats(),
      ]);

      const seen = new Set<string>();
      const uniqueReminders = remindersData.filter((reminder) => {
        const title = reminder.reminder_context.title;
        if (seen.has(title)) return false;
        seen.add(title);
        return true;
      });

      setReminders(uniqueReminders);
      setSettings(settingsData);
      setStats(statsData);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const markAsRead = async (reminderId: string) => {
    try {
      await markReminderAsRead(reminderId);
      // Auto-hide after marking as read
      if (statusFilter === 'all' || statusFilter === 'sent' || statusFilter === 'pending') {
        // Remove from list if not viewing "read" filter
        setReminders((prev) => prev.filter((r) => r.id !== reminderId));
      } else {
        // Update status if viewing "read" filter
        setReminders((prev) =>
          prev.map((r) => (r.id === reminderId ? { ...r, status: 'read' } : r))
        );
      }
    } catch (error) {
      console.error('Failed to mark as read:', error);
    }
  };

  const markAsUnread = async (reminderId: string) => {
    try {
      await markReminderAsUnread(reminderId);
      setReminders((prev) => prev.map((r) => (r.id === reminderId ? { ...r, status: 'sent' } : r)));
    } catch (error) {
      console.error('Failed to mark as unread:', error);
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

  const handleBatchOperation = async (action: 'read' | 'dismiss') => {
    if (selectedIds.size === 0) return;

    try {
      await batchOperation(Array.from(selectedIds), action);
      const newStatus = action === 'read' ? 'read' : 'dismissed';
      setReminders((prev) =>
        prev.map((r) => (selectedIds.has(r.id) ? { ...r, status: newStatus } : r))
      );
      setSelectedIds(new Set());
    } catch (error) {
      console.error(`Failed to ${action} reminders:`, error);
    }
  };

  const toggleSelectAll = () => {
    if (selectedIds.size === reminders.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(reminders.map((r) => r.id)));
    }
  };

  const toggleSelect = (id: string) => {
    const newSelected = new Set(selectedIds);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelectedIds(newSelected);
  };

  const toggleSettings = async (key: keyof IntelligentReminderSettings, value: any) => {
    try {
      const updatedSettings = { ...settings, [key]: value };
      setSettings(updatedSettings);
      await updateIntelligentReminderSettings({ [key]: value });
    } catch (error) {
      console.error('Failed to update settings:', error);
      setSettings(settings);
    }
  };

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto py-6 space-y-6">
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
    const typeMap: Record<string, string> = {
      article_relation: tr('pages.reminders.types.article-relation'),
      personalized_article: tr('pages.reminders.types.personalized-article'),
      version_update: tr('pages.reminders.types.version-update'),
      learning_path: tr('pages.reminders.types.learning-path'),
    };
    return typeMap[type] || type;
  };

  return (
    <div className="max-w-6xl mx-auto py-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">{tr('pages.reminders.title')}</h1>
        <p className="text-muted-foreground">{tr('pages.reminders.description')}</p>
      </div>

      {/* Stats Dashboard */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-3">
              <CardDescription className="text-sm">
                {tr('pages.reminders.stats.this-week')}
              </CardDescription>
              <CardTitle className="text-3xl font-bold">{stats.this_week_count}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription className="text-sm">
                {tr('pages.reminders.stats.read-rate')}
              </CardDescription>
              <CardTitle className="text-3xl font-bold">
                {Math.round(stats.read_rate * 100)}%
              </CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription className="text-sm">
                {tr('pages.reminders.stats.avg-priority')}
              </CardDescription>
              <CardTitle className="text-3xl font-bold">
                {Math.round(stats.avg_priority * 100)}%
              </CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription className="text-sm">
                {tr('pages.reminders.stats.pending')}
              </CardDescription>
              <CardTitle className="text-3xl font-bold">{stats.total_pending}</CardTitle>
            </CardHeader>
          </Card>
        </div>
      )}

      {/* Settings Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bell className="w-5 h-5" />
            {tr('pages.reminders.settings.title')}
          </CardTitle>
          <CardDescription>{tr('pages.reminders.settings.description')}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">{tr('pages.reminders.settings.enable')}</p>
              <p className="text-sm text-muted-foreground">
                {tr('pages.reminders.settings.enable-desc')}
              </p>
            </div>
            <Button
              variant={settings.enabled ? 'default' : 'outline'}
              size="sm"
              onClick={() => toggleSettings('enabled', !settings.enabled)}
            >
              {settings.enabled ? <Bell className="w-4 h-4" /> : <BellOff className="w-4 h-4" />}
              {settings.enabled ? tr('common.enabled') : tr('common.disabled')}
            </Button>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">{tr('pages.reminders.settings.daily-limit')}</p>
              <p className="text-sm text-muted-foreground">
                {tr('pages.reminders.settings.daily-limit-desc')}
              </p>
            </div>
            <Badge variant="outline">
              {tr('pages.reminders.settings.daily-limit-value', {
                count: settings.max_daily_reminders,
              })}
            </Badge>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">{tr('pages.reminders.settings.frequency')}</p>
              <p className="text-sm text-muted-foreground">
                {tr('pages.reminders.settings.frequency-desc')}
              </p>
            </div>
            <Badge variant="outline">
              {t(`pages.reminders.frequency.${settings.reminder_frequency}` as any)}
            </Badge>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">{tr('pages.reminders.settings.channels')}</p>
              <p className="text-sm text-muted-foreground">
                {tr('pages.reminders.settings.channels-desc')}
              </p>
            </div>
            <div className="flex gap-2">
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
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div>
              <CardTitle>{tr('pages.reminders.list.title')}</CardTitle>
              <CardDescription>{tr('pages.reminders.list.description')}</CardDescription>
            </div>
            <div className="flex gap-2">
              {selectedIds.size > 0 && (
                <>
                  <Button size="sm" variant="outline" onClick={() => handleBatchOperation('read')}>
                    <CheckCircle className="w-4 h-4 mr-1" />
                    {tr('pages.reminders.actions.batch-read', { count: selectedIds.size })}
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleBatchOperation('dismiss')}
                  >
                    <X className="w-4 h-4 mr-1" />
                    {tr('pages.reminders.actions.batch-dismiss', { count: selectedIds.size })}
                  </Button>
                </>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Filters */}
          <div className="flex gap-4 flex-wrap">
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4" />
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-[150px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">{tr('pages.reminders.filters.all')}</SelectItem>
                  <SelectItem value="pending">{tr('pages.reminders.filters.pending')}</SelectItem>
                  <SelectItem value="sent">{tr('pages.reminders.filters.sent')}</SelectItem>
                  <SelectItem value="read">{tr('pages.reminders.filters.read')}</SelectItem>
                  <SelectItem value="dismissed">
                    {tr('pages.reminders.filters.dismissed')}
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-center gap-2">
              <ArrowUpDown className="w-4 h-4" />
              <Select value={sortBy} onValueChange={setSortBy}>
                <SelectTrigger className="w-[150px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="sent_at">{tr('pages.reminders.sort.time')}</SelectItem>
                  <SelectItem value="priority_score">
                    {tr('pages.reminders.sort.priority')}
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>

            <Select value={sortOrder} onValueChange={setSortOrder}>
              <SelectTrigger className="w-[120px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="desc">{tr('pages.reminders.sort.desc')}</SelectItem>
                <SelectItem value="asc">{tr('pages.reminders.sort.asc')}</SelectItem>
              </SelectContent>
            </Select>

            {reminders.length > 0 && (
              <Button size="sm" variant="outline" onClick={toggleSelectAll}>
                <CheckSquare className="w-4 h-4 mr-1" />
                {selectedIds.size === reminders.length
                  ? tr('pages.reminders.actions.deselect-all')
                  : tr('pages.reminders.actions.select-all')}
              </Button>
            )}
          </div>

          {/* Reminders */}
          {reminders.length === 0 ? (
            <Card className="border-dashed">
              <CardContent className="flex flex-col items-center justify-center py-12">
                <Bell className="w-12 h-12 text-muted-foreground mb-4" />
                <p className="text-lg font-medium mb-2">{tr('pages.reminders.empty.title')}</p>
                <p className="text-sm text-muted-foreground text-center max-w-md">
                  {tr('pages.reminders.empty.description')}
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {reminders.map((reminder) => (
                <Card
                  key={reminder.id}
                  className={`transition-all hover:shadow-md ${selectedIds.has(reminder.id) ? 'ring-2 ring-primary' : ''}`}
                >
                  <CardHeader>
                    <div className="flex items-start gap-4">
                      <Checkbox
                        checked={selectedIds.has(reminder.id)}
                        onCheckedChange={() => toggleSelect(reminder.id)}
                        className="mt-1"
                      />
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2 flex-wrap">
                          {getStatusIcon(reminder.status)}
                          <Badge variant="outline">{getTypeLabel(reminder.reminder_type)}</Badge>
                          <Badge variant="secondary">{reminder.channel}</Badge>
                          {reminder.reminder_context.priority_score !== undefined && (
                            <Badge
                              variant={
                                reminder.reminder_context.priority_score >= 0.8
                                  ? 'default'
                                  : reminder.reminder_context.priority_score >= 0.6
                                    ? 'secondary'
                                    : 'outline'
                              }
                            >
                              {tr('pages.reminders.priority-label')}{' '}
                              {Math.round(reminder.reminder_context.priority_score * 100)}%
                            </Badge>
                          )}
                        </div>
                        {reminder.reminder_context.action_url ? (
                          <a
                            href={reminder.reminder_context.action_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="hover:underline"
                          >
                            <CardTitle className="text-lg text-primary">
                              {reminder.reminder_context.title}
                            </CardTitle>
                          </a>
                        ) : (
                          <CardTitle className="text-lg">
                            {reminder.reminder_context.title}
                          </CardTitle>
                        )}
                        <CardDescription className="mt-2">
                          {reminder.reminder_context.description}
                        </CardDescription>
                        {reminder.reminder_context.reading_time_estimate && (
                          <p className="text-xs text-muted-foreground mt-2">
                            {tr('pages.reminders.reading-time', {
                              minutes: reminder.reminder_context.reading_time_estimate,
                            })}
                          </p>
                        )}
                      </div>

                      <div className="flex gap-2">
                        {reminder.status === 'read' ? (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => markAsUnread(reminder.id)}
                          >
                            {tr('pages.reminders.actions.mark-unread')}
                          </Button>
                        ) : (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => markAsRead(reminder.id)}
                          >
                            {tr('pages.reminders.actions.mark-read')}
                          </Button>
                        )}
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => dismissReminderAction(reminder.id)}
                        >
                          {tr('pages.reminders.actions.dismiss')}
                        </Button>
                      </div>
                    </div>
                  </CardHeader>
                </Card>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
