import { test, expect } from '@playwright/test';

test.describe('Time Analysis', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('text=Welcome to WhatNow')).toBeVisible({ timeout: 10000 });
  });

  test('should display time analysis section', async ({ page }) => {
    // Scroll to time analysis
    await page.locator('text=Time Analysis').scrollIntoViewIfNeeded();

    // Check time period dropdown is visible
    await expect(page.locator('text=Time Period')).toBeVisible();

    // Check analyze button is visible
    await expect(page.locator('button:has-text("Analyze")')).toBeVisible();
  });

  test('should analyze time for different periods', async ({ page }) => {
    await page.locator('text=Time Analysis').scrollIntoViewIfNeeded();

    // Select time period
    const periodSelect = page.locator('select').first();
    await periodSelect.selectOption('last7Days');

    // Click analyze
    const analyzeButton = page.locator('button:has-text("Analyze")');
    await analyzeButton.click();

    // Should show loading or results
    await page.waitForTimeout(1000);

    // Even with no data, should not show error
    await expect(page.locator('text=Analysis failed')).not.toBeVisible();
  });

  test('should allow custom date range selection', async ({ page }) => {
    await page.locator('text=Time Analysis').scrollIntoViewIfNeeded();

    // Select custom range
    const periodSelect = page.locator('select').first();
    await periodSelect.selectOption('custom');

    // Date pickers should appear
    await expect(page.locator('input[type="date"]')).toHaveCount(2);
  });

  test('should export analysis data', async ({ page }) => {
    await page.locator('text=Time Analysis').scrollIntoViewIfNeeded();

    // Run analysis first
    const analyzeButton = page.locator('button:has-text("Analyze")');
    await analyzeButton.click();
    await page.waitForTimeout(1000);

    // Check export buttons are visible
    await expect(page.locator('button:has-text("Export Pings (CSV)")')).toBeVisible();
    await expect(page.locator('button:has-text("Export Pings (JSON)")')).toBeVisible();
    await expect(page.locator('button:has-text("Export Analysis (CSV)")')).toBeVisible();
    await expect(page.locator('button:has-text("Export Analysis (JSON)")')).toBeVisible();
  });

  test('should switch between tag and todo views', async ({ page }) => {
    await page.locator('text=Time Analysis').scrollIntoViewIfNeeded();

    // Run analysis
    const analyzeButton = page.locator('button:has-text("Analyze")');
    await analyzeButton.click();
    await page.waitForTimeout(1000);

    // Check tabs are visible
    const tagTab = page.locator('button:has-text("By Tag")');
    const todoTab = page.locator('button:has-text("By TODO")');

    await expect(tagTab).toBeVisible();
    await expect(todoTab).toBeVisible();

    // Click TODO tab
    await todoTab.click();

    // Should show TODO view (no error)
    await page.waitForTimeout(500);
    await expect(page.locator('text=Analysis failed')).not.toBeVisible();

    // Click back to Tag tab
    await tagTab.click();
    await page.waitForTimeout(500);
    await expect(page.locator('text=Analysis failed')).not.toBeVisible();
  });
});
