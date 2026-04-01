'use client'

import type { Portfolio } from '@/types/market'

interface HeaderProps {
  portfolio: Portfolio | null
  connected: boolean
}

function fmt(value: number): string {
  return value.toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

export default function Header({ portfolio, connected }: HeaderProps) {
  return (
    <div
      className="col-span-2 flex items-center justify-between px-4 py-2 border-b"
      style={{ borderColor: '#30363d', backgroundColor: '#161b22' }}
    >
      {/* Logo */}
      <div className="flex items-center gap-3">
        <span className="text-accent font-bold tracking-widest text-sm font-mono">
          FINALLY
        </span>
        <span className="text-text-muted text-xs hidden sm:block">
          AI Trading Workstation
        </span>
      </div>

      {/* Portfolio values + connection status */}
      <div className="flex items-center gap-6 text-sm">
        <div className="flex flex-col items-end">
          <span className="text-text-muted text-xs leading-none">Portfolio</span>
          <span className="text-text-primary font-mono font-semibold" data-testid="portfolio-value">
            {portfolio ? `$${fmt(portfolio.total_value)}` : '—'}
          </span>
        </div>

        <div className="flex flex-col items-end">
          <span className="text-text-muted text-xs leading-none">Cash</span>
          <span className="text-text-primary font-mono" data-testid="cash-balance">
            {portfolio ? `$${fmt(portfolio.cash_balance)}` : '—'}
          </span>
        </div>

        {/* Connection status dot with label */}
        <div className="flex items-center gap-1.5">
          <span
            className="inline-block w-2 h-2 rounded-full transition-colors duration-300"
            style={{ backgroundColor: connected ? '#22c55e' : '#ef4444' }}
            title={connected ? 'Connected to live stream' : 'Disconnected — reconnecting...'}
          />
          <span
            className="text-xs font-mono"
            style={{ color: connected ? '#22c55e' : '#ef4444' }}
          >
            {connected ? 'LIVE' : 'DISC'}
          </span>
        </div>
      </div>
    </div>
  )
}
