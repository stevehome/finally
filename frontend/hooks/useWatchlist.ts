'use client'

import { useState, useEffect, useCallback } from 'react'
import type { WatchlistItem } from '@/types/market'

export function useWatchlist() {
  const [tickers, setTickers] = useState<string[]>([])

  const refetch = useCallback(() => {
    fetch('/api/watchlist')
      .then(r => r.json())
      .then((data: { watchlist: WatchlistItem[] }) =>
        setTickers(data.watchlist.map(item => item.ticker))
      )
      .catch(() => {})
  }, [])

  useEffect(() => { refetch() }, [refetch])

  return { tickers, refetch }
}
