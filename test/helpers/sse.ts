import { Page, expect } from "@playwright/test";

export interface PriceUpdate {
  ticker: string;
  price: number;
  previous_price: number;
  timestamp: string;
  direction: "up" | "down" | "unchanged";
}

/**
 * Wait for the SSE connection to be established by checking for
 * the connection status indicator turning green or price data appearing.
 */
export async function waitForSSEConnection(
  page: Page,
  timeout = 15_000
): Promise<void> {
  // Wait for either a green connection indicator or price elements to appear
  await Promise.race([
    page
      .locator("[data-testid='connection-status'][data-connected='true']")
      .waitFor({ timeout }),
    page
      .locator("[data-testid='price']")
      .first()
      .waitFor({ timeout }),
    // Fallback: wait for any price-like content to appear in the watchlist
    page
      .locator("text=/\\$[0-9]+/")
      .first()
      .waitFor({ timeout }),
  ]);
}

/**
 * Assert that prices are updating by observing a change in displayed price text.
 */
export async function assertPriceUpdating(
  page: Page,
  ticker: string,
  timeout = 10_000
): Promise<void> {
  const tickerRow = page.locator(`[data-testid='ticker-row-${ticker}']`);
  const priceEl = tickerRow.locator("[data-testid='price']");

  // Get initial price text
  const initialPrice = await priceEl.textContent({ timeout });

  // Wait for price to change
  await expect(async () => {
    const currentPrice = await priceEl.textContent();
    expect(currentPrice).not.toBe(initialPrice);
  }).toPass({ timeout });
}

/**
 * Collect SSE price events directly via the API for a given duration.
 */
export async function collectSSEEvents(
  baseURL: string,
  durationMs = 3000
): Promise<PriceUpdate[]> {
  const events: PriceUpdate[] = [];

  return new Promise((resolve) => {
    const controller = new AbortController();

    fetch(`${baseURL}/api/stream/prices`, {
      signal: controller.signal,
      headers: { Accept: "text/event-stream" },
    })
      .then((res) => {
        const reader = res.body!.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        function read(): Promise<void> {
          return reader.read().then(({ done, value }) => {
            if (done) return;
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n");
            buffer = lines.pop() || "";

            for (const line of lines) {
              if (line.startsWith("data: ")) {
                try {
                  const data = JSON.parse(line.slice(6));
                  if (data.ticker) {
                    events.push(data as PriceUpdate);
                  }
                } catch {
                  // skip malformed lines
                }
              }
            }
            return read();
          });
        }

        read().catch(() => {});
      })
      .catch(() => {});

    setTimeout(() => {
      controller.abort();
      resolve(events);
    }, durationMs);
  });
}
