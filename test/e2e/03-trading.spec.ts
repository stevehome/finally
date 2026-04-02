import { test, expect } from '@playwright/test';

const BASE_URL = process.env.BASE_URL || 'http://localhost:8000';

test.describe('TEST-04: Buy and sell shares via TradeBar', () => {

  test('buy shares decreases cash balance', async ({ page, request }) => {
    await page.goto(BASE_URL);

    // Wait for cash balance to load
    const cashSpan = page.getByTestId('cash-balance');
    await expect(cashSpan).toBeVisible({ timeout: 15_000 });

    // Record cash before buy
    const before = await request.get(`${BASE_URL}/api/portfolio`);
    const cashBefore = (await before.json()).cash_balance as number;

    // Fill TradeBar and buy 2 AAPL
    await page.getByTestId('trade-ticker').fill('AAPL');
    await page.getByTestId('trade-qty').fill('2');
    await page.getByTestId('buy-btn').click();

    // Wait for portfolio to update via API
    await page.waitForFunction(
      ([url, prev]: [string, number]) =>
        fetch(`${url}/api/portfolio`).then(r => r.json()).then(d => d.cash_balance < prev),
      [BASE_URL, cashBefore] as [string, number],
      { timeout: 10_000 }
    );

    // Verify via API that cash decreased
    const portfolio = await request.get(`${BASE_URL}/api/portfolio`);
    const data = await portfolio.json();
    expect(data.cash_balance).toBeLessThan(cashBefore);

    // Verify AAPL position exists
    const positions = data.positions as Array<{ ticker: string; quantity: number }>;
    expect(positions.some(p => p.ticker === 'AAPL')).toBe(true);
  });

  test('sell shares increases cash balance', async ({ page, request }) => {
    await page.goto(BASE_URL);

    // Wait for cash balance to load
    const cashSpan = page.getByTestId('cash-balance');
    await expect(cashSpan).toBeVisible({ timeout: 15_000 });

    // Record cash before buy
    const preBuy = await request.get(`${BASE_URL}/api/portfolio`);
    const cashPreBuy = (await preBuy.json()).cash_balance as number;

    // Buy 2 AAPL first
    await page.getByTestId('trade-ticker').fill('AAPL');
    await page.getByTestId('trade-qty').fill('2');
    await page.getByTestId('buy-btn').click();

    // Wait for buy to process
    await page.waitForFunction(
      ([url, prev]: [string, number]) =>
        fetch(`${url}/api/portfolio`).then(r => r.json()).then(d => d.cash_balance < prev),
      [BASE_URL, cashPreBuy] as [string, number],
      { timeout: 10_000 }
    );

    // Record cash after buy
    const afterBuy = await request.get(`${BASE_URL}/api/portfolio`);
    const buyData = await afterBuy.json();
    const cashAfterBuy = buyData.cash_balance;

    // Sell 1 AAPL
    await page.getByTestId('trade-ticker').fill('AAPL');
    await page.getByTestId('trade-qty').fill('1');
    await page.getByTestId('sell-btn').click();

    // Wait for portfolio to update
    await page.waitForFunction(
      ([url, prevCash]: [string, number]) =>
        fetch(`${url}/api/portfolio`)
          .then(r => r.json())
          .then(d => d.cash_balance > prevCash),
      [BASE_URL, cashAfterBuy] as [string, number],
      { timeout: 10_000 }
    );

    // Verify cash increased
    const afterSell = await request.get(`${BASE_URL}/api/portfolio`);
    const sellData = await afterSell.json();
    expect(sellData.cash_balance).toBeGreaterThan(cashAfterBuy);
  });

  test('invalid trade shows error message', async ({ page }) => {
    await page.goto(BASE_URL);

    // Wait for page to load
    await expect(page.getByTestId('cash-balance')).toBeVisible({ timeout: 15_000 });

    // Try to sell AAPL without owning any
    await page.getByTestId('trade-ticker').fill('AAPL');
    await page.getByTestId('trade-qty').fill('999999');
    await page.getByTestId('sell-btn').click();

    // Error message should appear
    await expect(page.getByTestId('trade-error')).toBeVisible({ timeout: 5_000 });
  });

});
