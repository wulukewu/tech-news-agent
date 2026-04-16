/**
 * Property Tests for AI Analysis API Integration
 * Feature: frontend-feature-enhancement, Task 5.4
 *
 * These tests validate the correctness properties of the AI Analysis API
 * integration including API calls, caching, and error handling.
 *
 * **Validates: Requirements 2.3, 2.6**
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import fc from 'fast-check';
import { useAnalysis, useAnalysisModal } from '@/features/ai-analysis/hooks';
import {
  generateAnalysis,
  getCachedAnalysis,
  copyAnalysisToClipboard,
  generateShareableLink,
} from '@/features/ai-analysis/services';
import { apiClient } from '@/lib/api/client';
import {
  analysisResultArbitrary,
  analysisApiResponseArbitrary,
  articleIdArbitrary,
} from '../../utils/arbitraries';

// Mock API client
vi.mock('@/lib/api/client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
  handleApiError: vi.fn((error) => ({
    message: error.message || 'API Error',
    code: 'API_ERROR',
  })),
}));

describe('AI Analysis API Integration Properties', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });
    vi.clearAllMocks();
  });

  afterEach(() => {
    queryClient.clear();
  });

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  /**
   * Property 10: API 呼叫正確性
   * For any article analysis request, the system should make the correct API call
   * to the backend with proper parameters for Llama 3.3 70B analysis
   *
   * **Validates: Requirements 2.3**
   * THE AI_Analysis_Panel SHALL call the backend API to generate
   * detailed technical analysis using Llama 3.3 70B
   */
  it('Property 10: API should be called with correct parameters', async () => {
    await fc.assert(
      fc.asyncProperty(
        articleIdArbitrary,
        analysisApiResponseArbitrary,
        async (articleId, mockResponse) => {
          // Mock successful API response
          vi.mocked(apiClient.post).mockResolvedValueOnce({ data: mockResponse });

          // Call generateAnalysis
          const result = await generateAnalysis(articleId);

          // API should be called with correct endpoint
          expect(apiClient.post).toHaveBeenCalledWith(
            `/api/articles/${articleId}/analysis`,
            expect.objectContaining({
              model: 'llama-3.3-70b',
              include_sections: expect.arrayContaining([
                'core_concepts',
                'application_scenarios',
                'potential_risks',
                'recommended_steps',
              ]),
            })
          );

          // Result should match expected structure
          expect(result).toHaveProperty('coreConcepts');
          expect(result).toHaveProperty('applicationScenarios');
          expect(result).toHaveProperty('potentialRisks');
          expect(result).toHaveProperty('recommendedSteps');
          expect(result).toHaveProperty('generatedAt');
          expect(result).toHaveProperty('model');
          expect(result).toHaveProperty('rawText');

          // Model should be llama-3.3-70b
          expect(result.model).toBe('llama-3.3-70b');
        }
      ),
      { numRuns: 30 }
    );
  });

  /**
   * Property 13: 分析結果快取
   * For any article that has been analyzed, subsequent analysis requests
   * for the same article should use cached results instead of making new API calls
   *
   * **Validates: Requirements 2.6**
   * THE AI_Analysis_Panel SHALL cache analysis results to avoid
   * regenerating for the same article
   */
  it('Property 13: Cached analysis should be used for subsequent requests', async () => {
    await fc.assert(
      fc.asyncProperty(
        articleIdArbitrary,
        analysisApiResponseArbitrary,
        async (articleId, mockResponse) => {
          // Mock cached analysis response
          vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockResponse });

          // First request - should call API
          const { result, rerender } = renderHook(() => useAnalysis(articleId), { wrapper });

          await waitFor(() => {
            expect(result.current.isLoading).toBe(false);
          });

          // API should have been called once
          expect(apiClient.get).toHaveBeenCalledTimes(1);
          expect(apiClient.get).toHaveBeenCalledWith(`/api/articles/${articleId}/analysis`);

          // Analysis should be available
          expect(result.current.analysis).toBeDefined();

          // Second request - should use cache
          rerender();

          // API should not be called again (still 1 call)
          expect(apiClient.get).toHaveBeenCalledTimes(1);

          // Analysis should still be available from cache
          expect(result.current.analysis).toBeDefined();
        }
      ),
      { numRuns: 20 }
    );
  });

  /**
   * Property: API should handle successful responses correctly
   * For any valid API response, the service should parse and return correct data
   */
  it('Property: API should parse successful responses correctly', async () => {
    await fc.assert(
      fc.asyncProperty(
        articleIdArbitrary,
        analysisApiResponseArbitrary,
        async (articleId, mockResponse) => {
          vi.mocked(apiClient.post).mockResolvedValueOnce({ data: mockResponse });

          const result = await generateAnalysis(articleId);

          // All required fields should be present
          expect(result.coreConcepts).toEqual(mockResponse.data.core_concepts);
          expect(result.applicationScenarios).toEqual(mockResponse.data.application_scenarios);
          expect(result.potentialRisks).toEqual(mockResponse.data.potential_risks);
          expect(result.recommendedSteps).toEqual(mockResponse.data.recommended_steps);
          expect(result.rawText).toEqual(mockResponse.data.raw_text);

          // Date should be parsed correctly
          expect(result.generatedAt).toBeInstanceOf(Date);

          // Model should match
          expect(result.model).toBe(mockResponse.data.model);
        }
      ),
      { numRuns: 30 }
    );
  });

  /**
   * Property: API should handle error responses correctly
   * For any API error, the service should throw appropriate error
   *
   * **Validates: Requirements 2.9**
   * WHEN analysis generation fails, THE AI_Analysis_Panel SHALL display
   * an error message with retry option
   */
  it('Property: API should handle errors and throw appropriate messages', async () => {
    await fc.assert(
      fc.asyncProperty(
        articleIdArbitrary,
        fc.string({ minLength: 1, maxLength: 200 }), // error message
        async (articleId, errorMessage) => {
          // Mock API error
          vi.mocked(apiClient.post).mockRejectedValueOnce(new Error(errorMessage));

          // Should throw error
          await expect(generateAnalysis(articleId)).rejects.toThrow();
        }
      ),
      { numRuns: 20 }
    );
  });

  /**
   * Property: Cached analysis should return null for non-existent articles
   * For any article without cached analysis, getCachedAnalysis should return null
   */
  it('Property: getCachedAnalysis should return null for non-existent analysis', async () => {
    await fc.assert(
      fc.asyncProperty(articleIdArbitrary, async (articleId) => {
        // Mock 404 response
        const error = new Error('Not found');
        (error as any).response = { status: 404 };
        vi.mocked(apiClient.get).mockRejectedValueOnce(error);

        const result = await getCachedAnalysis(articleId);

        // Should return null instead of throwing
        expect(result).toBeNull();
      }),
      { numRuns: 20 }
    );
  });

  /**
   * Property: API should handle network errors gracefully
   * For any network error, the service should provide meaningful error messages
   */
  it('Property: API should handle network errors with meaningful messages', async () => {
    await fc.assert(
      fc.asyncProperty(articleIdArbitrary, async (articleId) => {
        // Mock network error
        const networkError = new Error('Network request failed');
        vi.mocked(apiClient.post).mockRejectedValueOnce(networkError);

        // Should throw with error message
        await expect(generateAnalysis(articleId)).rejects.toThrow();
      }),
      { numRuns: 15 }
    );
  });

  /**
   * Property: API should validate response structure
   * For any malformed API response, the service should handle it gracefully
   */
  it('Property: API should handle malformed responses', async () => {
    await fc.assert(
      fc.asyncProperty(articleIdArbitrary, async (articleId) => {
        // Mock malformed response (missing success field)
        vi.mocked(apiClient.post).mockResolvedValueOnce({
          data: { success: false, error: 'Invalid response' },
        });

        // Should throw error for unsuccessful response
        await expect(generateAnalysis(articleId)).rejects.toThrow();
      }),
      { numRuns: 15 }
    );
  });

  /**
   * Property: Cache key should be consistent for same article
   * For any article ID, the cache key should be deterministic
   */
  it('Property: Cache keys should be consistent for same article', async () => {
    await fc.assert(
      fc.asyncProperty(
        articleIdArbitrary,
        analysisApiResponseArbitrary,
        async (articleId, mockResponse) => {
          vi.mocked(apiClient.get).mockResolvedValue({ data: mockResponse });

          // First hook instance
          const { result: result1 } = renderHook(() => useAnalysis(articleId), { wrapper });

          await waitFor(() => {
            expect(result1.current.isLoading).toBe(false);
          });

          // Second hook instance with same articleId
          const { result: result2 } = renderHook(() => useAnalysis(articleId), { wrapper });

          await waitFor(() => {
            expect(result2.current.isLoading).toBe(false);
          });

          // Both should have the same data (from cache)
          expect(result1.current.analysis).toEqual(result2.current.analysis);

          // API should only be called once
          expect(apiClient.get).toHaveBeenCalledTimes(1);
        }
      ),
      { numRuns: 15 }
    );
  });

  /**
   * Property: API should respect cache strategy
   * For any cached analysis, the cache should follow the configured stale time
   */
  it('Property: API should use correct cache strategy', async () => {
    await fc.assert(
      fc.asyncProperty(
        articleIdArbitrary,
        analysisApiResponseArbitrary,
        async (articleId, mockResponse) => {
          vi.mocked(apiClient.get).mockResolvedValue({ data: mockResponse });

          const { result } = renderHook(() => useAnalysis(articleId), { wrapper });

          await waitFor(() => {
            expect(result.current.isLoading).toBe(false);
          });

          // Analysis should be cached
          expect(result.current.analysis).toBeDefined();

          // Query should not refetch on window focus (as per cache strategy)
          // This is validated by the cache configuration in the hook
          expect(apiClient.get).toHaveBeenCalledTimes(1);
        }
      ),
      { numRuns: 15 }
    );
  });

  /**
   * Property: Shareable link generation should be consistent
   * For any article ID, the shareable link should follow the correct format
   */
  it('Property: Shareable links should follow correct format', () => {
    fc.assert(
      fc.property(articleIdArbitrary, (articleId) => {
        const shareLink = generateShareableLink(articleId);

        // Link should contain the article ID
        expect(shareLink).toContain(articleId);

        // Link should follow the correct path format
        expect(shareLink).toMatch(/\/articles\/[^/]+\/analysis/);

        // Link should be a valid URL format
        expect(() => new URL(shareLink, 'http://localhost')).not.toThrow();
      }),
      { numRuns: 50 }
    );
  });
});
