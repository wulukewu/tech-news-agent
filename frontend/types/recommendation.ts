/**
 * Recommendation type definitions
 *
 * Validates Requirements 3.1-3.10:
 * - Smart recommendation engine based on user ratings
 * - Recommendation cards with article information
 * - Refresh and dismiss functionality
 */

import { Article } from './article';

/**
 * Recommendation interface representing a recommended article
 */
export interface Recommendation {
  /** Unique identifier for the recommendation */
  id: string;
  /** The recommended article */
  article: Article;
  /** AI-generated reason for the recommendation */
  reason: string;
  /** Confidence score (0-1) */
  confidence: number;
  /** When the recommendation was generated */
  generatedAt: string;
  /** Whether the user has dismissed this recommendation */
  dismissed?: boolean;
}

/**
 * Response from recommendations API
 */
export interface RecommendationsResponse {
  /** Array of recommendations */
  recommendations: Recommendation[];
  /** Total number of recommendations available */
  totalCount: number;
  /** Whether the user has sufficient rating data */
  hasSufficientData: boolean;
  /** Minimum number of ratings required */
  minRatingsRequired: number;
  /** User's current rating count */
  userRatingCount: number;
}

/**
 * Request to refresh recommendations
 */
export interface RefreshRecommendationsRequest {
  /** Optional: limit number of recommendations */
  limit?: number;
}

/**
 * Request to dismiss a recommendation
 */
export interface DismissRecommendationRequest {
  /** ID of the recommendation to dismiss */
  recommendationId: string;
}

/**
 * Recommendation interaction types for analytics
 */
export type RecommendationInteractionType = 'view' | 'click' | 'dismiss' | 'refresh';

/**
 * Recommendation interaction event
 */
export interface RecommendationInteraction {
  /** Recommendation ID */
  recommendationId: string;
  /** Type of interaction */
  type: RecommendationInteractionType;
  /** Timestamp of interaction */
  timestamp: string;
}
