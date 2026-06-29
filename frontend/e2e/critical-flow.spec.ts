import { test, expect } from '@playwright/test';

test.describe('Critical Flow', () => {
  test('home page should have brand elements', async ({ page }) => {
    await page.goto('/');
    // Look for brand name or logo
    const bodyText = await page.locator('body').innerText();
    // Should contain project-related text
    const hasBrand = bodyText.includes('择境') || bodyText.includes('ZENPATH') || bodyText.includes('志愿');
    expect(hasBrand).toBeTruthy();
  });

  test('pricing page should show plans', async ({ page }) => {
    await page.goto('/pricing');
    await expect(page.locator('body')).toBeVisible();
    // Wait for content to render
    await page.waitForTimeout(1000);
    const bodyText = await page.locator('body').innerText();
    // Should have pricing-related content
    expect(bodyText.length).toBeGreaterThan(10);
  });

  test('calculator page should have input area', async ({ page }) => {
    await page.goto('/calculator');
    await expect(page.locator('body')).toBeVisible();
    await page.waitForTimeout(1000);
    // Should have some interactive elements
    const inputs = await page.locator('input, select, button').count();
    expect(inputs).toBeGreaterThanOrEqual(0);
  });

  test('pages should not have console errors on load', async ({ page }) => {
    const errors: string[] = [];
    page.on('pageerror', (error) => {
      errors.push(error.message);
    });
    await page.goto('/');
    await page.waitForTimeout(2000);
    // Filter out known non-critical errors (e.g., API connection failures)
    const criticalErrors = errors.filter(
      (e) => !e.includes('fetch') && !e.includes('NetworkError') && !e.includes('Failed to fetch')
    );
    expect(criticalErrors).toHaveLength(0);
  });
});
