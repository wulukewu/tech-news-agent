/**
 * Custom wait utilities for async testing
 *
 * Provides specialized wait functions for common async scenarios
 */

import { waitFor } from '@testing-library/react';

/**
 * Wait for an element to be removed from the DOM
 */
export async function waitForElementToBeRemoved(
  callback: () => HTMLElement | null,
  options?: { timeout?: number }
) {
  await waitFor(
    () => {
      const element = callback();
      expect(element).not.toBeInTheDocument();
    },
    { timeout: options?.timeout || 3000 }
  );
}

/**
 * Wait for loading to finish
 */
export async function waitForLoadingToFinish(timeout: number = 3000) {
  await waitFor(
    () => {
      const loadingElements = document.querySelectorAll('[data-testid*="loading"]');
      expect(loadingElements.length).toBe(0);
    },
    { timeout }
  );
}

/**
 * Wait for API call to complete
 */
export async function waitForApiCall(timeout: number = 5000) {
  await waitFor(() => {}, { timeout });
}

/**
 * Wait for query to be successful
 */
export async function waitForQuerySuccess(
  queryKey: string[],
  queryClient: any,
  timeout: number = 5000
) {
  await waitFor(
    () => {
      const query = queryClient.getQueryState(queryKey);
      expect(query?.status).toBe('success');
    },
    { timeout }
  );
}

/**
 * Wait for mutation to complete
 */
export async function waitForMutationSuccess(
  mutationKey: string[],
  queryClient: any,
  timeout: number = 5000
) {
  await waitFor(
    () => {
      const mutation = queryClient.getMutationCache().find({ mutationKey });
      expect(mutation?.state.status).toBe('success');
    },
    { timeout }
  );
}

/**
 * Wait for element to have specific text content
 */
export async function waitForTextContent(
  element: HTMLElement,
  expectedText: string | RegExp,
  timeout: number = 3000
) {
  await waitFor(
    () => {
      if (typeof expectedText === 'string') {
        expect(element).toHaveTextContent(expectedText);
      } else {
        expect(element.textContent).toMatch(expectedText);
      }
    },
    { timeout }
  );
}

/**
 * Wait for element to have specific attribute
 */
export async function waitForAttribute(
  element: HTMLElement,
  attribute: string,
  expectedValue: string,
  timeout: number = 3000
) {
  await waitFor(
    () => {
      expect(element).toHaveAttribute(attribute, expectedValue);
    },
    { timeout }
  );
}

/**
 * Wait for element to be visible
 */
export async function waitForElementToBeVisible(
  callback: () => HTMLElement,
  timeout: number = 3000
) {
  await waitFor(
    () => {
      const element = callback();
      expect(element).toBeVisible();
    },
    { timeout }
  );
}

/**
 * Wait for multiple conditions
 */
export async function waitForAll(
  conditions: Array<() => void | Promise<void>>,
  timeout: number = 5000
) {
  await waitFor(
    async () => {
      for (const condition of conditions) {
        await condition();
      }
    },
    { timeout }
  );
}
