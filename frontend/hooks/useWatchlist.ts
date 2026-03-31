'use client'

import { useState, useEffect } from 'react'
import type { WatchlistItem } from '@/types/market'

export function useWatchlist() {
  const [tickers, setTickers] = useState<string[]>([])

  useEffect(() => {
    fetch('/api/watchlist')
      .then(r => r.json())
      .then((data: { watchlist: WatchlistItem[] }) =>
        setTickers(data.watchlist.map(item => item.ticker))
      )
      .catch(() => {})
  }, [])

  return tickers
}
