import { apiClient } from './client';

export interface ReminderSettings {
  reminder_enabled: boolean;
  reminder_on_add: boolean;
  reminder_on_rate: boolean;
  reminder_cooldown_hours: number;
  reminder_min_similarity: number;
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
