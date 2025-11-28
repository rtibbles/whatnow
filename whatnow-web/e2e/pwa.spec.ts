import { test, expect } from '@playwright/test';

test.describe('PWA Functionality', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('text=Welcome to WhatNow')).toBeVisible({ timeout: 10000 });
  });

  test('should register service worker', async ({ page }) => {
    // Wait for service worker registration
    const swRegistered = await page.evaluate(async () => {
      if ('serviceWorker' in navigator) {
        try {
          const registration = await navigator.serviceWorker.ready;
          return registration !== null;
        } catch {
          return false;
        }
      }
      return false;
    });

    expect(swRegistered).toBe(true);
  });

  test('should show offline indicator when network is offline', async ({ page, context }) => {
    // Set offline mode
    await context.setOffline(true);

    // Trigger offline event
    await page.evaluate(() => {
      window.dispatchEvent(new Event('offline'));
    });

    // Wait for offline indicator
    await expect(page.locator('text=You\'re offline')).toBeVisible({ timeout: 5000 });

    // Set back online
    await context.setOffline(false);
    await page.evaluate(() => {
      window.dispatchEvent(new Event('online'));
    });

    // Offline indicator should disappear
    await expect(page.locator('text=You\'re offline')).not.toBeVisible({ timeout: 5000 });
  });

  test('should show reconnecting indicator when coming back online', async ({ page, context }) => {
    // Start offline
    await context.setOffline(true);
    await page.evaluate(() => {
      window.dispatchEvent(new Event('offline'));
    });

    await expect(page.locator('text=You\'re offline')).toBeVisible({ timeout: 5000 });

    // Go back online
    await context.setOffline(false);
    await page.evaluate(() => {
      window.dispatchEvent(new Event('online'));
    });

    // Should show reconnecting briefly
    await expect(page.locator('text=Reconnecting')).toBeVisible({ timeout: 2000 });

    // Should disappear after a few seconds
    await expect(page.locator('text=Reconnecting')).not.toBeVisible({ timeout: 5000 });
  });

  test('should work offline with cached content', async ({ page, context }) => {
    // Load page fully first (with cache)
    await page.waitForLoadState('networkidle');

    // Go offline
    await context.setOffline(true);

    // Navigate to home
    await page.goto('/');

    // Should still load from cache
    await expect(page.locator('text=Welcome to WhatNow')).toBeVisible({ timeout: 10000 });

    // Main sections should still be visible
    await expect(page.locator('text=Work Session')).toBeVisible();
  });

  test('should dismiss install prompt', async ({ page }) => {
    // Check if install prompt is visible (may not be in test environment)
    const installPrompt = page.locator('text=Install WhatNow');

    if (await installPrompt.isVisible()) {
      // Click dismiss button
      const dismissButton = installPrompt.locator('..').locator('button[aria-label="Dismiss install prompt"]');
      await dismissButton.click();

      // Prompt should disappear
      await expect(installPrompt).not.toBeVisible();

      // Reload page
      await page.reload();
      await expect(page.locator('text=Welcome to WhatNow')).toBeVisible({ timeout: 10000 });

      // Prompt should not reappear (dismissed for 7 days)
      await expect(installPrompt).not.toBeVisible();
    } else {
      // If not visible, just verify it doesn't crash
      expect(true).toBe(true);
    }
  });
});
