'use client'

import type { PriceMap } from '@/types/market'
import type { SparkHistory } from '@/hooks/usePriceStream'
import type { MutableRefObject } from 'react'
import WatchlistRow from './WatchlistRow'

interface WatchlistPanelProps {
  tickers: string[]
  prices: PriceMap
  sparkHistory: MutableRefObject<SparkHistory>
  selectedTicker: string | null
  onSelectTicker: (ticker: string) => void
}

export default function WatchlistPanel({
  tickers,
  prices,
  sparkHistory,
  selectedTicker,
  onSelectTicker,
}: WatchlistPanelProps) {
  if (tickers.length === 0) {
    return (
      <div className="p-3 text-text-muted text-xs">Loading watchlist...</div>
    )
  }

  return (
    <>
      {tickers.map(ticker => (
        <WatchlistRow
          key={ticker}
          ticker={ticker}
          update={prices[ticker]}
          sparkPoints={sparkHistory.current[ticker] ?? []}
          selected={selectedTicker === ticker}
          onSelect={onSelectTicker}
        />
      ))}
    </>
  )
}
