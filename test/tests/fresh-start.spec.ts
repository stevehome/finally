import { test, expect } from "@playwright/test";

const DEFAULT_TICKERS = [
  "AAPL", "GOOGL", "MSFT", "AMZN", "TSLA",
  "NVDA", "META", "JPM", "V", "NFLX",
];

test.describe("Fresh start", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("domcontentloaded");
  });

  test("displays the FinAlly header", async ({ page }) => {
    await expect(page.locator("text=FinAlly")).toBeVisible();
  });

  test("shows a cash balance in the header", async ({ page }) => {
    const cashEl = page.locator("[data-testid='cash-balance']");
    await expect(cashEl).toBeVisible({ timeout: 10_000 });
    const text = await cashEl.textContent();
    // Cash balance should be a formatted dollar amount
    expect(text).toMatch(/\$[\d,]+\.\d{2}/);
  });

  test("displays all 10 default watchlist tickers", async ({ page }) => {
    for (const ticker of DEFAULT_TICKERS) {
      const row = page.locator(`[data-testid='ticker-row-${ticker}']`);
      await expect(row).toBeVisible({ timeout: 10_000 });
    }
  });

  test("SSE connection is established (prices streaming)", async ({ page }) => {
    const sseStatus = page.locator("[data-testid='sse-status']");
    await expect(sseStatus).toContainText("connected", { timeout: 15_000 });
  });

  test("prices update over time", async ({ page }) => {
    const sseStatus = page.locator("[data-testid='sse-status']");
    await expect(sseStatus).toContainText("connected", { timeout: 15_000 });

    const firstRow = page.locator("[data-testid='ticker-row-AAPL']");
    await expect(firstRow).toBeVisible();

    const priceCell = firstRow.locator("td").nth(2);
    const initialPrice = await priceCell.textContent();

    await expect(async () => {
      const currentPrice = await priceCell.textContent();
      expect(currentPrice).not.toBe(initialPrice);
    }).toPass({ timeout: 5_000 });
  });

  test("portfolio value is displayed in header", async ({ page }) => {
    const header = page.locator("header");
    await expect(header).toContainText("Portfolio Value", { timeout: 5_000 });
    // Should show some dollar amount
    await expect(header).toContainText("$", { timeout: 5_000 });
  });

  test("chat panel is visible and ready", async ({ page }) => {
    const chatInput = page.locator("[data-testid='chat-input']");
    await expect(chatInput).toBeVisible({ timeout: 5_000 });
  });
});
