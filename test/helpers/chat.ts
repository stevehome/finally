import { Page, expect } from "@playwright/test";

/**
 * Send a message in the AI chat panel and wait for a response.
 */
export async function sendChatMessage(
  page: Page,
  message: string,
  responseTimeout = 15_000
): Promise<string> {
  const input = page.locator("[data-testid='chat-input']");
  await input.fill(message);
  await input.press("Enter");

  // Wait for assistant response to appear
  const lastAssistantMsg = page.locator(
    "[data-testid='chat-message-assistant']"
  ).last();
  await expect(lastAssistantMsg).toBeVisible({ timeout: responseTimeout });

  return (await lastAssistantMsg.textContent()) || "";
}

/**
 * Assert that a trade action confirmation is shown in the chat.
 */
export async function assertTradeActionInChat(
  page: Page,
  ticker: string
): Promise<void> {
  const chatPanel = page.locator("[data-testid='chat-panel']");
  await expect(chatPanel).toContainText(ticker, { timeout: 5000 });
}
