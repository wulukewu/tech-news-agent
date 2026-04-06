/**
 * Bug Condition Exploration Test - Frontend Undefined article_id
 *
 * **Validates: Requirements 1.3, 1.4, 2.3, 2.4**
 *
 * Property 1: Bug Condition - Frontend Sends Undefined article_id to API
 *
 * CRITICAL: This test MUST FAIL on unfixed code - failure confirms the bug exists
 *
 * This test verifies that the frontend sends undefined/null/empty article_id
 * values to the backend API without validation, causing 400/422 errors.
 *
 * Expected counterexamples on UNFIXED code:
 * - API receives { article_id: "undefined" } in request body
 * - API receives DELETE /api/reading-list/undefined in URL
 * - Backend returns 400 or 422 validation errors
 * - No validation guards in frontend components
 *
 * When FIXED:
 * - Frontend validates article_id before API calls
 * - Invalid values are caught and handled gracefully
 * - No invalid requests are sent to backend
 */

import * as fc from 'fast-check';
import {
  addToReadingList,
  updateReadingListStatus,
  updateReadingListRating,
  removeFromReadingList,
} from '@/lib/api/readingList';

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

describe('Bug Condition Exploration - Frontend Undefined article_id', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  /**
   * Property 1: Bug Condition - addToReadingList sends undefined article_id
   *
   * For any API call where article_id is undefined/null/empty,
   * the UNFIXED code SHALL send the invalid value to the backend.
   * The FIXED code SHALL prevent the API call and handle the error gracefully.
   */
  it('should detect undefined article_id sent to addToReadingList API', async () => {
    console.log('\n=== Testing addToReadingList with undefined article_id ===');

    // Mock API client to capture what gets sent
    const mockPost = apiClient.post as jest.Mock;
    mockPost.mockRejectedValue({
      response: { status: 422, data: { detail: 'Invalid article_id' } },
    });

    let apiWasCalled = false;
    let sentPayload: any = null;

    try {
      // Call with undefined article_id (simulating malformed article object)
      await addToReadingList(undefined as any);
    } catch (error) {
      // Capture if API was called
      apiWasCalled = mockPost.mock.calls.length > 0;
      if (apiWasCalled) {
        sentPayload = mockPost.mock.calls[0][1];
      }
    }

    console.log(`API was called: ${apiWasCalled}`);
    console.log(`Sent payload:`, sentPayload);

    // On UNFIXED code: API is called with undefined (bug exists)
    // On FIXED code: API is NOT called, validation prevents it
    if (apiWasCalled) {
      console.log('\n=== Bug Detected - Counterexample Found ===');
      console.log('✗ API was called with undefined article_id');
      console.log(
        `✗ Backend received: { article_id: ${sentPayload?.article_id} }`,
      );
      console.log('✗ No validation guard prevented the invalid API call');
      console.log('\nThis proves the bug exists in the unfixed codebase');

      // Document the counterexample
      expect(sentPayload).toBeDefined();
      expect(sentPayload.article_id).toBeUndefined();
    } else {
      console.log('\n=== Bug Fixed - Validation Working ===');
      console.log('✓ API was NOT called with undefined article_id');
      console.log('✓ Validation guard prevented the invalid API call');
      console.log('✓ Error was handled gracefully');
    }

    // The test passes when validation prevents the API call (apiWasCalled = false)
    // The test fails when API is called with undefined (apiWasCalled = true)
    expect(apiWasCalled).toBe(false);
  });

  /**
   * Property 2: Bug Condition - updateReadingListStatus sends null article_id
   */
  it('should detect null article_id sent to updateReadingListStatus API', async () => {
    console.log(
      '\n=== Testing updateReadingListStatus with null article_id ===',
    );

    const mockPatch = apiClient.patch as jest.Mock;
    mockPatch.mockRejectedValue({
      response: { status: 400, data: { detail: 'Bad Request' } },
    });

    let apiWasCalled = false;
    let requestUrl: string = '';

    try {
      await updateReadingListStatus(null as any, 'Read');
    } catch (error) {
      apiWasCalled = mockPatch.mock.calls.length > 0;
      if (apiWasCalled) {
        requestUrl = mockPatch.mock.calls[0][0];
      }
    }

    console.log(`API was called: ${apiWasCalled}`);
    console.log(`Request URL: ${requestUrl}`);

    if (apiWasCalled) {
      console.log('\n=== Bug Detected - Counterexample Found ===');
      console.log('✗ API was called with null article_id');
      console.log(`✗ Backend received URL: ${requestUrl}`);
      console.log('✗ URL contains "null" instead of valid UUID');
      console.log('\nThis proves the bug exists in the unfixed codebase');

      expect(requestUrl).toContain('null');
    } else {
      console.log('\n=== Bug Fixed - Validation Working ===');
      console.log('✓ API was NOT called with null article_id');
      console.log('✓ Validation guard prevented the invalid API call');
    }

    expect(apiWasCalled).toBe(false);
  });

  /**
   * Property 3: Bug Condition - updateReadingListRating sends empty string article_id
   */
  it('should detect empty string article_id sent to updateReadingListRating API', async () => {
    console.log(
      '\n=== Testing updateReadingListRating with empty article_id ===',
    );

    const mockPatch = apiClient.patch as jest.Mock;
    mockPatch.mockRejectedValue({
      response: { status: 422, data: { detail: 'Validation error' } },
    });

    let apiWasCalled = false;
    let requestUrl: string = '';

    try {
      await updateReadingListRating('', 3);
    } catch (error) {
      apiWasCalled = mockPatch.mock.calls.length > 0;
      if (apiWasCalled) {
        requestUrl = mockPatch.mock.calls[0][0];
      }
    }

    console.log(`API was called: ${apiWasCalled}`);
    console.log(`Request URL: ${requestUrl}`);

    if (apiWasCalled) {
      console.log('\n=== Bug Detected - Counterexample Found ===');
      console.log('✗ API was called with empty string article_id');
      console.log(`✗ Backend received URL: ${requestUrl}`);
      console.log('✗ URL is malformed with empty article_id');
      console.log('\nThis proves the bug exists in the unfixed codebase');

      expect(requestUrl).toBeDefined();
    } else {
      console.log('\n=== Bug Fixed - Validation Working ===');
      console.log('✓ API was NOT called with empty article_id');
      console.log('✓ Validation guard prevented the invalid API call');
    }

    expect(apiWasCalled).toBe(false);
  });

  /**
   * Property 4: Bug Condition - removeFromReadingList sends "undefined" string
   */
  it('should detect "undefined" string sent to removeFromReadingList API', async () => {
    console.log(
      '\n=== Testing removeFromReadingList with "undefined" string ===',
    );

    const mockDelete = apiClient.delete as jest.Mock;
    mockDelete.mockRejectedValue({
      response: { status: 400, data: { detail: 'Invalid UUID format' } },
    });

    let apiWasCalled = false;
    let requestUrl: string = '';

    try {
      // Simulate what happens when article.id is undefined and gets stringified
      const undefinedArticleId = String(undefined); // "undefined"
      await removeFromReadingList(undefinedArticleId);
    } catch (error) {
      apiWasCalled = mockDelete.mock.calls.length > 0;
      if (apiWasCalled) {
        requestUrl = mockDelete.mock.calls[0][0];
      }
    }

    console.log(`API was called: ${apiWasCalled}`);
    console.log(`Request URL: ${requestUrl}`);

    if (apiWasCalled) {
      console.log('\n=== Bug Detected - Counterexample Found ===');
      console.log('✗ API was called with "undefined" string as article_id');
      console.log(`✗ Backend received: DELETE ${requestUrl}`);
      console.log('✗ URL contains literal "undefined" string');
      console.log('\nThis proves the bug exists in the unfixed codebase');

      expect(requestUrl).toContain('undefined');
    } else {
      console.log('\n=== Bug Fixed - Validation Working ===');
      console.log('✓ API was NOT called with "undefined" string');
      console.log('✓ Validation guard prevented the invalid API call');
    }

    expect(apiWasCalled).toBe(false);
  });

  /**
   * Property-Based Test: Verify all API methods reject invalid article_id values
   *
   * This test uses property-based testing to verify that ALL reading list
   * API functions properly validate article_id before making API calls.
   */
  it('should validate article_id across all API methods using property-based testing', async () => {
    console.log('\n=== Property-Based Test: All API Methods ===');

    await fc.assert(
      fc.asyncProperty(
        // Generate invalid article_id values
        fc.oneof(
          fc.constant(undefined),
          fc.constant(null),
          fc.constant(''),
          fc.constant('undefined'),
          fc.constant('null'),
        ),
        // Generate API method names
        fc.constantFrom(
          'addToReadingList',
          'updateStatus',
          'updateRating',
          'removeFromReadingList',
        ),
        async (invalidArticleId, apiMethod) => {
          // Reset mocks
          jest.clearAllMocks();

          const mockPost = apiClient.post as jest.Mock;
          const mockPatch = apiClient.patch as jest.Mock;
          const mockDelete = apiClient.delete as jest.Mock;

          // Mock all methods to reject
          mockPost.mockRejectedValue({ response: { status: 422 } });
          mockPatch.mockRejectedValue({ response: { status: 422 } });
          mockDelete.mockRejectedValue({ response: { status: 400 } });

          let apiWasCalled = false;

          try {
            // Call the appropriate API method with invalid article_id
            switch (apiMethod) {
              case 'addToReadingList':
                await addToReadingList(invalidArticleId as any);
                apiWasCalled = mockPost.mock.calls.length > 0;
                break;
              case 'updateStatus':
                await updateReadingListStatus(invalidArticleId as any, 'Read');
                apiWasCalled = mockPatch.mock.calls.length > 0;
                break;
              case 'updateRating':
                await updateReadingListRating(invalidArticleId as any, 3);
                apiWasCalled = mockPatch.mock.calls.length > 0;
                break;
              case 'removeFromReadingList':
                await removeFromReadingList(invalidArticleId as any);
                apiWasCalled = mockDelete.mock.calls.length > 0;
                break;
            }
          } catch (error) {
            // Error is expected
          }

          // On UNFIXED code: API is called (returns false, test fails)
          // On FIXED code: API is NOT called (returns true, test passes)
          const validationWorking = !apiWasCalled;

          if (!validationWorking) {
            console.log(
              `\nCounterexample: ${apiMethod} called with ${invalidArticleId}`,
            );
          }

          return validationWorking;
        },
      ),
      { numRuns: 20 },
    );
  });

  /**
   * Property-Based Test: Verify valid article_id values still work
   *
   * This ensures that validation doesn't break legitimate API calls.
   */
  it('should allow valid UUID article_id values through validation', async () => {
    console.log('\n=== Property-Based Test: Valid UUIDs ===');

    await fc.assert(
      fc.asyncProperty(
        // Generate valid UUID v4 strings
        fc.uuid(),
        fc.constantFrom(
          'addToReadingList',
          'updateStatus',
          'updateRating',
          'removeFromReadingList',
        ),
        async (validArticleId, apiMethod) => {
          // Reset mocks
          jest.clearAllMocks();

          const mockPost = apiClient.post as jest.Mock;
          const mockPatch = apiClient.patch as jest.Mock;
          const mockDelete = apiClient.delete as jest.Mock;

          // Mock all methods to succeed
          mockPost.mockResolvedValue({
            message: 'Success',
            articleId: validArticleId,
          });
          mockPatch.mockResolvedValue({ message: 'Success' });
          mockDelete.mockResolvedValue({ message: 'Success' });

          let apiWasCalled = false;
          let success = false;

          try {
            // Call the appropriate API method with valid article_id
            switch (apiMethod) {
              case 'addToReadingList':
                await addToReadingList(validArticleId);
                apiWasCalled = mockPost.mock.calls.length > 0;
                success = true;
                break;
              case 'updateStatus':
                await updateReadingListStatus(validArticleId, 'Read');
                apiWasCalled = mockPatch.mock.calls.length > 0;
                success = true;
                break;
              case 'updateRating':
                await updateReadingListRating(validArticleId, 3);
                apiWasCalled = mockPatch.mock.calls.length > 0;
                success = true;
                break;
              case 'removeFromReadingList':
                await removeFromReadingList(validArticleId);
                apiWasCalled = mockDelete.mock.calls.length > 0;
                success = true;
                break;
            }
          } catch (error) {
            // Should not error with valid UUID
            success = false;
          }

          // Valid UUIDs should always result in API calls
          return apiWasCalled && success;
        },
      ),
      { numRuns: 10 },
    );
  });
});
