import { Page, expect } from "@playwright/test";

/**
 * Get the displayed cash balance from the page.
 */
export async function getCashBalance(page: Page): Promise<string> {
  const balanceEl = page.locator("[data-testid='cash-balance']");
  return (await balanceEl.textContent()) || "";
}

/**
 * Execute a trade via the trade bar UI.
 */
export async function executeTrade(
  page: Page,
  ticker: string,
  quantity: number,
  side: "buy" | "sell"
): Promise<void> {
  await page.locator("[data-testid='trade-ticker']").fill(ticker);
  await page.locator("[data-testid='trade-quantity']").fill(String(quantity));
  await page.locator(`[data-testid='trade-${side}']`).click();

  // Wait for the trade to process (position or balance should update)
  await page.waitForTimeout(1000);
}

/**
 * Assert that a position exists in the positions table.
 */
export async function assertPositionExists(
  page: Page,
  ticker: string
): Promise<void> {
  const positionRow = page.locator(`[data-testid='position-row-${ticker}']`);
  await expect(positionRow).toBeVisible({ timeout: 5000 });
}

/**
 * Assert that a position does not exist in the positions table.
 */
export async function assertPositionNotExists(
  page: Page,
  ticker: string
): Promise<void> {
  const positionRow = page.locator(`[data-testid='position-row-${ticker}']`);
  await expect(positionRow).not.toBeVisible({ timeout: 5000 });
}
