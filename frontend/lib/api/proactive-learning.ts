import { apiClient } from './client';

export interface LearningConversation {
  id: string;
  conversation_type: string;
  question: string;
  options: string[] | null;
  status: 'pending' | 'answered' | 'expired';
  context_data: Record<string, unknown> | null;
  created_at: string;
  responded_at: string | null;
}

export interface PreferenceModel {
  id: string;
  user_id: string;
  category_weights: Record<string, number>;
  learning_enabled: boolean;
  max_weekly_conversations: number;
  conversations_this_week: number;
  updated_at: string;
}

export interface LearningSettings {
  learning_enabled: boolean;
  max_weekly_conversations: number;
  conversations_this_week: number;
}

export interface FeedbackSignals {
  sentiment: 'positive' | 'negative' | 'neutral' | 'mixed';
  interested_topics: string[];
  disinterested_topics: string[];
  weight_adjustments: Record<string, number>;
  needs_clarification: boolean;
}

/** Get all pending learning conversations. */
export async function getPendingConversations(): Promise<{
  conversations: LearningConversation[];
  count: number;
}> {
  const res = await apiClient.get<{
    success: boolean;
    data: { conversations: LearningConversation[]; count: number };
  }>('/api/learning/conversations/pending');
  return res.data.data;
}

/** Submit a response to a learning conversation. */
export async function respondToConversation(
  conversationId: string,
  response: string
): Promise<{ signals: FeedbackSignals; updated_weights: Record<string, number> }> {
  const res = await apiClient.post<{
    success: boolean;
    data: { signals: FeedbackSignals; updated_weights: Record<string, number> };
  }>(`/api/learning/conversations/${conversationId}/respond`, { response });
  return res.data.data;
}

/** Get current preference model. */
export async function getPreferences(): Promise<PreferenceModel> {
  const res = await apiClient.get<{ success: boolean; data: PreferenceModel }>(
    '/api/learning/preferences'
  );
  return res.data.data;
}

/** Manually update category weights. */
export async function updatePreferences(
  categoryWeights: Record<string, number>
): Promise<PreferenceModel> {
  const res = await apiClient.put<{ success: boolean; data: PreferenceModel }>(
    '/api/learning/preferences',
    { category_weights: categoryWeights }
  );
  return res.data.data;
}

/** Get learning settings. */
export async function getLearningSettings(): Promise<LearningSettings> {
  const res = await apiClient.get<{ success: boolean; data: LearningSettings }>(
    '/api/learning/settings'
  );
  return res.data.data;
}

/** Update learning settings. */
export async function updateLearningSettings(
  settings: Partial<Pick<LearningSettings, 'learning_enabled' | 'max_weekly_conversations'>>
): Promise<{ updated: Partial<LearningSettings> }> {
  const res = await apiClient.put<{
    success: boolean;
    data: { updated: Partial<LearningSettings> };
  }>('/api/learning/settings', settings);
  return res.data.data;
}

/** Record a behavior event. */
export async function recordBehaviorEvent(event: {
  event_type: string;
  article_id?: string;
  category?: string;
  rating?: number;
  duration_seconds?: number;
}): Promise<void> {
  await apiClient.post('/api/learning/events', event);
}

/** Manually trigger behavior analysis. */
export async function triggerLearning(): Promise<{
  triggered: boolean;
  conversation?: LearningConversation;
  reason?: string;
}> {
  const res = await apiClient.post<{
    success: boolean;
    data: { triggered: boolean; conversation?: LearningConversation; reason?: string };
  }>('/api/learning/trigger', {});
  return res.data.data;
}

/** Complete onboarding: set initial category weights and get first question. */
export async function completeOnboarding(selectedCategories: string[]): Promise<{
  weights: Record<string, number>;
  initial_conversation: LearningConversation | null;
}> {
  const res = await apiClient.post<{
    success: boolean;
    data: { weights: Record<string, number>; initial_conversation: LearningConversation | null };
  }>('/api/learning/onboarding', { selected_categories: selectedCategories });
  return res.data.data;
}

export const ONBOARDING_CATEGORIES = [
  'AI/ML',
  'Web Development',
  'DevOps',
  'Security',
  'Cloud',
  'Mobile',
  'Data Science',
  'Open Source',
  'Startup',
  'Hardware',
] as const;
