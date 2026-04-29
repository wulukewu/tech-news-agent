'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Bell, Clock, Settings, TrendingUp, X, CheckCircle, ExternalLink } from 'lucide-react';
import { toast } from '@/lib/toast';
import {
  getPendingReminders,
  dismissReminder,
  markReminderRead,
  getReminderSettings,
  updateReminderSettings,
  getReminderStats,
  type ReminderResponse,
  type ReminderSettingsResponse,
  type ReminderStatsResponse,
  type ReminderSettingsRequest,
} from '@/lib/api/reminders';

export default function RemindersPage() {
  const [reminders, setReminders] = useState<ReminderResponse[]>([]);
  const [settings, setSettings] = useState<ReminderSettingsResponse | null>(null);
  const [stats, setStats] = useState<ReminderStatsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [remindersData, settingsData, statsData] = await Promise.all([
        getPendingReminders(),
        getReminderSettings(),
        getReminderStats(),
      ]);

      setReminders(remindersData);
      setSettings(settingsData);
      setStats(statsData);
    } catch (error) {
      console.error('Error loading reminders data:', error);
      toast.error('Failed to load reminders data');
    } finally {
      setLoading(false);
    }
  };

  const handleDismissReminder = async (reminderId: string) => {
    try {
      await dismissReminder(reminderId);
      setReminders((prev) => prev.filter((r) => r.id !== reminderId));
      toast.success('Reminder dismissed');
    } catch (error) {
      console.error('Error dismissing reminder:', error);
      toast.error('Failed to dismiss reminder');
    }
  };

  const handleMarkRead = async (reminderId: string) => {
    try {
      await markReminderRead(reminderId);
      setReminders((prev) => prev.map((r) => (r.id === reminderId ? { ...r, status: 'read' } : r)));
      toast.success('Reminder marked as read');
    } catch (error) {
      console.error('Error marking reminder as read:', error);
      toast.error('Failed to mark reminder as read');
    }
  };

  const handleUpdateSettings = async (updates: ReminderSettingsRequest) => {
    try {
      setUpdating(true);
      await updateReminderSettings(updates);

      // Reload settings to get updated values
      const updatedSettings = await getReminderSettings();
      setSettings(updatedSettings);

      toast.success('Settings updated successfully');
    } catch (error) {
      console.error('Error updating settings:', error);
      toast.error('Failed to update settings');
    } finally {
      setUpdating(false);
    }
  };

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'sent':
        return 'bg-blue-100 text-blue-800';
      case 'delivered':
        return 'bg-green-100 text-green-800';
      case 'read':
        return 'bg-gray-100 text-gray-800';
      case 'dismissed':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getReminderTypeIcon = (type: string) => {
    switch (type) {
      case 'article_relation':
        return '📚';
      case 'version_update':
        return '🔄';
      case 'learning_path':
        return '🎯';
      default:
        return '📋';
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center gap-3">
        <Bell className="h-8 w-8 text-blue-600" />
        <div>
          <h1 className="text-3xl font-bold">Intelligent Reminders</h1>
          <p className="text-gray-600">Manage your personalized content reminders</p>
        </div>
      </div>

      <Tabs defaultValue="reminders" className="space-y-6">
        <TabsList>
          <TabsTrigger value="reminders">Active Reminders</TabsTrigger>
          <TabsTrigger value="settings">Settings</TabsTrigger>
          <TabsTrigger value="stats">Statistics</TabsTrigger>
        </TabsList>

        <TabsContent value="reminders" className="space-y-4">
          {reminders.length === 0 ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12">
                <Bell className="h-12 w-12 text-gray-400 mb-4" />
                <h3 className="text-lg font-semibold text-gray-600 mb-2">No active reminders</h3>
                <p className="text-gray-500 text-center">
                  Your intelligent reminders will appear here when new content becomes available.
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4">
              {reminders.map((reminder) => (
                <Card key={reminder.id} className="relative">
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-3">
                        <span className="text-2xl">
                          {getReminderTypeIcon(reminder.reminder_type)}
                        </span>
                        <div className="flex-1">
                          <CardTitle className="text-lg">{reminder.title}</CardTitle>
                          <div className="flex items-center gap-2 mt-1">
                            <Badge className={getStatusColor(reminder.status)}>
                              {reminder.status}
                            </Badge>
                            <span className="text-sm text-gray-500">
                              {formatDateTime(reminder.sent_at)}
                            </span>
                            {reminder.reading_time_estimate && (
                              <span className="text-sm text-gray-500 flex items-center gap-1">
                                <Clock className="h-3 w-3" />
                                {reminder.reading_time_estimate} min
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        {reminder.status !== 'read' && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleMarkRead(reminder.id)}
                          >
                            <CheckCircle className="h-4 w-4" />
                          </Button>
                        )}
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleDismissReminder(reminder.id)}
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-gray-700 mb-4">{reminder.description}</p>
                    {reminder.action_url && (
                      <Button asChild size="sm">
                        <a href={reminder.action_url} target="_blank" rel="noopener noreferrer">
                          <ExternalLink className="h-4 w-4 mr-2" />
                          View Content
                        </a>
                      </Button>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="settings" className="space-y-6">
          {settings && (
            <div className="grid gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Settings className="h-5 w-5" />
                    General Settings
                  </CardTitle>
                  <CardDescription>
                    Configure how and when you receive intelligent reminders
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <Label htmlFor="enabled">Enable Reminders</Label>
                      <p className="text-sm text-gray-500">Turn intelligent reminders on or off</p>
                    </div>
                    <Switch
                      id="enabled"
                      checked={settings.enabled}
                      onCheckedChange={(enabled) => handleUpdateSettings({ enabled })}
                      disabled={updating}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="max-daily">Maximum Daily Reminders</Label>
                    <Input
                      id="max-daily"
                      type="number"
                      min="0"
                      max="20"
                      value={settings.max_daily_reminders}
                      onChange={(e) => {
                        const value = parseInt(e.target.value);
                        if (value >= 0 && value <= 20) {
                          handleUpdateSettings({ max_daily_reminders: value });
                        }
                      }}
                      disabled={updating}
                    />
                    <p className="text-sm text-gray-500">
                      Limit the number of reminders you receive per day (0-20)
                    </p>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="frequency">Reminder Frequency</Label>
                    <Select
                      value={settings.reminder_frequency}
                      onValueChange={(frequency) =>
                        handleUpdateSettings({ reminder_frequency: frequency })
                      }
                      disabled={updating}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="smart">Smart (AI-optimized timing)</SelectItem>
                        <SelectItem value="daily">Daily</SelectItem>
                        <SelectItem value="weekly">Weekly</SelectItem>
                        <SelectItem value="disabled">Disabled</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="quiet-start">Quiet Hours Start</Label>
                      <Input
                        id="quiet-start"
                        type="time"
                        value={settings.quiet_hours_start || ''}
                        onChange={(e) =>
                          handleUpdateSettings({ quiet_hours_start: e.target.value })
                        }
                        disabled={updating}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="quiet-end">Quiet Hours End</Label>
                      <Input
                        id="quiet-end"
                        type="time"
                        value={settings.quiet_hours_end || ''}
                        onChange={(e) => handleUpdateSettings({ quiet_hours_end: e.target.value })}
                        disabled={updating}
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>

        <TabsContent value="stats" className="space-y-6">
          {stats && (
            <div className="grid gap-6">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Card>
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-600">Total Sent</p>
                        <p className="text-2xl font-bold">{stats.total_sent}</p>
                      </div>
                      <Bell className="h-8 w-8 text-blue-600" />
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-600">Click Rate</p>
                        <p className="text-2xl font-bold">{(stats.click_rate * 100).toFixed(1)}%</p>
                      </div>
                      <TrendingUp className="h-8 w-8 text-green-600" />
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-600">Read Rate</p>
                        <p className="text-2xl font-bold">{(stats.read_rate * 100).toFixed(1)}%</p>
                      </div>
                      <CheckCircle className="h-8 w-8 text-blue-600" />
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-600">Dismissed</p>
                        <p className="text-2xl font-bold">{stats.total_dismissed}</p>
                      </div>
                      <X className="h-8 w-8 text-red-600" />
                    </div>
                  </CardContent>
                </Card>
              </div>

              {stats.recommendations.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Recommendations</CardTitle>
                    <CardDescription>
                      AI-generated suggestions to improve your reminder experience
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-2">
                      {stats.recommendations.map((recommendation, index) => (
                        <li key={index} className="flex items-start gap-2">
                          <span className="text-blue-600 mt-1">•</span>
                          <span className="text-gray-700">{recommendation}</span>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              )}

              {(stats.most_effective_channel || stats.most_effective_time !== null) && (
                <Card>
                  <CardHeader>
                    <CardTitle>Optimization Insights</CardTitle>
                    <CardDescription>
                      Data-driven insights about your reminder preferences
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {stats.most_effective_channel && (
                      <div>
                        <p className="font-medium">Most Effective Channel</p>
                        <p className="text-gray-600 capitalize">{stats.most_effective_channel}</p>
                      </div>
                    )}
                    {stats.most_effective_time !== null && (
                      <div>
                        <p className="font-medium">Optimal Time</p>
                        <p className="text-gray-600">{stats.most_effective_time}:00</p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
