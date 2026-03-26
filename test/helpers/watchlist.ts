import { Page, expect } from "@playwright/test";

const DEFAULT_TICKERS = [
  "AAPL", "GOOGL", "MSFT", "AMZN", "TSLA",
  "NVDA", "META", "JPM", "V", "NFLX",
];

/**
 * Assert that all default tickers are visible in the watchlist.
 */
export async function assertDefaultWatchlist(page: Page): Promise<void> {
  for (const ticker of DEFAULT_TICKERS) {
    const row = page.locator(`[data-testid='ticker-row-${ticker}']`);
    await expect(row).toBeVisible({ timeout: 10_000 });
  }
}

/**
 * Add a ticker to the watchlist via UI.
 */
export async function addTicker(page: Page, ticker: string): Promise<void> {
  const input = page.locator("[data-testid='watchlist-add-input']");
  await input.fill(ticker);
  await page.locator("[data-testid='watchlist-add-button']").click();

  // Wait for the new ticker row to appear
  const row = page.locator(`[data-testid='ticker-row-${ticker}']`);
  await expect(row).toBeVisible({ timeout: 5000 });
}

/**
 * Remove a ticker from the watchlist via UI.
 */
export async function removeTicker(page: Page, ticker: string): Promise<void> {
  const removeBtn = page.locator(
    `[data-testid='ticker-row-${ticker}'] [data-testid='remove-ticker']`
  );
  await removeBtn.click();

  // Wait for the row to disappear
  const row = page.locator(`[data-testid='ticker-row-${ticker}']`);
  await expect(row).not.toBeVisible({ timeout: 5000 });
}

export { DEFAULT_TICKERS };
