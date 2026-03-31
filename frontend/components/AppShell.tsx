'use client'

import { useState } from 'react'
import { usePriceStream } from '@/hooks/usePriceStream'
import { usePortfolio } from '@/hooks/usePortfolio'
import { useWatchlist } from '@/hooks/useWatchlist'
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
      {/* Header */}
      <div
        className="col-span-2 flex items-center justify-between px-4 py-2 border-b"
        style={{ borderColor: '#30363d', backgroundColor: '#161b22' }}
      >
        <span className="text-accent font-bold tracking-widest text-sm">FINALLY</span>
        <div className="flex items-center gap-6 text-sm">
          <span className="text-text-muted">
            Total:{' '}
            <span className="text-text-primary font-mono">
              {portfolio
                ? `$${portfolio.total_value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
                : '—'}
            </span>
          </span>
          <span className="text-text-muted">
            Cash:{' '}
            <span className="text-text-primary font-mono">
              {portfolio
                ? `$${portfolio.cash_balance.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
                : '—'}
            </span>
          </span>
          <span className="flex items-center gap-1.5 text-text-muted">
            <span
              className="inline-block w-2 h-2 rounded-full"
              style={{ backgroundColor: connected ? '#22c55e' : '#ef4444' }}
            />
            {connected ? 'Live' : 'Disconnected'}
          </span>
        </div>
      </div>

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

      {/* Main area */}
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
