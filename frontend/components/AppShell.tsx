'use client'

import { useState } from 'react'
import { usePriceStream } from '@/hooks/usePriceStream'
import { usePortfolio } from '@/hooks/usePortfolio'
import { useWatchlist } from '@/hooks/useWatchlist'

export default function AppShell() {
  const { prices, connected, sparkHistory } = usePriceStream()
  const portfolio = usePortfolio()
  const tickers = useWatchlist()
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null)

  // sparkHistory passed as prop for WatchlistRow in plan 04-03
  void sparkHistory

  return (
    <div className="grid h-screen" style={{
      gridTemplateRows: 'auto 1fr',
      gridTemplateColumns: '300px 1fr',
    }}>
      {/* Header — spans both columns */}
      <div
        className="col-span-2 flex items-center justify-between px-4 py-2 border-b"
        style={{ borderColor: '#30363d', backgroundColor: '#161b22' }}
      >
        <span className="text-accent font-bold tracking-widest text-sm">FINALLY</span>
        <div className="flex items-center gap-6 text-sm">
          <span className="text-text-muted">
            Total:{' '}
            <span className="text-text-primary font-mono">
              {portfolio ? `$${portfolio.total_value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '—'}
            </span>
          </span>
          <span className="text-text-muted">
            Cash:{' '}
            <span className="text-text-primary font-mono">
              {portfolio ? `$${portfolio.cash_balance.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '—'}
            </span>
          </span>
          {/* Connection status dot */}
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
        <div className="p-2 text-xs text-text-muted uppercase tracking-wider border-b px-3 py-2"
          style={{ borderColor: '#30363d' }}>
          Watchlist
        </div>
        {tickers.length === 0 ? (
          <div className="p-3 text-text-muted text-xs">Loading...</div>
        ) : (
          tickers.map(ticker => (
            <div
              key={ticker}
              onClick={() => setSelectedTicker(ticker)}
              className="px-3 py-2 cursor-pointer text-sm border-b"
              style={{
                borderColor: '#30363d',
                backgroundColor: selectedTicker === ticker ? '#1a1a2e' : 'transparent',
              }}
            >
              <span className="text-text-primary font-mono font-semibold">{ticker}</span>
              {prices[ticker] && (
                <span className="ml-2 text-text-muted font-mono text-xs">
                  ${prices[ticker].price.toFixed(2)}
                </span>
              )}
            </div>
          ))
        )}
      </div>

      {/* Main area — placeholder for Phase 5 chart */}
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
