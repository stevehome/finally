import { test, expect } from "@playwright/test";

test.describe("Portfolio visualizations", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("domcontentloaded");
    // Wait for SSE
    const sseStatus = page.locator("[data-testid='sse-status']");
    await expect(sseStatus).toContainText("connected", { timeout: 15_000 });
  });

  test("heatmap renders with positions", async ({ page }) => {
    // Buy some shares to ensure at least one position exists
    await page.locator("input[placeholder='Ticker']").fill("AAPL");
    await page.locator("input[placeholder='Qty']").fill("10");
    await page.locator("[data-testid='trade-buy']").click();

    // Wait for the position to be reflected
    await page.waitForTimeout(1_000);

    // An SVG element should appear inside the Portfolio Heatmap section
    const heatmapSection = page.locator("text=Portfolio Heatmap").locator("..").locator("..");
    const svg = heatmapSection.locator("svg");
    await expect(svg).toBeVisible({ timeout: 5_000 });
  });

  test("P&L chart shows data points after a trade", async ({ page }) => {
    // Buy shares to trigger a portfolio snapshot
    await page.locator("input[placeholder='Ticker']").fill("AAPL");
    await page.locator("input[placeholder='Qty']").fill("5");
    await page.locator("[data-testid='trade-buy']").click();

    // Wait for trade to process
    await page.waitForTimeout(1_000);

    // P&L section should have a Recharts LineChart SVG
    const pnlSection = page.locator("text=P&L").first().locator("..").locator("..");
    await expect(async () => {
      const waitingText = pnlSection.locator("text=Waiting for data...");
      await expect(waitingText).not.toBeVisible({ timeout: 500 });
    }).toPass({ timeout: 10_000 });

    const svg = pnlSection.locator("svg");
    await expect(svg).toBeVisible({ timeout: 5_000 });
  });

  test("positions table shows trade details", async ({ page }) => {
    // Buy a single share (small amount to avoid insufficient cash)
    await page.locator("input[placeholder='Ticker']").fill("V");
    await page.locator("input[placeholder='Qty']").fill("1");
    await page.locator("[data-testid='trade-buy']").click();

    // Positions table should show V
    const posTable = page.locator("table").filter({ hasText: "Avg Cost" });
    await expect(posTable).toBeVisible({ timeout: 5_000 });
    await expect(posTable.locator("td", { hasText: /^V$/ })).toBeVisible({ timeout: 5_000 });
  });
});
