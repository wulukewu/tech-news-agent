/**
 * Preservation Property Tests - Frontend Valid article_id
 *
 * **Validates: Requirements 3.4, 3.5**
 *
 * Property 2: Preservation - Valid Frontend API Calls Behavior
 *
 * IMPORTANT: Follow observation-first methodology
 *
 * These tests capture the baseline behavior on UNFIXED code for valid article_id values:
 * - Valid UUIDs work correctly
 * - Adding articles to reading list succeeds
 * - Status updates work correctly
 * - Rating updates work correctly
 * - Removing articles works correctly
 *
 * Expected outcome on UNFIXED code: Tests PASS (confirms baseline behavior)
 * Expected outcome on FIXED code: Tests PASS (confirms no regressions)
 *
 * CRITICAL: Use numRuns=5 for fast execution in fast-check tests
 */

import * as fc from 'fast-check';
import {
  addToReadingList,
  updateReadingListStatus,
  updateReadingListRating,
  removeFromReadingList,
} from '@/lib/api/readingList';
import type { ReadingListStatus } from '@/types/readingList';

// Mock the API client
jest.mock('@/lib/api/client', () => ({
  apiClient: {
    post: jest.fn(),
    patch: jest.fn(),
    delete: jest.fn(),
    get: jest.fn(),
  },
}));

import { apiClient } from '@/lib/api/client';

