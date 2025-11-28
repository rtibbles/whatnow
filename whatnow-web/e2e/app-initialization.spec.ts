import { test, expect } from '@playwright/test';

test.describe('App Initialization', () => {
  test('should load the app and initialize database', async ({ page }) => {
    await page.goto('/');

    // Wait for database initialization
    await expect(page.locator('text=Welcome to WhatNow')).toBeVisible({ timeout: 10000 });

    // Check that main sections are visible
    await expect(page.locator('text=Work Session')).toBeVisible();
    await expect(page.locator('text=Google Calendar')).toBeVisible();
    await expect(page.locator('text=GitHub')).toBeVisible();
    await expect(page.locator('text=Settings')).toBeVisible();
  });

  test('should not show database error on first load', async ({ page }) => {
    await page.goto('/');

    // Should not show error state
    await expect(page.locator('text=Database Error')).not.toBeVisible();
  });

  test('should handle concurrent initialization gracefully', async ({ page, context }) => {
    // Open multiple pages simultaneously to test race condition fix
    const [page1, page2, page3] = await Promise.all([
      context.newPage(),
      context.newPage(),
      context.newPage(),
    ]);

    await Promise.all([
      page1.goto('/'),
      page2.goto('/'),
      page3.goto('/'),
    ]);

    // All pages should successfully initialize
    await expect(page1.locator('text=Welcome to WhatNow')).toBeVisible({ timeout: 10000 });
    await expect(page2.locator('text=Welcome to WhatNow')).toBeVisible({ timeout: 10000 });
    await expect(page3.locator('text=Welcome to WhatNow')).toBeVisible({ timeout: 10000 });

    // Clean up
    await page1.close();
    await page2.close();
    await page3.close();
  });
});
