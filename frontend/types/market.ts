/** Price update received from the SSE stream. */
export type PriceUpdate = {
  ticker: string
  price: number
  previous_price: number
  timestamp: number
  change: number
  change_percent: number
  direction: 'up' | 'down' | 'flat'
}

/** Map of ticker symbol → latest PriceUpdate. */
export type PriceMap = Record<string, PriceUpdate>

/** Single item from GET /api/watchlist. */
export type WatchlistItem = {
  ticker: string
  price: number
}

/** Portfolio snapshot from GET /api/portfolio. */
export type Portfolio = {
  cash_balance: number
  total_value: number
  positions: PositionItem[]
}

/** Single position in the portfolio. */
export type PositionItem = {
  ticker: string
  quantity: number
  avg_cost: number
  current_price: number
  unrealized_pnl: number
  value: number
}
