'use client'

import { useState } from 'react'
import { usePriceStream } from '@/hooks/usePriceStream'
import { usePortfolio } from '@/hooks/usePortfolio'
import { useWatchlist } from '@/hooks/useWatchlist'
import Header from './Header'
import WatchlistPanel from './WatchlistPanel'

export default function AppShell() {
  const { prices, connected, sparkHistory } = usePriceStream()
  const portfolio = usePortfolio()
  const tickers = useWatchlist()
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null)

  return (
    <div className="grid h-screen" style={{
      gridTemplateRows: 'auto 1fr',
      gridTemplateColumns: '300px 1fr',
    }}>
      <Header portfolio={portfolio} connected={connected} />

      {/* Watchlist column */}
      <div
        className="overflow-y-auto border-r"
        style={{ borderColor: '#30363d', backgroundColor: '#0d1117' }}
      >
        <div
          className="text-xs text-text-muted uppercase tracking-wider px-3 py-2 border-b"
          style={{ borderColor: '#30363d' }}
        >
          Watchlist
        </div>
        <WatchlistPanel
          tickers={tickers}
          prices={prices}
          sparkHistory={sparkHistory}
          selectedTicker={selectedTicker}
          onSelectTicker={setSelectedTicker}
        />
      </div>

      {/* Main area — placeholder for Phase 5 */}
      <div
        className="flex items-center justify-center"
        style={{ backgroundColor: '#0d1117' }}
      >
        {selectedTicker ? (
          <p className="text-text-muted text-sm font-mono">
            {selectedTicker} — chart coming in Phase 5
          </p>
        ) : (
          <p className="text-text-muted text-xs">Select a ticker to view chart</p>
        )}
      </div>
    </div>
  )
}
