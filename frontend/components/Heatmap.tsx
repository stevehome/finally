'use client'

import type { Portfolio, PositionItem } from '@/types/market'

interface HeatmapProps {
  portfolio: Portfolio
}

function tileColor(pos: PositionItem): string {
  const intensity = Math.min(Math.abs(pos.unrealized_pnl) / (pos.value || 1), 0.4)
  const alpha = (0.15 + intensity).toFixed(2)
  return pos.unrealized_pnl >= 0
    ? `rgba(34, 197, 94, ${alpha})`
    : `rgba(239, 68, 68, ${alpha})`
}

export default function Heatmap({ portfolio }: HeatmapProps) {
  const { positions } = portfolio
  const total = positions.reduce((s, p) => s + p.value, 0) || 1

  if (positions.length === 0) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100%',
        color: '#8b949e',
        fontSize: 11,
        padding: 8,
      }}>
        No positions — buy something to see your portfolio here
      </div>
    )
  }

  return (
    <div style={{
      display: 'flex',
      flexWrap: 'wrap',
      gap: 2,
      padding: 8,
      height: '100%',
      alignContent: 'flex-start',
      overflowY: 'auto',
    }}>
      {positions.map(pos => {
        const pct = (pos.value / total) * 100
        const pnlPct = pos.avg_cost > 0
          ? ((pos.current_price - pos.avg_cost) / pos.avg_cost * 100).toFixed(1)
          : '0.0'
        const isProfit = pos.unrealized_pnl >= 0
        return (
          <div
            key={pos.ticker}
            style={{
              width: `calc(${pct}% - 2px)`,
              minWidth: 48,
              backgroundColor: tileColor(pos),
              border: '1px solid #30363d',
              borderRadius: 4,
              padding: '4px 6px',
              flexGrow: pct,
              flexShrink: 0,
            }}
          >
            <div style={{ color: '#e6edf3', fontSize: 11, fontFamily: 'monospace', fontWeight: 600 }}>
              {pos.ticker}
            </div>
            <div style={{ color: isProfit ? '#22c55e' : '#ef4444', fontSize: 10 }}>
              {isProfit ? '+' : ''}{pnlPct}%
            </div>
          </div>
        )
      })}
    </div>
  )
}
