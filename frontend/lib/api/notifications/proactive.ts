'use client';

import { apiClient } from '../client';

export type ProactiveFrequency = 'daily' | 'every_two_days' | 'weekly';

export interface ProactiveFrequencyData {
  frequency: ProactiveFrequency;
  cooldown_hours: number;
}

export async function getProactiveFrequency(): Promise<ProactiveFrequencyData> {
  const response = await apiClient.get<{ success: boolean; data: ProactiveFrequencyData }>(
    '/api/notifications/proactive-frequency'
  );
  return response.data.data;
}

export async function updateProactiveFrequency(
  frequency: ProactiveFrequency
): Promise<ProactiveFrequencyData> {
  const response = await apiClient.patch<{ success: boolean; data: ProactiveFrequencyData }>(
    '/api/notifications/proactive-frequency',
    { frequency }
  );
  return response.data.data;
}
