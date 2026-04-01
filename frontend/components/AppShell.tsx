'use client'

import { useState } from 'react'
import { usePriceStream } from '@/hooks/usePriceStream'
import { usePortfolio } from '@/hooks/usePortfolio'
import { useWatchlist } from '@/hooks/useWatchlist'
import Header from './Header'
import WatchlistPanel from './WatchlistPanel'

export default function AppShell() {
  const { prices, connected, sparkHistory } = usePriceStream()
  const { portfolio, refetch } = usePortfolio()
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

      {/* Main area — nested grid for Phase 5 panels */}
      <div style={{
        display: 'grid',
        gridTemplateRows: '60% 40%',
        height: '100%',
        overflow: 'hidden',
        backgroundColor: '#0d1117',
      }}>
        {/* Top row: main chart (placeholder — filled in Plan 05-02) */}
        <div style={{
          backgroundColor: '#0d1117',
          borderBottom: '1px solid #30363d',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#8b949e',
          fontSize: 12,
        }}>
          {selectedTicker
            ? `${selectedTicker} — chart loading…`
            : 'Select a ticker to view chart'}
        </div>

        {/* Bottom row: portfolio panels left + chat right */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: '1fr 380px',
          overflow: 'hidden',
        }}>
          {/* Portfolio panels placeholder — filled in Plan 05-03 */}
          <div style={{
            borderRight: '1px solid #30363d',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#8b949e',
            fontSize: 12,
          }}>
            Portfolio panels coming soon
          </div>

          {/* Chat panel placeholder — filled in Plan 05-04 */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#8b949e',
            fontSize: 12,
          }}>
            Chat coming soon
          </div>
        </div>
      </div>
    </div>
  )
}
