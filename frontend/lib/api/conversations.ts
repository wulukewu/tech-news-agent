import { apiClient } from './client';

// ─── Types ────────────────────────────────────────────────────────────────────

export interface ConversationSummary {
  id: string;
  title: string;
  summary?: string;
  platform: 'web' | 'discord';
  last_message_at: string;
  message_count: number;
  tags: string[];
  is_favorite: boolean;
  is_archived: boolean;
}

export interface ConversationMessage {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant';
  content: string;
  platform: 'web' | 'discord';
  created_at: string;
  metadata?: Record<string, unknown>;
}

export interface ConversationDetail extends ConversationSummary {
  messages?: ConversationMessage[];
}

export interface MessageFilters {
  limit?: number;
  offset?: number;
}

export interface AddMessageData {
  role: 'user' | 'assistant';
  content: string;
  platform?: 'web' | 'discord';
  metadata?: Record<string, unknown>;
}

export interface ConversationFilters {
  search?: string;
  platform?: 'web' | 'discord';
  is_favorite?: boolean;
  is_archived?: boolean;
  tags?: string[];
  limit?: number;
  offset?: number;
}

export interface ConversationsResponse {
  items: ConversationSummary[];
  total_count: number;
  has_next: boolean;
  offset: number;
  limit: number;
}

export interface CreateConversationData {
  title?: string;
  platform?: 'web' | 'discord';
  tags?: string[];
}

export interface UpdateConversationData {
  title?: string;
  summary?: string;
  tags?: string[];
  is_favorite?: boolean;
  is_archived?: boolean;
}

// ─── API Functions ─────────────────────────────────────────────────────────────

/**
 * Fetch paginated list of conversations with optional filters
 * Validates Requirements 3.1
 */
export async function getConversations(
  filters: ConversationFilters = {}
): Promise<ConversationsResponse> {
  const params = new URLSearchParams();

  if (filters.search) params.set('search', filters.search);
  if (filters.platform) params.set('platform', filters.platform);
  if (filters.is_favorite !== undefined) params.set('is_favorite', String(filters.is_favorite));
  if (filters.is_archived !== undefined) params.set('is_archived', String(filters.is_archived));
  if (filters.tags && filters.tags.length > 0) params.set('tags', filters.tags.join(','));
  if (filters.limit !== undefined) params.set('limit', String(filters.limit));
  if (filters.offset !== undefined) params.set('offset', String(filters.offset));

  const url = `/api/conversations${params.toString() ? `?${params.toString()}` : ''}`;

  const response = await apiClient.get<{
    success: boolean;
    data: ConversationSummary[];
    pagination: {
      total_count: number;
      has_next: boolean;
      offset: number;
      limit: number;
    };
  }>(url);

  return {
    items: response.data.data ?? [],
    total_count: response.data.pagination?.total_count ?? 0,
    has_next: response.data.pagination?.has_next ?? false,
    offset: response.data.pagination?.offset ?? 0,
    limit: response.data.pagination?.limit ?? 20,
  };
}

/**
 * Create a new conversation
 * Validates Requirements 3.1, 3.2
 */
export async function createConversation(
  data: CreateConversationData = {}
): Promise<ConversationSummary> {
  const response = await apiClient.post<{
    success: boolean;
    data: ConversationSummary;
  }>('/api/conversations', data);

  return response.data.data;
}

/**
 * Update conversation metadata (title, tags, favorite, archive status)
 * Validates Requirements 3.2, 3.4
 */
export async function updateConversation(
  id: string,
  data: UpdateConversationData
): Promise<ConversationSummary> {
  const response = await apiClient.patch<{
    success: boolean;
    data: ConversationSummary;
  }>(`/api/conversations/${id}`, data);

  return response.data.data;
}

/**
 * Delete a conversation permanently
 * Validates Requirements 3.1
 */
export async function deleteConversation(id: string): Promise<void> {
  await apiClient.delete(`/api/conversations/${id}`);
}

/**
 * Get a single conversation with its metadata
 * Validates Requirements 3.1, 9.1
 */
export async function getConversation(id: string): Promise<ConversationDetail> {
  const response = await apiClient.get<{
    success: boolean;
    data: ConversationDetail;
  }>(`/api/conversations/${id}`);

  return response.data.data;
}

/**
 * Get messages for a conversation with optional pagination
 * Validates Requirements 3.1, 9.1
 */
export async function getConversationMessages(
  id: string,
  params: MessageFilters = {}
): Promise<ConversationMessage[]> {
  const query = new URLSearchParams();
  if (params.limit !== undefined) query.set('limit', String(params.limit));
  if (params.offset !== undefined) query.set('offset', String(params.offset));

  const url = `/api/conversations/${id}/messages${query.toString() ? `?${query.toString()}` : ''}`;

  const response = await apiClient.get<{
    success: boolean;
    data: ConversationMessage[];
  }>(url);

  return response.data.data ?? [];
}

/**
 * Add a message to a conversation
 * Validates Requirements 3.1, 9.2
 */
export async function addMessage(id: string, data: AddMessageData): Promise<ConversationMessage> {
  const response = await apiClient.post<{
    success: boolean;
    data: ConversationMessage;
  }>(`/api/conversations/${id}/messages`, data);

  return response.data.data;
}

/**
 * Export a conversation in the specified format
 * Validates Requirements 9.1, 9.3
 */
export async function exportConversation(
  id: string,
  format: 'markdown' | 'json' | 'pdf' = 'markdown'
): Promise<Blob> {
  const response = await apiClient.get(`/api/conversations/${id}/export`, {
    params: { format },
    responseType: 'blob',
  });

  return response.data as Blob;
}

/**
 * Toggle the favorite status of a conversation.
 * Validates Requirements 3.2, 3.4
 */
export async function setFavorite(id: string, isFavorite: boolean): Promise<ConversationSummary> {
  return updateConversation(id, { is_favorite: isFavorite });
}

/**
 * Toggle the archived status of a conversation.
 * Validates Requirements 3.2, 3.4
 */
export async function setArchived(id: string, isArchived: boolean): Promise<ConversationSummary> {
  return updateConversation(id, { is_archived: isArchived });
}

/**
 * Search conversations by query string with optional filters.
 * Validates Requirements 3.1, 3.3
 */
export async function searchConversations(
  query: string,
  filters: Omit<ConversationFilters, 'search'> = {}
): Promise<ConversationsResponse> {
  return getConversations({ ...filters, search: query });
}
