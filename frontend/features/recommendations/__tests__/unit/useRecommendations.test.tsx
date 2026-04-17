/**
 * Tests for useRecommendations hooks
 *
 * Tests the React Query hooks for recommendations functionality
 */

import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';
import { vi, describe, it, expect, beforeEach } from 'vitest';

import {
  useRecommendations,
  useRefreshRecommendations,
  useDismissRecommendation,
  useTrackRecommendationInteraction,
} from '../../hooks/useRecommendations';

// Mock the API module
vi.mock('../../services/recommendationApi', () => ({
  getRecommendations: vi.fn(),
  refreshRecommendations: vi.fn(),
  dismissRecommendation: vi.fn(),
  trackRecommendationInteraction: vi.fn(),
}));

// Import the mocked functions
import {
  getRecommendations,
  refreshRecommendations,
  dismissRecommendation,
  trackRecommendationInteraction,
} from '../../services/recommendationApi';

const mockGetRecommendations = vi.mocked(getRecommendations);
const mockRefreshRecommendations = vi.mocked(refreshRecommendations);
const mockDismissRecommendation = vi.mocked(dismissRecommendation);
const mockTrackRecommendationInteraction = vi.mocked(trackRecommendationInteraction);

// Test wrapper with QueryClient
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
      mutations: {
        retry: false,
      },
    },
  });

  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('useRecommendations', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should fetch recommendations successfully', async () => {
    const mockResponse = {
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
    };

    mockGetRecommendations.mockResolvedValue(mockResponse);

    const wrapper = createWrapper();
    const { result } = renderHook(() => useRecommendations(), { wrapper });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockResponse);
    expect(mockGetRecommendations).toHaveBeenCalledWith(undefined);
  });

  it('should fetch recommendations with limit', async () => {
    const mockResponse = {
      recommendations: [],
      totalCount: 0,
      hasSufficientData: false,
      minRatingsRequired: 3,
      userRatingCount: 1,
    };

    mockGetRecommendations.mockResolvedValue(mockResponse);

    const wrapper = createWrapper();
    const { result } = renderHook(() => useRecommendations(5), { wrapper });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockGetRecommendations).toHaveBeenCalledWith(5);
  });

  it('should handle API errors', async () => {
    mockGetRecommendations.mockRejectedValue(new Error('API Error'));

    const wrapper = createWrapper();
    const { result } = renderHook(() => useRecommendations(), { wrapper });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toBeInstanceOf(Error);
  });
});

describe('useRefreshRecommendations', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should refresh recommendations successfully', async () => {
    const mockResponse = {
      recommendations: [],
      totalCount: 0,
      hasSufficientData: true,
      minRatingsRequired: 3,
      userRatingCount: 5,
    };

    mockRefreshRecommendations.mockResolvedValue(mockResponse);

    const wrapper = createWrapper();
    const { result } = renderHook(() => useRefreshRecommendations(), { wrapper });

    result.current.mutate({ limit: 10 });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockRefreshRecommendations).toHaveBeenCalledWith({ limit: 10 });
  });

  it('should handle refresh errors', async () => {
    mockRefreshRecommendations.mockRejectedValue(new Error('Refresh Error'));

    const wrapper = createWrapper();
    const { result } = renderHook(() => useRefreshRecommendations(), { wrapper });

    result.current.mutate({});

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toBeInstanceOf(Error);
  });
});

describe('useDismissRecommendation', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should dismiss recommendation successfully', async () => {
    mockDismissRecommendation.mockResolvedValue();

    const wrapper = createWrapper();
    const { result } = renderHook(() => useDismissRecommendation(), { wrapper });

    result.current.mutate({ recommendationId: 'rec1' });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockDismissRecommendation).toHaveBeenCalledWith({
      recommendationId: 'rec1',
    });
  });

  it('should handle dismiss errors', async () => {
    mockDismissRecommendation.mockRejectedValue(new Error('Dismiss Error'));

    const wrapper = createWrapper();
    const { result } = renderHook(() => useDismissRecommendation(), { wrapper });

    result.current.mutate({ recommendationId: 'rec1' });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toBeInstanceOf(Error);
  });
});

describe('useTrackRecommendationInteraction', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should track interaction successfully', async () => {
    mockTrackRecommendationInteraction.mockResolvedValue();

    const wrapper = createWrapper();
    const { result } = renderHook(() => useTrackRecommendationInteraction(), { wrapper });

    const interaction = {
      recommendationId: 'rec1',
      type: 'click' as const,
      timestamp: '2024-01-01T00:00:00Z',
    };

    result.current.mutate(interaction);

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockTrackRecommendationInteraction).toHaveBeenCalledWith(interaction);
  });

  it('should handle tracking errors gracefully', async () => {
    mockTrackRecommendationInteraction.mockRejectedValue(new Error('Tracking Error'));

    const wrapper = createWrapper();
    const { result } = renderHook(() => useTrackRecommendationInteraction(), { wrapper });

    const interaction = {
      recommendationId: 'rec1',
      type: 'view' as const,
      timestamp: '2024-01-01T00:00:00Z',
    };

    result.current.mutate(interaction);

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    // Error should be logged but not thrown (analytics is non-critical)
    expect(result.current.error).toBeInstanceOf(Error);
  });
});
