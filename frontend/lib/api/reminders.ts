/**
 * API client for intelligent reminders
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface ReminderResponse {
  id: string;
  reminder_type: string;
  title: string;
  description: string;
  sent_at: string;
  status: string;
  priority_score: number;
  reading_time_estimate?: number;
  action_url?: string;
}

export interface ReminderSettingsRequest {
  enabled?: boolean;
  max_daily_reminders?: number;
  preferred_channels?: string[];
  quiet_hours_start?: string; // HH:MM format
  quiet_hours_end?: string; // HH:MM format
  timezone?: string;
  reminder_frequency?: string;
}

export interface ReminderSettingsResponse {
  enabled: boolean;
  max_daily_reminders: number;
  preferred_channels: string[];
  quiet_hours_start?: string;
  quiet_hours_end?: string;
  timezone: string;
  reminder_frequency: string;
}

export interface ReminderStatsResponse {
  total_sent: number;
  total_clicked: number;
  total_read: number;
  total_dismissed: number;
  click_rate: number;
  read_rate: number;
  most_effective_channel?: string;
  most_effective_time?: number;
  recommendations: string[];
}

/**
 * Get pending reminders for the current user
 */
export async function getPendingReminders(): Promise<ReminderResponse[]> {
  const response = await fetch(`${API_BASE}/api/reminders/pending`, {
    credentials: 'include',
  });

  if (!response.ok) {
    throw new Error('Failed to fetch pending reminders');
  }

  return response.json();
}

/**
 * Dismiss a reminder
 */
export async function dismissReminder(reminderId: string): Promise<void> {
  const response = await fetch(`${API_BASE}/api/reminders/${reminderId}/dismiss`, {
    method: 'POST',
    credentials: 'include',
  });

  if (!response.ok) {
    throw new Error('Failed to dismiss reminder');
  }
}

/**
 * Mark a reminder as read
 */
export async function markReminderRead(reminderId: string): Promise<void> {
  const response = await fetch(`${API_BASE}/api/reminders/${reminderId}/read`, {
    method: 'POST',
    credentials: 'include',
  });

  if (!response.ok) {
    throw new Error('Failed to mark reminder as read');
  }
}

/**
 * Get user's reminder settings
 */
export async function getReminderSettings(): Promise<ReminderSettingsResponse> {
  const response = await fetch(`${API_BASE}/api/reminders/settings`, {
    credentials: 'include',
  });

  if (!response.ok) {
    throw new Error('Failed to fetch reminder settings');
  }

  return response.json();
}

/**
 * Update user's reminder settings
 */
export async function updateReminderSettings(settings: ReminderSettingsRequest): Promise<void> {
  const response = await fetch(`${API_BASE}/api/reminders/settings`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify(settings),
  });

  if (!response.ok) {
    throw new Error('Failed to update reminder settings');
  }
}

/**
 * Get reminder effectiveness statistics
 */
export async function getReminderStats(): Promise<ReminderStatsResponse> {
  const response = await fetch(`${API_BASE}/api/reminders/stats`, {
    credentials: 'include',
  });

  if (!response.ok) {
    throw new Error('Failed to fetch reminder statistics');
  }

  return response.json();
}

/**
 * Trigger manual analysis (for testing)
 */
export async function triggerManualAnalysis(articleId?: string): Promise<void> {
  const url = articleId
    ? `${API_BASE}/api/reminders/trigger-analysis?article_id=${articleId}`
    : `${API_BASE}/api/reminders/trigger-analysis`;

  const response = await fetch(url, {
    method: 'POST',
    credentials: 'include',
  });

  if (!response.ok) {
    throw new Error('Failed to trigger manual analysis');
  }
}

/**
 * Send pending reminders (for testing)
 */
export async function sendPendingReminders(): Promise<void> {
  const response = await fetch(`${API_BASE}/api/reminders/send-pending`, {
    method: 'POST',
    credentials: 'include',
  });

  if (!response.ok) {
    throw new Error('Failed to send pending reminders');
  }
}
