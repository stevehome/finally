import { test, expect } from "@playwright/test";

test.describe("SSE resilience", () => {
  test("reconnects after SSE connection is interrupted", async ({ page }) => {
    // Block SSE from the start so we can control the connection
    await page.route("**/api/stream/prices", (route) => route.abort());

    await page.goto("/");
    await page.waitForLoadState("domcontentloaded");

    // Status should show disconnected or reconnecting since SSE is blocked
    const sseStatus = page.locator("[data-testid='sse-status']");
    await expect(async () => {
      const text = await sseStatus.textContent();
      expect(text?.toLowerCase()).toMatch(/disconnected|reconnecting/);
    }).toPass({ timeout: 10_000 });

    // Unblock SSE to allow connection
    await page.unrouteAll({ behavior: "ignoreErrors" });

    // Should eventually reconnect
    await expect(sseStatus).toContainText("connected", { timeout: 30_000 });
  });
});
