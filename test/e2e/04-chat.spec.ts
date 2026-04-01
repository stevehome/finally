import { test, expect } from '@playwright/test';

const BASE_URL = process.env.BASE_URL || 'http://localhost:8000';

test.describe('TEST-05: AI chat with mocked LLM response', () => {

  test('sending a message shows assistant response', async ({ page }) => {
    await page.goto(BASE_URL);

    // Wait for the chat panel to be visible
    await expect(page.getByText('AI Assistant')).toBeVisible({ timeout: 15_000 });

    // Send a message
    await page.getByPlaceholder('Ask about portfolio or trade…').fill('Hello');
    await page.getByRole('button', { name: 'Send' }).click();

    // Wait for assistant message to appear in chat-messages
    const chatMessages = page.getByTestId('chat-messages');
    await expect(
      chatMessages.getByTestId('chat-message').filter({ hasText: 'FinAlly here' })
    ).toBeVisible({ timeout: 15_000 });
  });

  test('mock response shows inline trade confirmation', async ({ page }) => {
    await page.goto(BASE_URL);

    // Wait for page to be ready
    await expect(page.getByTestId('cash-balance')).toBeVisible({ timeout: 15_000 });

    // Send any message — mock always returns AAPL buy
    await page.getByPlaceholder('Ask about portfolio or trade…').fill('What should I buy?');
    await page.getByRole('button', { name: 'Send' }).click();

    // Wait for assistant message
    const chatMessages = page.getByTestId('chat-messages');
    await expect(
      chatMessages.getByTestId('chat-message').filter({ hasText: 'FinAlly here' })
    ).toBeVisible({ timeout: 15_000 });

    // Verify inline trade confirmation appears (green "Executed: BUY..." line)
    // ChatMessage renders: "Executed: BUY {quantity} {ticker} @ ${price}"
    await expect(
      chatMessages.getByText(/Executed: BUY/i)
    ).toBeVisible({ timeout: 5_000 });
  });

  test('user message appears in chat history', async ({ page }) => {
    await page.goto(BASE_URL);
    await expect(page.getByText('AI Assistant')).toBeVisible({ timeout: 15_000 });

    const userMsg = 'Tell me about my portfolio please';
    await page.getByPlaceholder('Ask about portfolio or trade…').fill(userMsg);
    await page.getByRole('button', { name: 'Send' }).click();

    // User message should be visible in chat
    const chatMessages = page.getByTestId('chat-messages');
    await expect(
      chatMessages.getByTestId('chat-message').filter({ hasText: userMsg })
    ).toBeVisible({ timeout: 5_000 });
  });

  test('mock trade from chat updates portfolio', async ({ page, request }) => {
    await page.goto(BASE_URL);

    // Verify initial cash is $10,000
    await expect(page.getByTestId('cash-balance')).toHaveText('$10,000.00', { timeout: 15_000 });

    // Send message — mock auto-buys 1 AAPL
    await page.getByPlaceholder('Ask about portfolio or trade…').fill('Do a trade');
    await page.getByRole('button', { name: 'Send' }).click();

    // Wait for assistant response (trade executed inline)
    await expect(
      page.getByTestId('chat-messages').getByText(/Executed: BUY/i)
    ).toBeVisible({ timeout: 15_000 });

    // Verify portfolio API reflects the trade
    const portfolio = await request.get(`${BASE_URL}/api/portfolio`);
    const data = await portfolio.json();
    expect(data.cash_balance).toBeLessThan(10000.0);
    const positions = data.positions as Array<{ ticker: string }>;
    expect(positions.some(p => p.ticker === 'AAPL')).toBe(true);
  });

});
