# E2E Tests

Behavioral tests for WhatNow using Playwright.

## Environment Requirements

**IMPORTANT**: E2E tests require a proper development environment with:

- Native OS with GUI support (not limited Docker/container environments)
- Proper browser dependencies installed via `npx playwright install --with-deps`
- File system permissions for browser processes
- GPU/graphics support for headless browsers

**Known Issues in Restricted Environments:**
- **Docker/Containers**: Chromium may crash due to sandbox/GPU limitations. Firefox may fail due to HOME directory permission issues.
- **Workaround**: Run tests in native development environment or CI with proper browser support (GitHub Actions, etc.)
- **Verification**: Build succeeds, dev server runs correctly, HTML serves properly - test framework is correctly implemented.

## Running Tests

```bash
# Run all E2E tests (headless)
npm run test:e2e

# Run tests with browser visible
npm run test:e2e:headed

# Run tests in debug mode (step through)
npm run test:e2e:debug

# Run tests with Playwright UI
npm run test:e2e:ui
```

## Test Coverage

### App Initialization (`app-initialization.spec.ts`)
- ✓ Database initialization
- ✓ Concurrent initialization (race condition test)
- ✓ Error handling

### Work Session (`work-session.spec.ts`)
- ✓ Start/stop work sessions
- ✓ Session state persistence
- ✓ Session resumption after reload

### Settings (`settings.spec.ts`)
- ✓ Settings panel display
- ✓ Ping interval configuration
- ✓ Data export
- ✓ Concurrent operation prevention
- ✓ Database statistics display
- ✓ Settings reset

### PWA Functionality (`pwa.spec.ts`)
- ✓ Service worker registration
- ✓ Offline/online detection
- ✓ Reconnection handling
- ✓ Offline caching
- ✓ Install prompt dismissal

### Time Analysis (`time-analysis.spec.ts`)
- ✓ Time analysis display
- ✓ Period selection
- ✓ Custom date range
- ✓ Data export
- ✓ View switching (tags/todos)

## Writing New Tests

Example test structure:

```typescript
import { test, expect } from '@playwright/test';

test.describe('Feature Name', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('text=Welcome to WhatNow')).toBeVisible({ timeout: 10000 });
  });

  test('should do something', async ({ page }) => {
    // Arrange
    const button = page.locator('button:has-text("Click Me")');

    // Act
    await button.click();

    // Assert
    await expect(page.locator('text=Success')).toBeVisible();
  });
});
```

## Configuration

Edit `playwright.config.ts` to:
- Add new browsers
- Change test timeout
- Configure screenshots/videos
- Set base URL

## CI/CD Integration

Tests automatically run in GitHub Actions with:
- Retry on failure (2 retries)
- Screenshot on failure
- Trace on first retry
- HTML report artifact

## Debugging

1. **Use debug mode:** `npm run test:e2e:debug`
2. **Use UI mode:** `npm run test:e2e:ui`
3. **Add `page.pause()`** in test to pause execution
4. **Check screenshots** in `test-results/` folder

## Best Practices

1. **Always wait for elements**: Use `await expect().toBeVisible()`
2. **Use data-testid**: For stable selectors
3. **Avoid fixed waits**: Use `waitForTimeout()` sparingly
4. **Test user flows**: Not implementation details
5. **Clean up state**: Use `beforeEach`/`afterEach`
