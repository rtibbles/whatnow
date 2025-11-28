import { test, expect } from '@playwright/test';
import path from 'path';

test.describe('Settings Management', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('text=Welcome to WhatNow')).toBeVisible({ timeout: 10000 });
  });

  test('should display settings panel', async ({ page }) => {
    // Scroll to settings section
    await page.locator('text=Settings').scrollIntoViewIfNeeded();

    // Check settings sections are visible
    await expect(page.locator('text=Notifications')).toBeVisible();
    await expect(page.locator('text=Synchronization')).toBeVisible();
    await expect(page.locator('text=Appearance')).toBeVisible();
    await expect(page.locator('text=Data Management')).toBeVisible();
  });

  test('should update ping interval setting', async ({ page }) => {
    // Scroll to settings
    await page.locator('text=Settings').scrollIntoViewIfNeeded();

    // Find ping interval slider
    const slider = page.locator('input[type="range"]').first();
    await expect(slider).toBeVisible();

    // Get initial value
    const initialValue = await slider.getAttribute('value');

    // Change slider value
    await slider.fill('60');

    // Wait for update to persist
    await page.waitForTimeout(500);

    // Reload page
    await page.reload();
    await expect(page.locator('text=Welcome to WhatNow')).toBeVisible({ timeout: 10000 });

    // Scroll to settings again
    await page.locator('text=Settings').scrollIntoViewIfNeeded();

    // Verify value persisted
    const newSlider = page.locator('input[type="range"]').first();
    const newValue = await newSlider.getAttribute('value');
    expect(newValue).toBe('60');
    expect(newValue).not.toBe(initialValue);
  });

  test('should export data', async ({ page }) => {
    await page.locator('text=Settings').scrollIntoViewIfNeeded();

    // Set up download listener
    const downloadPromise = page.waitForEvent('download');

    // Click export button
    const exportButton = page.locator('button:has-text("Export All Data")');
    await expect(exportButton).toBeVisible();
    await exportButton.click();

    // Wait for download
    const download = await downloadPromise;

    // Verify download filename pattern
    const filename = download.suggestedFilename();
    expect(filename).toMatch(/whatnow-backup-\d{4}-\d{2}-\d{2}\.json/);
  });

  test('should prevent concurrent background sync toggles', async ({ page }) => {
    await page.locator('text=Settings').scrollIntoViewIfNeeded();

    // Find background sync toggle
    const syncToggle = page.locator('text=Background Sync').locator('..').locator('input[type="checkbox"]');

    // Get initial state
    const initialState = await syncToggle.isChecked();

    // Rapidly click toggle multiple times
    await Promise.all([
      syncToggle.click(),
      syncToggle.click(),
      syncToggle.click(),
    ]).catch(() => {
      // Some clicks may fail due to guard - that's expected
    });

    // Wait for operations to complete
    await page.waitForTimeout(1000);

    // Check final state is consistent (toggled once)
    const finalState = await syncToggle.isChecked();
    expect(finalState).toBe(!initialState);
  });

  test('should show database statistics', async ({ page }) => {
    await page.locator('text=Settings').scrollIntoViewIfNeeded();

    // Check statistics are displayed
    await expect(page.locator('text=Pings')).toBeVisible();
    await expect(page.locator('text=TODOs')).toBeVisible();
    await expect(page.locator('text=Storage')).toBeVisible();

    // Should show numeric values
    const statsSection = page.locator('text=Pings').locator('..');
    await expect(statsSection).toContainText(/\d+/);
  });

  test('should reset settings to defaults', async ({ page }) => {
    await page.locator('text=Settings').scrollIntoViewIfNeeded();

    // Change a setting first
    const slider = page.locator('input[type="range"]').first();
    await slider.fill('90');
    await page.waitForTimeout(500);

    // Accept the confirmation dialog
    page.on('dialog', dialog => dialog.accept());

    // Click reset button
    const resetButton = page.locator('button:has-text("Reset All Settings")');
    await expect(resetButton).toBeVisible();
    await resetButton.click();

    // Wait for reset to complete
    await page.waitForTimeout(500);

    // Reload to verify
    await page.reload();
    await expect(page.locator('text=Welcome to WhatNow')).toBeVisible({ timeout: 10000 });

    // Check slider is back to default (45)
    await page.locator('text=Settings').scrollIntoViewIfNeeded();
    const newSlider = page.locator('input[type="range"]').first();
    const value = await newSlider.getAttribute('value');
    expect(value).toBe('45');
  });
});
