/**
 * Conversation type definitions for the chat persistence system.
 *
 * Validates Requirements 3.1, 3.2:
 * - 3.1: Conversation list, search, and filter functionality
 * - 3.2: Smart conversation features (title, summary, tags, favorites)
 */

/**
 * Full conversation object with all metadata fields.
 */
export interface Conversation {
  id: string;
  title: string;
  summary?: string;
  platform: 'web' | 'discord';
  tags: string[];
  is_archived: boolean;
  is_favorite: boolean;
  created_at: string;
  last_message_at: string;
  message_count: number;
  metadata?: Record<string, unknown>;
}

/**
 * Filters for querying conversations from the API.
 */
export interface ConversationFilters {
  platform?: 'web' | 'discord';
  is_archived?: boolean;
  is_favorite?: boolean;
  tags?: string[];
  limit?: number;
  offset?: number;
}
