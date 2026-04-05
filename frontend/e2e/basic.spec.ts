import { test, expect } from '@playwright/test';

test.describe('Basic E2E Tests', () => {
  test('should load the login page', async ({ page }) => {
    await page.goto('/');

    // Check if the page title is correct
    await expect(page).toHaveTitle(/Tech News Agent/);

    // Check if login button exists
    const loginButton = page.getByRole('button', {
      name: /login with discord/i,
    });
    await expect(loginButton).toBeVisible();
  });

  test('should have responsive navigation', async ({ page }) => {
    // Set viewport to mobile size
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');

    // On mobile, the page should still be accessible
    await expect(page).toHaveTitle(/Tech News Agent/);
  });
});
