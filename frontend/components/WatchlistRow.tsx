'use client'

import { useState, useEffect, useRef } from 'react'
import type { PriceUpdate } from '@/types/market'
import type { SparkPoint } from '@/hooks/usePriceStream'
import Sparkline from './Sparkline'

interface WatchlistRowProps {
  ticker: string
  update: PriceUpdate | undefined
  sparkPoints: SparkPoint[]
  selected: boolean
  onSelect: (ticker: string) => void
}

export default function WatchlistRow({
  ticker,
  update,
  sparkPoints,
  selected,
  onSelect,
}: WatchlistRowProps) {
  const [flashClass, setFlashClass] = useState('')
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Trigger flash animation on each price update
  useEffect(() => {
    if (!update || update.direction === 'flat') return

    // Clear any pending timer from previous tick before setting new one
    if (timerRef.current) clearTimeout(timerRef.current)

    const cls = update.direction === 'up' ? 'flash-up' : 'flash-down'
    setFlashClass(cls)
    timerRef.current = setTimeout(() => setFlashClass(''), 500)

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current)
    }
  }, [update?.price, update?.direction]) // re-run on every price change

  const priceColor = update
    ? update.direction === 'up'
      ? '#22c55e'
      : update.direction === 'down'
      ? '#ef4444'
      : '#e6edf3'
    : '#8b949e'

  const changeText = update
    ? `${update.change_percent >= 0 ? '+' : ''}${update.change_percent.toFixed(3)}%`
    : '—'

  return (
    <div
      onClick={() => onSelect(ticker)}
      data-testid={`watchlist-row-${ticker}`}
      className={`flex items-center justify-between px-3 py-2 cursor-pointer border-b text-xs ${flashClass}`}
      style={{
        borderColor: '#30363d',
        backgroundColor: selected ? '#1a1a2e' : 'transparent',
        borderLeft: selected ? '2px solid #ecad0a' : '2px solid transparent',
      }}
    >
      {/* Ticker + price column */}
      <div className="flex flex-col min-w-0 flex-1">
        <span className="font-mono font-semibold text-text-primary">{ticker}</span>
        <span className="font-mono" style={{ color: priceColor }}>
          {update ? `$${update.price.toFixed(2)}` : '—'}
        </span>
      </div>

      {/* Change % column */}
      <div className="flex flex-col items-end mx-2">
        <span className="text-text-muted text-xs">chg%</span>
        <span className="font-mono text-xs" style={{ color: priceColor }}>
          {changeText}
        </span>
      </div>

      {/* Sparkline */}
      <Sparkline
        points={sparkPoints}
        color={update?.direction === 'down' ? '#ef4444' : '#209dd7'}
      />
    </div>
  )
}
