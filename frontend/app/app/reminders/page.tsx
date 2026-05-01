'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
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
  dismissReminder,
  batchOperation,
  type IntelligentReminder,
  type IntelligentReminderSettings,
  type IntelligentReminderStats,
} from '@/lib/api/reminders';

export default function RemindersPage() {
  const { isAuthenticated } = useAuth();
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
    <div className="max-w-6xl mx-auto py-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">智能提醒</h1>
        <p className="text-muted-foreground">管理您的個性化文章推薦提醒</p>
      </div>

      {/* Stats Dashboard */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>本週提醒</CardDescription>
              <CardTitle className="text-3xl">{stats.this_week_count}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>已讀率</CardDescription>
              <CardTitle className="text-3xl">{Math.round(stats.read_rate * 100)}%</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>平均優先級</CardDescription>
              <CardTitle className="text-3xl">{Math.round(stats.avg_priority * 100)}%</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>待處理</CardDescription>
              <CardTitle className="text-3xl">{stats.total_pending}</CardTitle>
            </CardHeader>
          </Card>
        </div>
      )}

      {/* Settings Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bell className="w-5 h-5" />
            提醒設定
          </CardTitle>
          <CardDescription>管理您的提醒偏好設定</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">啟用提醒</p>
              <p className="text-sm text-muted-foreground">接收個性化文章推薦</p>
            </div>
            <Button
              variant={settings.enabled ? 'default' : 'outline'}
              size="sm"
              onClick={() => toggleSettings('enabled', !settings.enabled)}
            >
              {settings.enabled ? <Bell className="w-4 h-4" /> : <BellOff className="w-4 h-4" />}
              {settings.enabled ? '已啟用' : '已停用'}
            </Button>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">每日上限</p>
              <p className="text-sm text-muted-foreground">每天最多接收的提醒數量</p>
            </div>
            <Badge variant="outline">每天 {settings.max_daily_reminders} 個</Badge>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">提醒頻率</p>
              <p className="text-sm text-muted-foreground">提醒發送的頻率</p>
            </div>
            <Badge variant="outline">
              {settings.reminder_frequency === 'smart' && '智能'}
              {settings.reminder_frequency === 'daily' && '每日'}
              {settings.reminder_frequency === 'weekly' && '每週'}
            </Badge>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">通知渠道</p>
              <p className="text-sm text-muted-foreground">接收提醒的渠道</p>
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
              <CardTitle>提醒列表</CardTitle>
              <CardDescription>查看和管理您的提醒</CardDescription>
            </div>
            <div className="flex gap-2">
              {selectedIds.size > 0 && (
                <>
                  <Button size="sm" variant="outline" onClick={() => handleBatchOperation('read')}>
                    <CheckCircle className="w-4 h-4 mr-1" />
                    標記已讀 ({selectedIds.size})
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleBatchOperation('dismiss')}
                  >
                    <X className="w-4 h-4 mr-1" />
                    忽略 ({selectedIds.size})
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
                  <SelectItem value="all">全部</SelectItem>
                  <SelectItem value="pending">待處理</SelectItem>
                  <SelectItem value="sent">已發送</SelectItem>
                  <SelectItem value="read">已讀</SelectItem>
                  <SelectItem value="dismissed">已忽略</SelectItem>
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
                  <SelectItem value="sent_at">時間</SelectItem>
                  <SelectItem value="priority_score">優先級</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <Select value={sortOrder} onValueChange={setSortOrder}>
              <SelectTrigger className="w-[120px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="desc">降序</SelectItem>
                <SelectItem value="asc">升序</SelectItem>
              </SelectContent>
            </Select>

            {reminders.length > 0 && (
              <Button size="sm" variant="outline" onClick={toggleSelectAll}>
                <CheckSquare className="w-4 h-4 mr-1" />
                {selectedIds.size === reminders.length ? '取消全選' : '全選'}
              </Button>
            )}
          </div>

          {/* Reminders */}
          {reminders.length === 0 ? (
            <Card className="border-dashed">
              <CardContent className="flex flex-col items-center justify-center py-12">
                <Bell className="w-12 h-12 text-muted-foreground mb-4" />
                <p className="text-lg font-medium mb-2">沒有提醒</p>
                <p className="text-sm text-muted-foreground text-center max-w-md">
                  當系統為您找到相關文章時，會在這裡顯示提醒。
                  <br />
                  繼續閱讀和評分文章，幫助我們了解您的偏好！
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
                              優先級 {Math.round(reminder.reminder_context.priority_score * 100)}%
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
                            預估閱讀時間: ~{reminder.reminder_context.reading_time_estimate} 分鐘
                          </p>
                        )}
                      </div>

                      <div className="flex gap-2">
                        <Button size="sm" variant="outline" onClick={() => markAsRead(reminder.id)}>
                          標記已讀
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => dismissReminderAction(reminder.id)}
                        >
                          忽略
                        </Button>
                      </div>
                    </div>
                  </CardHeader>

                  {reminder.reminder_context.action_url && (
                    <CardContent className="pt-0">
                      <Button variant="default" size="sm" asChild>
                        <a
                          href={reminder.reminder_context.action_url}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          閱讀完整文章
                        </a>
                      </Button>
                    </CardContent>
                  )}
                </Card>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
