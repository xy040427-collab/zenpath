import { test, expect } from '@playwright/test';

test.describe('Navigation', () => {
  test('should have navigation elements on home page', async ({ page }) => {
    await page.goto('/');
    // Look for nav or header element
    const nav = page.locator('nav, header, [role="navigation"]').first();
    await expect(nav).toBeVisible();
  });

  test('should navigate to pricing page', async ({ page }) => {
    await page.goto('/pricing');
    await expect(page.locator('body')).toBeVisible();
    const bodyText = await page.locator('body').innerText();
    expect(bodyText.length).toBeGreaterThan(0);
  });

  test('should navigate to calculator page', async ({ page }) => {
    await page.goto('/calculator');
    await expect(page.locator('body')).toBeVisible();
    const bodyText = await page.locator('body').innerText();
    expect(bodyText.length).toBeGreaterThan(0);
  });

  test('should have footer on home page', async ({ page }) => {
    await page.goto('/');
    const footer = page.locator('footer, [role="contentinfo"]').first();
    await expect(footer).toBeVisible();
  });
});
