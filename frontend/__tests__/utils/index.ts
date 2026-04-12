/**
 * Shared test utilities index
 *
 * Re-exports all shared test utilities for convenient importing
 */

// Re-export everything from test-utils
export * from './test-utils';

// Re-export render utilities
export {
  createTestQueryClient,
  QueryClientWrapper,
  renderWithQueryClient,
  createWrapper,
  renderWithAllProviders,
  waitForLoadingToFinish,
} from './render';

// Re-export mock utilities
export {
  mockArticle,
  mockUser,
  mockFeed,
  mockReadingListItem,
  mockArticles,
  mockFeeds,
  mockPaginatedResponse,
  mockErrorResponse,
  mockAxiosError,
} from './mocks';

// Re-export API mock utilities
export {
  createApiHandlers,
  setupMockServer,
  mockApiResponse,
  mockApiErrorResponse,
  mockPaginatedApiResponse,
} from './api-mocks';

// Re-export custom assertions
export {
  assertAccessibleName,
  assertLoadingState,
  assertNoLoadingState,
  assertErrorMessage,
  assertNoErrorMessage,
  assertListLength,
  assertPaginationControls,
  assertVisuallyHidden,
  assertFieldError,
  assertButtonLoading,
  assertArticleCard,
  assertFeedCard,
} from './assertions';

// Re-export wait utilities
export {
  waitForElementToBeRemoved,
  waitForApiCall,
  waitForQuerySuccess,
  waitForMutationSuccess,
  waitForTextContent,
  waitForAttribute,
  waitForElementToBeVisible,
  waitForAll,
} from './wait-for';
