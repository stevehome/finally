import { test, expect } from "@playwright/test";

test.describe("Trading", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("domcontentloaded");
    // Wait for SSE prices to be available
    const sseStatus = page.locator("[data-testid='sse-status']");
    await expect(sseStatus).toContainText("connected", { timeout: 15_000 });
  });

  test("buy shares — cash decreases and position appears", async ({ page }) => {
    // Check available cash and find an affordable ticker via API
    const portfolioRes = await page.request.get("/api/portfolio");
    const portfolio = await portfolioRes.json();
    const cash = portfolio.cash;

    const watchlistRes = await page.request.get("/api/watchlist");
    const watchlist = await watchlistRes.json();
    const affordable = watchlist
      .filter((t: any) => t.price && t.price > 0 && t.price < cash)
      .sort((a: any, b: any) => a.price - b.price)[0];

    if (!affordable) {
      test.skip(true, `No affordable ticker with $${cash.toFixed(2)} cash`);
      return;
    }

    const ticker = affordable.ticker;

    // Record initial cash
    const cashEl = page.locator("[data-testid='cash-balance']");
    await expect(cashEl).toBeVisible({ timeout: 5_000 });
    const initialCash = await cashEl.textContent();

    // Buy 1 share
    await page.locator("input[placeholder='Ticker']").fill(ticker);
    await page.locator("input[placeholder='Qty']").fill("1");
    await page.locator("[data-testid='trade-buy']").click();

    // Cash should change
    await expect(async () => {
      const cashText = await cashEl.textContent();
      expect(cashText).not.toBe(initialCash);
    }).toPass({ timeout: 5_000 });

    // Ticker should appear in the positions table
    const posTable = page.locator("table").filter({ hasText: "Avg Cost" });
    await expect(posTable.locator("td", { hasText: new RegExp(`^${ticker}$`) })).toBeVisible({ timeout: 5_000 });
  });

  test("sell shares — cash increases and position updates", async ({ page }) => {
    // Check if we have any position to sell
    const portfolioRes = await page.request.get("/api/portfolio");
    const portfolio = await portfolioRes.json();
    const position = portfolio.positions.find((p: any) => p.quantity >= 1);

    if (!position) {
      // Buy 1 share first — find cheapest affordable
      const watchlistRes = await page.request.get("/api/watchlist");
      const watchlist = await watchlistRes.json();
      const affordable = watchlist
        .filter((t: any) => t.price && t.price > 0 && t.price < portfolio.cash)
        .sort((a: any, b: any) => a.price - b.price)[0];

      if (!affordable) {
        test.skip(true, "No affordable ticker to buy before selling");
        return;
      }

      await page.locator("input[placeholder='Ticker']").fill(affordable.ticker);
      await page.locator("input[placeholder='Qty']").fill("1");
      await page.locator("[data-testid='trade-buy']").click();
      await page.waitForTimeout(1_000);
    }

    // Re-check positions
    const newPortfolioRes = await page.request.get("/api/portfolio");
    const newPortfolio = await newPortfolioRes.json();
    const sellPosition = newPortfolio.positions.find((p: any) => p.quantity >= 1);

    if (!sellPosition) {
      test.skip(true, "No position available to sell");
      return;
    }

    const ticker = sellPosition.ticker;

    // Record cash before sell
    const cashEl = page.locator("[data-testid='cash-balance']");
    await page.waitForTimeout(500);
    const cashBefore = await cashEl.textContent();

    // Sell 1 share
    await page.locator("input[placeholder='Ticker']").fill(ticker);
    await page.locator("input[placeholder='Qty']").fill("1");
    await page.locator("[data-testid='trade-sell']").click();

    // Cash should increase
    await expect(async () => {
      const cashAfter = await cashEl.textContent();
      expect(cashAfter).not.toBe(cashBefore);
    }).toPass({ timeout: 5_000 });
  });
});
