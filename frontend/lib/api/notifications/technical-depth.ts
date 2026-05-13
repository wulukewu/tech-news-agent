'use client';

import { apiClient } from '../client';
import { TechnicalDepthSettings, TechnicalDepthLevel, TechnicalDepthStats } from './quiet-hours';

/**
 * Get user's technical depth settings
 *
 * @returns Promise<TechnicalDepthSettings> - Technical depth settings
 * @throws Error if request fails
 */
export async function getTechnicalDepthSettings(): Promise<TechnicalDepthSettings> {
  const response = await apiClient.get<{
    success: boolean;
    data: TechnicalDepthSettings;
  }>('/api/notifications/tech-depth');
  return response.data.data;
}

/**
 * Update user's technical depth settings
 *
 * @param updates - Updated technical depth settings
 * @returns Promise<TechnicalDepthSettings> - Updated technical depth settings
 * @throws Error if request fails
 */
export async function updateTechnicalDepthSettings(
  updates: Partial<TechnicalDepthSettings>
): Promise<TechnicalDepthSettings> {
  const response = await apiClient.put<{
    success: boolean;
    data: TechnicalDepthSettings;
  }>('/api/notifications/tech-depth', updates);
  return response.data.data;
}

/**
 * Get available technical depth levels
 *
 * @returns Promise<TechnicalDepthLevel[]> - List of available levels
 * @throws Error if request fails
 */
export async function getTechnicalDepthLevels(): Promise<TechnicalDepthLevel[]> {
  const response = await apiClient.get<{
    success: boolean;
    data: { levels: TechnicalDepthLevel[] };
  }>('/api/notifications/tech-depth/levels');
  return response.data.data.levels;
}

/**
 * Get technical depth filtering statistics
 *
 * @returns Promise<TechnicalDepthStats> - Filtering statistics
 * @throws Error if request fails
 */
export async function getTechnicalDepthStats(): Promise<TechnicalDepthStats> {
  const response = await apiClient.get<{
    success: boolean;
    data: TechnicalDepthStats;
  }>('/api/notifications/tech-depth/stats');
  return response.data.data;
}

// Notification History API Functions
