import { apiClient } from './client';

// ─── Types ────────────────────────────────────────────────────────────────────

export interface ArticleSummary {
  article_id: string;
  title: string;
  summary: string;
  url: string;
  relevance_score: number;
  reading_time: number;
  key_insights: string[];
  published_at: string | null;
  category: string;
}

export interface QAQueryResponse {
  query: string;
  articles: ArticleSummary[];
  insights: string[];
  recommendations: string[];
  conversation_id: string;
  response_time: number;
}

export interface ConversationTurn {
  turn_number: number;
  query: string;
  timestamp: string;
}

export interface ConversationHistory {
  conversation_id: string;
  user_id: string;
  turns: ConversationTurn[];
  current_topic: string | null;
  created_at: string;
  last_updated: string;
}

export interface CreateConversationResponse {
  conversation_id: string;
  query_result?: QAQueryResponse;
}

// ─── API Functions ────────────────────────────────────────────────────────────

/**
 * Send a query to the QA agent (single-turn or with existing conversation)
 * Validates Requirements 1.1
 */
export async function sendQuery(query: string, conversationId?: string): Promise<QAQueryResponse> {
  const response = await apiClient.post<{ success: boolean; data: QAQueryResponse }>(
    '/api/qa/query',
    { query, ...(conversationId ? { conversation_id: conversationId } : {}) }
  );
  return response.data.data;
}

/**
 * Create a new conversation, optionally with an initial query
 * Validates Requirements 1.1, 4.1
 */
export async function createConversation(
  initialQuery?: string
): Promise<CreateConversationResponse> {
  const response = await apiClient.post<{
    success: boolean;
    data: CreateConversationResponse;
  }>('/api/qa/conversations', initialQuery ? { initial_query: initialQuery } : {});
  return response.data.data;
}

/**
 * Continue an existing conversation with a follow-up query
 * Validates Requirements 1.1, 4.1
 */
export async function continueConversation(
  conversationId: string,
  query: string
): Promise<QAQueryResponse> {
  const response = await apiClient.post<{ success: boolean; data: QAQueryResponse }>(
    `/api/qa/conversations/${conversationId}/continue`,
    { query }
  );
  return response.data.data;
}

/**
 * Retrieve the history of a conversation
 * Validates Requirements 4.1
 */
export async function getConversationHistory(conversationId: string): Promise<ConversationHistory> {
  const response = await apiClient.get<{ success: boolean; data: ConversationHistory }>(
    `/api/qa/conversations/${conversationId}`
  );
  return response.data.data;
}

/**
 * Delete a conversation and its history
 * Validates Requirements 4.1
 */
export async function deleteConversation(conversationId: string): Promise<{ message: string }> {
  const response = await apiClient.delete<{ success: boolean; data: { message: string } }>(
    `/api/qa/conversations/${conversationId}`
  );
  return response.data.data;
}
