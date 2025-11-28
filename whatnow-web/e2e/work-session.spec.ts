import { test, expect } from '@playwright/test';

test.describe('Work Session Management', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('text=Welcome to WhatNow')).toBeVisible({ timeout: 10000 });
  });

  test('should start a work session', async ({ page }) => {
    // Click start session button
    const startButton = page.locator('button:has-text("Start Session")');
    await expect(startButton).toBeVisible();
    await startButton.click();

    // Should show active session state
    await expect(page.locator('text=Active Session')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('button:has-text("Stop Session")')).toBeVisible();
  });

  test('should stop a work session', async ({ page }) => {
    // Start session first
    const startButton = page.locator('button:has-text("Start Session")');
    await startButton.click();
    await expect(page.locator('text=Active Session')).toBeVisible({ timeout: 5000 });

    // Stop session
    const stopButton = page.locator('button:has-text("Stop Session")');
    await stopButton.click();

    // Should return to idle state
    await expect(page.locator('button:has-text("Start Session")')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('text=Active Session')).not.toBeVisible();
  });

  test('should persist session state across page reload', async ({ page }) => {
    // Start session
    await page.locator('button:has-text("Start Session")').click();
    await expect(page.locator('text=Active Session')).toBeVisible({ timeout: 5000 });

    // Reload page
    await page.reload();
    await expect(page.locator('text=Welcome to WhatNow')).toBeVisible({ timeout: 10000 });

    // Session should still be active
    await expect(page.locator('text=Active Session')).toBeVisible();
    await expect(page.locator('button:has-text("Stop Session")')).toBeVisible();
  });
});
