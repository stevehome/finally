import { test, expect } from "@playwright/test";

test.describe("AI Chat (mock mode)", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("domcontentloaded");
    // Wait for SSE
    const sseStatus = page.locator("[data-testid='sse-status']");
    await expect(sseStatus).toContainText("connected", { timeout: 15_000 });
  });

  test("send a message and receive a response", async ({ page }) => {
    const chatInput = page.locator("[data-testid='chat-input']");
    await chatInput.fill("Hello, what can you do?");
    await chatInput.press("Enter");

    // Should see user message in chat
    const chatMessages = page.locator("[data-testid='chat-messages']");
    await expect(chatMessages).toContainText("Hello, what can you do?", { timeout: 5_000 });

    // Should receive assistant response (mock returns the generic help message)
    await expect(chatMessages).toContainText("AI trading assistant", { timeout: 15_000 });
  });

  test("chat can execute a trade via LLM", async ({ page }) => {
    // Record initial cash
    const cashEl = page.locator("[data-testid='cash-balance']");
    const initialCash = await cashEl.textContent();

    // Ask the AI to buy shares (mock mode will parse "buy 5 AAPL")
    const chatInput = page.locator("[data-testid='chat-input']");
    await chatInput.fill("buy 1 AAPL");
    await chatInput.press("Enter");

    // Wait for assistant response
    const chatMessages = page.locator("[data-testid='chat-messages']");
    await expect(chatMessages).toContainText("Executing buy order", { timeout: 15_000 });

    // Trade execution should be shown inline
    await expect(chatMessages).toContainText("Executed", { timeout: 5_000 });
    await expect(chatMessages).toContainText("BUY", { timeout: 5_000 });
    await expect(chatMessages).toContainText("AAPL", { timeout: 5_000 });

    // Cash should have changed
    await expect(async () => {
      const cashText = await cashEl.textContent();
      expect(cashText).not.toBe(initialCash);
    }).toPass({ timeout: 5_000 });
  });

  test("chat can add ticker to watchlist via LLM", async ({ page }) => {
    const chatInput = page.locator("[data-testid='chat-input']");
    await chatInput.fill("add PYPL to watchlist");
    await chatInput.press("Enter");

    // Wait for assistant response about adding to watchlist
    const chatMessages = page.locator("[data-testid='chat-messages']");
    await expect(chatMessages).toContainText("Adding", { timeout: 15_000 });
    await expect(chatMessages).toContainText("PYPL", { timeout: 5_000 });

    // PYPL should now appear in the watchlist
    await expect(page.locator("[data-testid='ticker-row-PYPL']")).toBeVisible({ timeout: 10_000 });
  });
});
