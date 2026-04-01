'use client'

import type { Portfolio } from '@/types/market'

const fmt2 = (n: number) => n.toFixed(2)
const fmtPct = (n: number) => `${n >= 0 ? '+' : ''}${n.toFixed(1)}%`
const pnlColor = (n: number) => n >= 0 ? '#22c55e' : '#ef4444'

const thStyle: React.CSSProperties = {
  padding: '4px 8px',
  textAlign: 'right',
  color: '#8b949e',
  fontSize: 10,
  fontWeight: 500,
  borderBottom: '1px solid #30363d',
  whiteSpace: 'nowrap',
}

const tdStyle: React.CSSProperties = {
  padding: '4px 8px',
  textAlign: 'right',
  fontSize: 11,
  fontFamily: 'monospace',
  borderBottom: '1px solid #21262d',
}

export default function PositionsTable({ portfolio }: { portfolio: Portfolio }) {
  const { positions } = portfolio

  return (
    <div style={{ overflowY: 'auto', height: '100%' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr>
            <th style={{ ...thStyle, textAlign: 'left' }}>Ticker</th>
            <th style={thStyle}>Qty</th>
            <th style={thStyle}>Avg Cost</th>
            <th style={thStyle}>Price</th>
            <th style={thStyle}>Unr. P&amp;L</th>
            <th style={thStyle}>Change %</th>
          </tr>
        </thead>
        <tbody>
          {positions.length === 0 ? (
            <tr>
              <td colSpan={6} style={{ ...tdStyle, textAlign: 'center', color: '#8b949e' }}>
                No positions
              </td>
            </tr>
          ) : positions.map(pos => {
            const pnlPct = pos.avg_cost > 0
              ? (pos.current_price - pos.avg_cost) / pos.avg_cost * 100
              : 0
            return (
              <tr key={pos.ticker}>
                <td style={{ ...tdStyle, textAlign: 'left', color: '#e6edf3', fontWeight: 600 }}>
                  {pos.ticker}
                </td>
                <td style={{ ...tdStyle, color: '#e6edf3' }}>{fmt2(pos.quantity)}</td>
                <td style={{ ...tdStyle, color: '#8b949e' }}>${fmt2(pos.avg_cost)}</td>
                <td style={{ ...tdStyle, color: '#e6edf3' }}>${fmt2(pos.current_price)}</td>
                <td style={{ ...tdStyle, color: pnlColor(pos.unrealized_pnl) }}>
                  {pos.unrealized_pnl >= 0 ? '+' : ''}${fmt2(pos.unrealized_pnl)}
                </td>
                <td style={{ ...tdStyle, color: pnlColor(pnlPct) }}>
                  {fmtPct(pnlPct)}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
