import { test, expect } from "@playwright/test";

test.describe("Watchlist management", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("domcontentloaded");
    // Wait for watchlist to load
    await expect(page.locator("[data-testid='ticker-row-AAPL']")).toBeVisible({ timeout: 10_000 });
  });

  test("add a new ticker to the watchlist", async ({ page }) => {
    // The watchlist add form has an input with placeholder "Add ticker..." and a "+" button
    const addInput = page.locator("input[placeholder='Add ticker...']");
    await addInput.fill("PYPL");

    // Click the "+" submit button
    const addButton = addInput.locator("..").locator("button[type='submit']");
    await addButton.click();

    // New ticker row should appear
    const newRow = page.locator("[data-testid='ticker-row-PYPL']");
    await expect(newRow).toBeVisible({ timeout: 10_000 });
  });

  test("remove a ticker from the watchlist", async ({ page }) => {
    // First add a ticker so we can remove it without affecting defaults
    const addInput = page.locator("input[placeholder='Add ticker...']");
    await addInput.fill("PYPL");
    const addButton = addInput.locator("..").locator("button[type='submit']");
    await addButton.click();
    await expect(page.locator("[data-testid='ticker-row-PYPL']")).toBeVisible({ timeout: 10_000 });

    // The remove button is inside the ticker row — small "x" button
    const pyplRow = page.locator("[data-testid='ticker-row-PYPL']");
    // Hover to make the remove button visible (it has opacity-0 by default)
    await pyplRow.hover();
    const removeBtn = pyplRow.locator("button", { hasText: "x" });
    await removeBtn.click({ force: true });

    // Row should disappear
    await expect(page.locator("[data-testid='ticker-row-PYPL']")).not.toBeVisible({ timeout: 5_000 });
  });
});
