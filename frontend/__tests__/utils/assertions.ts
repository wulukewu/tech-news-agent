/**
 * Custom test assertions and matchers
 *
 * Provides domain-specific assertions for common testing scenarios
 */

import { screen, within } from '@testing-library/react';

/**
 * Assert that an element has accessible name
 */
export function assertAccessibleName(element: HTMLElement, expectedName: string) {
  const accessibleName = element.getAttribute('aria-label') || element.textContent;
  expect(accessibleName).toBe(expectedName);
}

/**
 * Assert that a loading state is shown
 */
export function assertLoadingState() {
  const loadingElements = screen.queryAllByTestId(/loading/i);
  expect(loadingElements.length).toBeGreaterThan(0);
}

/**
 * Assert that no loading state is shown
 */
export function assertNoLoadingState() {
  const loadingElements = screen.queryAllByTestId(/loading/i);
  expect(loadingElements.length).toBe(0);
}

/**
 * Assert that an error message is displayed
 */
export function assertErrorMessage(message?: string) {
  const errorElement = screen.getByRole('alert');
  expect(errorElement).toBeInTheDocument();
  if (message) {
    expect(errorElement).toHaveTextContent(message);
  }
}

/**
 * Assert that no error message is displayed
 */
export function assertNoErrorMessage() {
  const errorElement = screen.queryByRole('alert');
  expect(errorElement).not.toBeInTheDocument();
}

/**
 * Assert that a list has expected number of items
 */
export function assertListLength(listElement: HTMLElement, expectedLength: number) {
  const items = within(listElement).getAllByRole('listitem');
  expect(items).toHaveLength(expectedLength);
}

/**
 * Assert that pagination controls are present
 */
export function assertPaginationControls() {
  expect(screen.getByRole('navigation', { name: /pagination/i })).toBeInTheDocument();
}

/**
 * Assert that an element is visually hidden but accessible
 */
export function assertVisuallyHidden(element: HTMLElement) {
  const styles = window.getComputedStyle(element);
  expect(
    styles.position === 'absolute' &&
      styles.width === '1px' &&
      styles.height === '1px' &&
      styles.overflow === 'hidden'
  ).toBe(true);
}

/**
 * Assert that a form field has validation error
 */
export function assertFieldError(fieldName: string, errorMessage?: string) {
  const field = screen.getByRole('textbox', { name: new RegExp(fieldName, 'i') });
  expect(field).toHaveAttribute('aria-invalid', 'true');

  if (errorMessage) {
    const errorId = field.getAttribute('aria-describedby');
    if (errorId) {
      const errorElement = document.getElementById(errorId);
      expect(errorElement).toHaveTextContent(errorMessage);
    }
  }
}

/**
 * Assert that a button is in loading state
 */
export function assertButtonLoading(button: HTMLElement) {
  expect(button).toBeDisabled();
  expect(within(button).queryByTestId('loading-spinner')).toBeInTheDocument();
}

/**
 * Assert that an article card displays correct information
 */
export function assertArticleCard(
  card: HTMLElement,
  expected: { title: string; author?: string; source?: string }
) {
  expect(within(card).getByText(expected.title)).toBeInTheDocument();
  if (expected.author) {
    expect(within(card).getByText(new RegExp(expected.author, 'i'))).toBeInTheDocument();
  }
  if (expected.source) {
    expect(within(card).getByText(new RegExp(expected.source, 'i'))).toBeInTheDocument();
  }
}

/**
 * Assert that a feed card displays correct information
 */
export function assertFeedCard(
  card: HTMLElement,
  expected: { name: string; description?: string; subscriberCount?: number }
) {
  expect(within(card).getByText(expected.name)).toBeInTheDocument();
  if (expected.description) {
    expect(within(card).getByText(expected.description)).toBeInTheDocument();
  }
  if (expected.subscriberCount !== undefined) {
    expect(
      within(card).getByText(new RegExp(`${expected.subscriberCount}`, 'i'))
    ).toBeInTheDocument();
  }
}
