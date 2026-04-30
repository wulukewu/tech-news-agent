import { apiClient } from './client';

export interface ReminderSettings {
  reminder_enabled: boolean;
  reminder_on_add: boolean;
  reminder_on_rate: boolean;
  reminder_cooldown_hours: number;
  reminder_min_similarity: number;
}

export interface ReminderStats {
  week_sent_count: number;
  week_click_count: number;
  click_rate: number;
  last_reminder_at: string | null;
  last_reminder_type: string | null;
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

export async function getReminderStats(): Promise<ReminderStats> {
  const r = await apiClient.get<ReminderStats>('/api/reminders/stats');
  return r.data;
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

export async function getReminderHistory(limit = 20): Promise<{ history: ReminderHistoryItem[] }> {
  const r = await apiClient.get<{ history: ReminderHistoryItem[] }>(
    `/api/reminders/history?limit=${limit}`
  );
  return r.data;
}
