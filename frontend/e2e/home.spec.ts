import { test, expect } from '@playwright/test';

test.describe('Home Page', () => {
  test('should load without white screen', async ({ page }) => {
    await page.goto('/');
    // Body should be visible
    await expect(page.locator('body')).toBeVisible();
    // Should not be a blank page
    const bodyText = await page.locator('body').innerText();
    expect(bodyText.length).toBeGreaterThan(0);
  });

  test('should have page title', async ({ page }) => {
    await page.goto('/');
    const title = await page.title();
    expect(title).toBeTruthy();
    expect(title.length).toBeGreaterThan(0);
  });

  test('should have main content area', async ({ page }) => {
    await page.goto('/');
    // Root div should have content
    const root = page.locator('#root');
    await expect(root).toBeVisible();
    const rootChildren = await root.locator('> *').count();
    expect(rootChildren).toBeGreaterThan(0);
  });
});