describe('Preservation Property Tests - Valid article_id Operations', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  /**
   * Property 2.1: Valid UUID article_id works for addToReadingList
   *
   * **Validates: Requirement 3.4**
   *
   * For any valid UUID article_id, the addToReadingList function
   * SHALL successfully make the API call and return the expected response.
   */
  it('should successfully add articles with valid UUID article_id', async () => {
    console.log('\n=== Testing addToReadingList with valid UUIDs ===');

    const mockPost = apiClient.post as jest.Mock;
    mockPost.mockResolvedValue({
      message: 'Article added to reading list',
      articleId: 'test-uuid',
    });

    const validUuid = '550e8400-e29b-41d4-a716-446655440000';

    const result = await addToReadingList(validUuid);

    // Verify API was called
    expect(mockPost).toHaveBeenCalledTimes(1);
    expect(mockPost).toHaveBeenCalledWith('/api/reading-list', {
      article_id: validUuid,
    });

    // Verify response structure
    expect(result).toHaveProperty('message');
    expect(result).toHaveProperty('articleId');

    console.log('✓ Valid UUID successfully added to reading list');
    console.log(`✓ API called with: { article_id: "${validUuid}" }`);
    console.log('✓ Response structure preserved');
  });

  /**
   * Property 2.2: Valid UUID article_id works for updateReadingListStatus
   *
   * **Validates: Requirement 3.5**
   *
   * For any valid UUID article_id and valid status value,
   * the updateReadingListStatus function SHALL successfully make
   * the API call and return the expected response.
   */
  it('should successfully update status with valid UUID article_id', async () => {
    console.log('\n=== Testing updateReadingListStatus with valid UUIDs ===');

    const mockPatch = apiClient.patch as jest.Mock;
    mockPatch.mockResolvedValue({
      message: 'Status updated',
      status: 'Read',
    });

    const validUuid = '550e8400-e29b-41d4-a716-446655440000';
    const status: ReadingListStatus = 'Read';

    const result = await updateReadingListStatus(validUuid, status);

    // Verify API was called with correct URL and payload
    expect(mockPatch).toHaveBeenCalledTimes(1);
    expect(mockPatch).toHaveBeenCalledWith(
      `/api/reading-list/${validUuid}/status`,
      { status },
    );

    // Verify response structure
    expect(result).toHaveProperty('message');
    expect(result).toHaveProperty('status');

    console.log('✓ Valid UUID successfully updated status');
    console.log(`✓ API called with URL: /api/reading-list/${validUuid}/status`);
    console.log('✓ Response structure preserved');
  });

  /**
   * Property 2.3: Valid UUID article_id works for updateReadingListRating
   *
   * **Validates: Requirement 3.5**
   *
   * For any valid UUID article_id and valid rating value (1-5 or null),
   * the updateReadingListRating function SHALL successfully make
   * the API call and return the expected response.
   */
  it('should successfully update rating with valid UUID article_id', async () => {
    console.log('\n=== Testing updateReadingListRating with valid UUIDs ===');

    const mockPatch = apiClient.patch as jest.Mock;
    mockPatch.mockResolvedValue({
      message: 'Rating updated',
      rating: 4,
    });

    const validUuid = '550e8400-e29b-41d4-a716-446655440000';
    const rating = 4;

    const result = await updateReadingListRating(validUuid, rating);

    // Verify API was called with correct URL and payload
    expect(mockPatch).toHaveBeenCalledTimes(1);
    expect(mockPatch).toHaveBeenCalledWith(
      `/api/reading-list/${validUuid}/rating`,
      { rating },
    );

    // Verify response structure
    expect(result).toHaveProperty('message');
    expect(result).toHaveProperty('rating');

    console.log('✓ Valid UUID successfully updated rating');
    console.log(`✓ API called with URL: /api/reading-list/${validUuid}/rating`);
    console.log('✓ Response structure preserved');
  });

  /**
   * Property 2.4: Valid UUID article_id works for removeFromReadingList
   *
   * **Validates: Requirement 3.5**
   *
   * For any valid UUID article_id, the removeFromReadingList function
   * SHALL successfully make the API call and return the expected response.
   */
  it('should successfully remove articles with valid UUID article_id', async () => {
    console.log('\n=== Testing removeFromReadingList with valid UUIDs ===');

    const mockDelete = apiClient.delete as jest.Mock;
    mockDelete.mockResolvedValue({
      message: 'Article removed from reading list',
    });

    const validUuid = '550e8400-e29b-41d4-a716-446655440000';

    const result = await removeFromReadingList(validUuid);

    // Verify API was called with correct URL
    expect(mockDelete).toHaveBeenCalledTimes(1);
    expect(mockDelete).toHaveBeenCalledWith(`/api/reading-list/${validUuid}`);

    // Verify response structure
    expect(result).toHaveProperty('message');

    console.log('✓ Valid UUID successfully removed from reading list');
    console.log(`✓ API called with URL: /api/reading-list/${validUuid}`);
    console.log('✓ Response structure preserved');
  });

  /**
   * Property-Based Test 2.5: All API operations work with valid UUIDs
   *
   * **Validates: Requirements 3.4, 3.5**
   *
   * For any valid UUID article_id and any API operation,
   * the system SHALL successfully make the API call and return
   * the expected response structure.
   *
   * CRITICAL: Uses numRuns=5 for fast execution
   */
  it('should preserve all API operations with valid UUIDs (property-based)', async () => {
    console.log('\n=== Property-Based Test: All Valid UUID Operations ===');

    // Test each operation separately to avoid mock conflicts
    const operations = [
      {
        name: 'addToReadingList',
        test: async (uuid: string) => {
          const mockPost = apiClient.post as jest.Mock;
          mockPost.mockResolvedValue({ message: 'Success', articleId: uuid });
          await addToReadingList(uuid);
          return mockPost.mock.calls.length === 1;
        },
      },
      {
        name: 'updateStatus',
        test: async (uuid: string) => {
          const mockPatch = apiClient.patch as jest.Mock;
          mockPatch.mockResolvedValue({ message: 'Success' });
          await updateReadingListStatus(uuid, 'Read');
          return mockPatch.mock.calls.length === 1;
        },
      },
      {
        name: 'updateRating',
        test: async (uuid: string) => {
          const mockPatch = apiClient.patch as jest.Mock;
          mockPatch.mockResolvedValue({ message: 'Success' });
          await updateReadingListRating(uuid, 3);
          return mockPatch.mock.calls.length === 1;
        },
      },
      {
        name: 'removeFromReadingList',
        test: async (uuid: string) => {
          const mockDelete = apiClient.delete as jest.Mock;
          mockDelete.mockResolvedValue({ message: 'Success' });
          await removeFromReadingList(uuid);
          return mockDelete.mock.calls.length === 1;
        },
      },
    ];

    for (const operation of operations) {
      await fc.assert(
        fc.asyncProperty(fc.uuid(), async (validArticleId) => {
          jest.clearAllMocks();
          try {
            const result = await operation.test(validArticleId);
            return result;
          } catch (error) {
            console.log(
              `\nRegression detected: ${operation.name} failed with valid UUID ${validArticleId}`,
            );
            return false;
          }
        }),
        { numRuns: 5 }, // CRITICAL: Fast execution with 5 runs
      );
    }

    console.log('✓ All API operations work correctly with valid UUIDs');
  });

  /**
   * Property-Based Test 2.6: Status updates work with all valid status values
   *
   * **Validates: Requirement 3.5**
   *
   * For any valid UUID article_id and any valid ReadingListStatus value,
   * the updateReadingListStatus function SHALL successfully make the API call.
   *
   * CRITICAL: Uses numRuns=5 for fast execution
   */
  it('should preserve status updates with all valid status values (property-based)', async () => {
    console.log('\n=== Property-Based Test: All Valid Status Values ===');

    const statuses: ReadingListStatus[] = ['Unread', 'Read', 'Archived'];

    for (const status of statuses) {
      await fc.assert(
        fc.asyncProperty(fc.uuid(), async (validArticleId) => {
          jest.clearAllMocks();

          const mockPatch = apiClient.patch as jest.Mock;
          mockPatch.mockResolvedValue({
            message: 'Status updated',
            status,
          });

          try {
            const result = await updateReadingListStatus(
              validArticleId,
              status,
            );

            // Verify API was called correctly
            const calls = mockPatch.mock.calls;
            if (calls.length !== 1) return false;

            const [url, payload] = calls[0];
            if (url !== `/api/reading-list/${validArticleId}/status`)
              return false;
            if (payload.status !== status) return false;

            // Verify response structure
            if (!result.message || result.status !== status) return false;

            return true;
          } catch (error) {
            console.log(`\nUnexpected error for status ${status}: ${error}`);
            return false;
          }
        }),
        { numRuns: 5 }, // CRITICAL: Fast execution with 5 runs
      );
    }

    console.log('✓ All valid status values work correctly');
  });

  /**
   * Property-Based Test 2.7: Rating updates work with valid rating values
   *
   * **Validates: Requirement 3.5**
   *
   * For any valid UUID article_id and any valid rating value (1-5),
   * the updateReadingListRating function SHALL successfully make the API call.
   *
   * CRITICAL: Uses numRuns=5 for fast execution
   */
  it('should preserve rating updates with valid rating values (property-based)', async () => {
    console.log('\n=== Property-Based Test: All Valid Rating Values ===');

    await fc.assert(
      fc.asyncProperty(
        fc.uuid(),
        fc.integer({ min: 1, max: 5 }),
        async (validArticleId, rating) => {
          jest.clearAllMocks();

          const mockPatch = apiClient.patch as jest.Mock;
          mockPatch.mockResolvedValue({
            message: 'Rating updated',
            rating,
          });

          try {
            const result = await updateReadingListRating(
              validArticleId,
              rating,
            );

            // Verify API was called correctly
            const calls = mockPatch.mock.calls;
            if (calls.length !== 1) return false;

            const [url, payload] = calls[0];
            if (url !== `/api/reading-list/${validArticleId}/rating`)
              return false;
            if (payload.rating !== rating) return false;

            // Verify response structure
            if (!result.message || result.rating !== rating) return false;

            return true;
          } catch (error) {
            console.log(`\nUnexpected error for rating ${rating}: ${error}`);
            return false;
          }
        },
      ),
      { numRuns: 5 }, // CRITICAL: Fast execution with 5 runs
    );

    console.log('✓ All valid rating values (1-5) work correctly');
  });

  /**
   * Property-Based Test 2.8: API call structure is preserved
   *
   * **Validates: Requirements 3.4, 3.5**
   *
   * For any valid UUID article_id, the API functions SHALL construct
   * the correct request URLs and payloads according to the API contract.
   *
   * CRITICAL: Uses numRuns=5 for fast execution
   */
  it('should preserve API call structure and contracts (property-based)', async () => {
    console.log('\n=== Property-Based Test: API Call Structure ===');

    await fc.assert(
      fc.asyncProperty(fc.uuid(), async (validArticleId) => {
        jest.clearAllMocks();

        const mockPost = apiClient.post as jest.Mock;
        const mockPatch = apiClient.patch as jest.Mock;
        const mockDelete = apiClient.delete as jest.Mock;

        mockPost.mockResolvedValue({ message: 'Success' });
        mockPatch.mockResolvedValue({ message: 'Success' });
        mockDelete.mockResolvedValue({ message: 'Success' });

        // Test addToReadingList
        await addToReadingList(validArticleId);
        if (mockPost.mock.calls.length !== 1) return false;
        if (mockPost.mock.calls[0][0] !== '/api/reading-list') return false;
        if (mockPost.mock.calls[0][1].article_id !== validArticleId)
          return false;

        jest.clearAllMocks();

        // Test updateReadingListStatus
        await updateReadingListStatus(validArticleId, 'Read');
        if (mockPatch.mock.calls.length !== 1) return false;
        if (
          mockPatch.mock.calls[0][0] !==
          `/api/reading-list/${validArticleId}/status`
        )
          return false;
        if (mockPatch.mock.calls[0][1].status !== 'Read') return false;

        jest.clearAllMocks();

        // Test updateReadingListRating
        await updateReadingListRating(validArticleId, 3);
        if (mockPatch.mock.calls.length !== 1) return false;
        if (
          mockPatch.mock.calls[0][0] !==
          `/api/reading-list/${validArticleId}/rating`
        )
          return false;
        if (mockPatch.mock.calls[0][1].rating !== 3) return false;

        jest.clearAllMocks();

        // Test removeFromReadingList
        await removeFromReadingList(validArticleId);
        if (mockDelete.mock.calls.length !== 1) return false;
        if (
          mockDelete.mock.calls[0][0] !== `/api/reading-list/${validArticleId}`
        )
          return false;

        return true;
      }),
      { numRuns: 5 }, // CRITICAL: Fast execution with 5 runs
    );

    console.log('✓ API call structure and contracts preserved');
  });

  /**
   * Property 2.9: Error handling for other validation errors is preserved
   *
   * **Validates: Requirement 3.5**
   *
   * For valid UUID article_id but invalid other parameters (e.g., invalid status),
   * the system SHALL continue to handle errors appropriately.
   */
  it('should preserve error handling for invalid status values', async () => {
    console.log('\n=== Testing error handling for invalid status ===');

    const mockPatch = apiClient.patch as jest.Mock;
    mockPatch.mockRejectedValue({
      response: {
        status: 422,
        data: { detail: 'Invalid status value' },
      },
    });

    const validUuid = '550e8400-e29b-41d4-a716-446655440000';
    const invalidStatus = 'InvalidStatus' as any;

    let errorCaught = false;

    try {
      await updateReadingListStatus(validUuid, invalidStatus);
    } catch (error) {
      errorCaught = true;
    }

    // Verify API was called (validation happens on backend)
    expect(mockPatch).toHaveBeenCalledTimes(1);

    // Verify error was propagated
    expect(errorCaught).toBe(true);

    console.log('✓ Error handling for invalid status preserved');
    console.log('✓ API call made with valid UUID but invalid status');
    console.log('✓ Error properly propagated to caller');
  });

  /**
   * Property 2.10: Error handling for invalid rating values is preserved
   *
   * **Validates: Requirement 3.5**
   *
   * For valid UUID article_id but invalid rating values (e.g., 0, 6, -1),
   * the system SHALL continue to handle errors appropriately.
   */
  it('should preserve error handling for invalid rating values', async () => {
    console.log('\n=== Testing error handling for invalid ratings ===');

    const mockPatch = apiClient.patch as jest.Mock;
    mockPatch.mockRejectedValue({
      response: {
        status: 422,
        data: { detail: 'Rating must be between 1 and 5' },
      },
    });

    const validUuid = '550e8400-e29b-41d4-a716-446655440000';
    const invalidRating = 6;

    let errorCaught = false;

    try {
      await updateReadingListRating(validUuid, invalidRating);
    } catch (error) {
      errorCaught = true;
    }

    // Verify API was called (validation happens on backend)
    expect(mockPatch).toHaveBeenCalledTimes(1);

    // Verify error was propagated
    expect(errorCaught).toBe(true);

    console.log('✓ Error handling for invalid rating preserved');
    console.log('✓ API call made with valid UUID but invalid rating');
    console.log('✓ Error properly propagated to caller');
  });
});
