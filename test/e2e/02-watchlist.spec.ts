import { test, expect } from '@playwright/test';

const BASE_URL = process.env.BASE_URL || 'http://localhost:8000';

test.describe('TEST-03: Watchlist add and remove via API', () => {

  test.afterEach(async ({ request }) => {
    // Cleanup: remove PYPL if it exists (idempotent)
    await request.delete(`${BASE_URL}/api/watchlist/PYPL`).catch(() => {});
  });

  test('add ticker via API appears in watchlist UI', async ({ page, request }) => {
    // Add PYPL via REST API
    const addResp = await request.post(`${BASE_URL}/api/watchlist`, {
      data: { ticker: 'PYPL' },
    });
    expect(addResp.status()).toBe(201);

    // Navigate to app and verify PYPL appears
    await page.goto(BASE_URL);
    const pyplRow = page.getByTestId('watchlist-row-PYPL');
    await expect(pyplRow).toBeVisible({ timeout: 15_000 });
  });

  test('remove ticker via API disappears from watchlist UI', async ({ page, request }) => {
    // Ensure PYPL is added first
    await request.post(`${BASE_URL}/api/watchlist`, {
      data: { ticker: 'PYPL' },
    });

    // Navigate and confirm it's there
    await page.goto(BASE_URL);
    await expect(page.getByTestId('watchlist-row-PYPL')).toBeVisible({ timeout: 15_000 });

    // Remove via API
    const delResp = await request.delete(`${BASE_URL}/api/watchlist/PYPL`);
    expect(delResp.status()).toBe(200);

    // Reload and confirm it's gone
    await page.reload();
    // Wait for page to fully load (AAPL must be visible before checking PYPL absence)
    await expect(page.getByTestId('watchlist-row-AAPL')).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId('watchlist-row-PYPL')).not.toBeVisible();
  });

  test('watchlist API returns 10 default tickers', async ({ request }) => {
    const resp = await request.get(`${BASE_URL}/api/watchlist`);
    expect(resp.status()).toBe(200);
    const data = await resp.json();
    expect(data.watchlist).toHaveLength(10);
  });

});
