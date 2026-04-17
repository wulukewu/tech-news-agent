/**
 * Tests for recommendation API service
 *
 * Tests the API service functions for recommendations
 */

import { vi, describe, it, expect, beforeEach } from 'vitest';

// Mock the API client before importing the module
vi.mock('@/lib/api/client', () => {
  const mockApiClient = {
    get: vi.fn(),
    post: vi.fn(),
  };

  const mockHandleApiError = vi.fn((error) => ({
    code: 'API_ERROR',
    message: error.message || 'API Error',
    timestamp: new Date().toISOString(),
  }));

  return {
    apiClient: mockApiClient,
    handleApiError: mockHandleApiError,
  };
});

import {
  getRecommendations,
  refreshRecommendations,
  dismissRecommendation,
  trackRecommendationInteraction,
} from '../../services/recommendationApi';

// Get the mocked functions
import { apiClient, handleApiError } from '@/lib/api/client';
const mockApiClient = vi.mocked(apiClient);
const mockHandleApiError = vi.mocked(handleApiError);

describe('recommendationApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getRecommendations', () => {
    it('should fetch recommendations successfully', async () => {
      const mockResponse = {
        data: {
          recommendations: [
            {
              id: 'rec1',
              article: {
                id: 'article1',
                title: 'Test Article',
                url: 'https://example.com',
                feedName: 'Test Feed',
                category: 'Programming',
                publishedAt: '2024-01-01T00:00:00Z',
                tinkeringIndex: 4,
                aiSummary: 'Test summary',
              },
              reason: 'Test reason',
              confidence: 0.8,
              generatedAt: '2024-01-01T00:00:00Z',
              dismissed: false,
            },
          ],
          totalCount: 1,
          hasSufficientData: true,
          minRatingsRequired: 3,
          userRatingCount: 5,
        },
      };

      mockApiClient.get.mockResolvedValue(mockResponse);

      const result = await getRecommendations();

      expect(mockApiClient.get).toHaveBeenCalledWith('/api/v1/recommendations', {
        params: { limit: undefined },
      });
      expect(result).toEqual(mockResponse.data);
    });

    it('should fetch recommendations with limit', async () => {
      const mockResponse = {
        data: {
          recommendations: [],
          totalCount: 0,
          hasSufficientData: false,
          minRatingsRequired: 3,
          userRatingCount: 1,
        },
      };

      mockApiClient.get.mockResolvedValue(mockResponse);

      const result = await getRecommendations(5);

      expect(mockApiClient.get).toHaveBeenCalledWith('/api/v1/recommendations', {
        params: { limit: 5 },
      });
      expect(result).toEqual(mockResponse.data);
    });

    it('should handle API errors', async () => {
      const mockError = new Error('Network Error');
      mockApiClient.get.mockRejectedValue(mockError);

      await expect(getRecommendations()).rejects.toThrow('Network Error');
    });
  });

  describe('refreshRecommendations', () => {
    it('should refresh recommendations successfully', async () => {
      const mockResponse = {
        data: {
          recommendations: [],
          totalCount: 0,
          hasSufficientData: true,
          minRatingsRequired: 3,
          userRatingCount: 5,
        },
      };

      mockApiClient.post.mockResolvedValue(mockResponse);

      const request = { limit: 10 };
      const result = await refreshRecommendations(request);

      expect(mockApiClient.post).toHaveBeenCalledWith('/api/v1/recommendations/refresh', request);
      expect(result).toEqual(mockResponse.data);
    });

    it('should refresh recommendations with empty request', async () => {
      const mockResponse = {
        data: {
          recommendations: [],
          totalCount: 0,
          hasSufficientData: true,
          minRatingsRequired: 3,
          userRatingCount: 5,
        },
      };

      mockApiClient.post.mockResolvedValue(mockResponse);

      const result = await refreshRecommendations();

      expect(mockApiClient.post).toHaveBeenCalledWith('/api/v1/recommendations/refresh', {});
      expect(result).toEqual(mockResponse.data);
    });

    it('should handle refresh errors', async () => {
      const mockError = new Error('Refresh Error');
      mockApiClient.post.mockRejectedValue(mockError);

      await expect(refreshRecommendations({})).rejects.toThrow('Refresh Error');
    });
  });

  describe('dismissRecommendation', () => {
    it('should dismiss recommendation successfully', async () => {
      mockApiClient.post.mockResolvedValue({ data: {} });

      const request = { recommendationId: 'rec1' };
      await dismissRecommendation(request);

      expect(mockApiClient.post).toHaveBeenCalledWith('/api/v1/recommendations/dismiss', request);
    });

    it('should handle dismiss errors', async () => {
      const mockError = new Error('Dismiss Error');
      mockApiClient.post.mockRejectedValue(mockError);

      const request = { recommendationId: 'rec1' };
      await expect(dismissRecommendation(request)).rejects.toThrow('Dismiss Error');
    });
  });

  describe('trackRecommendationInteraction', () => {
    it('should track interaction successfully', async () => {
      mockApiClient.post.mockResolvedValue({ data: {} });

      const interaction = {
        recommendationId: 'rec1',
        type: 'click' as const,
        timestamp: '2024-01-01T00:00:00Z',
      };

      await trackRecommendationInteraction(interaction);

      expect(mockApiClient.post).toHaveBeenCalledWith('/api/v1/recommendations/track', interaction);
    });

    it('should handle tracking errors', async () => {
      const mockError = new Error('Tracking Error');
      mockApiClient.post.mockRejectedValue(mockError);

      const interaction = {
        recommendationId: 'rec1',
        type: 'view' as const,
        timestamp: '2024-01-01T00:00:00Z',
      };

      await expect(trackRecommendationInteraction(interaction)).rejects.toThrow('Tracking Error');
    });
  });
});
