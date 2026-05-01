import { apiClient } from './client';

// Legacy reminder settings (keep for compatibility)
export interface ReminderSettings {
  reminder_enabled: boolean;
  reminder_on_add: boolean;
  reminder_on_rate: boolean;
  reminder_cooldown_hours: number;
  reminder_min_similarity: number;
}

// New intelligent reminder interfaces
export interface IntelligentReminderSettings {
  enabled: boolean;
  max_daily_reminders: number;
  preferred_channels: string[];
  quiet_hours_start?: string;
  quiet_hours_end?: string;
  timezone: string;
  reminder_frequency: 'smart' | 'daily' | 'weekly' | 'disabled';
}

export interface IntelligentReminder {
  id: string;
  reminder_type: 'article_relation' | 'version_update' | 'learning_path';
  reminder_context: {
    title: string;
    description: string;
    related_articles?: Array<{
      title: string;
      url?: string;
      summary?: string;
      relationship?: string;
      confidence?: number;
    }>;
    version_info?: {
      technology: string;
      old_version: string;
      new_version: string;
      version_type: string;
      breaking_changes: boolean;
      impact_level: string;
    };
    reading_time_estimate?: number;
    priority_score: number;
    action_url?: string;
  };
  sent_at: string;
  channel: 'discord' | 'web' | 'email';
  status: 'sent' | 'delivered' | 'read' | 'clicked' | 'dismissed' | 'failed';
  response_time?: number;
  effectiveness_score?: number;
}

export interface ReminderStats {
  week_sent_count: number;
  week_click_count: number;
  click_rate: number;
  last_reminder_at: string | null;
  last_reminder_type: string | null;
}

// Intelligent Reminder API functions
export async function getPendingReminders(
  status?: string,
  sortBy?: string,
  sortOrder?: string
): Promise<IntelligentReminder[]> {
  try {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (sortBy) params.append('sort_by', sortBy);
    if (sortOrder) params.append('sort_order', sortOrder);

    const url = `/api/intelligent-reminders/pending${params.toString() ? `?${params.toString()}` : ''}`;
    const r = await apiClient.get<{ reminders: IntelligentReminder[] }>(url);
    return r.data.reminders || [];
  } catch (error: unknown) {
    console.error('Failed to fetch pending reminders:', error);
    return [];
  }
}

export async function getIntelligentReminderSettings(): Promise<IntelligentReminderSettings> {
  try {
    const r = await apiClient.get<IntelligentReminderSettings>(
      '/api/intelligent-reminders/settings'
    );
    return r.data;
  } catch (error: unknown) {
    console.error('Failed to fetch reminder settings:', error);
    return {
      enabled: true,
      max_daily_reminders: 5,
      preferred_channels: ['discord'],
      timezone: 'UTC',
      reminder_frequency: 'smart',
    };
  }
}

export async function updateIntelligentReminderSettings(
  settings: Partial<IntelligentReminderSettings>
): Promise<IntelligentReminderSettings> {
  const r = await apiClient.put<IntelligentReminderSettings>(
    '/api/intelligent-reminders/settings',
    settings
  );
  return r.data;
}

export async function markReminderAsRead(reminderId: string): Promise<void> {
  await apiClient.post(`/api/intelligent-reminders/${reminderId}/read`);
}

export async function dismissReminder(reminderId: string): Promise<void> {
  await apiClient.post(`/api/intelligent-reminders/${reminderId}/dismiss`);
}

export interface IntelligentReminderStats {
  total_sent: number;
  total_clicked: number;
  total_read: number;
  total_dismissed: number;
  total_pending: number;
  click_rate: number;
  read_rate: number;
  avg_priority: number;
  this_week_count: number;
  top_categories: Array<{ name: string; count: number }>;
  most_effective_channel: string;
  most_effective_time: number;
  recommendations: string[];
}

export async function getIntelligentReminderStats(): Promise<IntelligentReminderStats> {
  try {
    const r = await apiClient.get<IntelligentReminderStats>('/api/intelligent-reminders/stats');
    return r.data;
  } catch (error: unknown) {
    console.error('Failed to fetch reminder stats:', error);
    return {
      total_sent: 0,
      total_clicked: 0,
      total_read: 0,
      total_dismissed: 0,
      total_pending: 0,
      click_rate: 0,
      read_rate: 0,
      avg_priority: 0,
      this_week_count: 0,
      top_categories: [],
      most_effective_channel: 'discord',
      most_effective_time: 10,
      recommendations: [],
    };
  }
}

export async function batchOperation(
  reminderIds: string[],
  action: 'read' | 'dismiss'
): Promise<{ message: string; count: number }> {
  const r = await apiClient.post<{ message: string; count: number }>(
    '/api/intelligent-reminders/batch',
    {
      reminder_ids: reminderIds,
      action,
    }
  );
  return r.data;
}

export async function getPendingRemindersCount(): Promise<number> {
  try {
    const reminders = await getPendingReminders();
    return reminders.length;
  } catch {
    return 0;
  }
}

// Legacy functions (keep for compatibility)
export async function getReminderSettings(): Promise<ReminderSettings> {
  const r = await apiClient.get<ReminderSettings>('/api/reminders/settings');
  return r.data;
}

export async function updateReminderSettings(
  settings: ReminderSettings
): Promise<ReminderSettings> {
  const r = await apiClient.put<ReminderSettings>('/api/reminders/settings', settings);
  return r.data;
}

export interface ReminderHistoryItem {
  sent_at: string;
  trigger_type: string;
  similarity_score: number;
  clicked_at: string | null;
  user_feedback: string | null;
  trigger_article: { title: string };
  recommended_article: { title: string; url: string };
}

export async function testReminder(): Promise<{ message: string }> {
  const r = await apiClient.post<{ message: string }>('/api/reminders/test');
  return r.data;
}

export async function submitFeedback(
  articleId: string,
  feedback: 'accurate' | 'inaccurate' | 'not_interested'
): Promise<{ message: string }> {
  const r = await apiClient.post<{ message: string }>('/api/reminders/feedback', {
    article_id: articleId,
    feedback,
  });
  return r.data;
}

// Legacy ReminderStats interface for compatibility
export interface LegacyReminderStats {
  week_sent_count: number;
  week_click_count: number;
  click_rate: number;
  last_reminder_at: string | null;
  last_reminder_type: string | null;
}

export async function getReminderStats(): Promise<ReminderStats> {
  try {
    const intelligentStats = await getIntelligentReminderStats();
    // Convert new format to legacy format
    return {
      week_sent_count: intelligentStats.this_week_count,
      week_click_count: Math.round(intelligentStats.this_week_count * intelligentStats.click_rate),
      click_rate: intelligentStats.click_rate,
      last_reminder_at: null, // Not available in new format
      last_reminder_type: null, // Not available in new format
    } as ReminderStats;
  } catch (error: unknown) {
    console.error('Failed to get reminder stats:', error);
    return {
      week_sent_count: 0,
      week_click_count: 0,
      click_rate: 0,
      last_reminder_at: null,
      last_reminder_type: null,
    } as ReminderStats;
  }
}

export async function getReminderHistory(limit = 20): Promise<{ history: ReminderHistoryItem[] }> {
  const r = await apiClient.get<{ history: ReminderHistoryItem[] }>(
    `/api/reminders/history?limit=${limit}`
  );
  return r.data;
}
