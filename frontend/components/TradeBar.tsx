'use client'

import { useState } from 'react'

interface TradeBarProps {
  refetch: () => void
}

const inputStyle: React.CSSProperties = {
  backgroundColor: '#161b22',
  border: '1px solid #30363d',
  borderRadius: 4,
  color: '#e6edf3',
  fontSize: 12,
  padding: '4px 8px',
  fontFamily: 'monospace',
  outline: 'none',
}

const btnStyle = (color: string, disabled: boolean): React.CSSProperties => ({
  backgroundColor: disabled ? '#21262d' : color,
  color: disabled ? '#8b949e' : '#fff',
  border: 'none',
  borderRadius: 4,
  padding: '4px 12px',
  fontSize: 12,
  fontFamily: 'monospace',
  cursor: disabled ? 'not-allowed' : 'pointer',
  fontWeight: 600,
})

export default function TradeBar({ refetch }: TradeBarProps) {
  const [ticker, setTicker] = useState('')
  const [quantity, setQuantity] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const canSubmit = ticker.trim().length > 0 && quantity.trim().length > 0 && !submitting

  async function handleTrade(side: 'buy' | 'sell') {
    if (!canSubmit) return
    setSubmitting(true)
    setError(null)
    try {
      const res = await fetch('/api/portfolio/trade', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ticker: ticker.trim().toUpperCase(),
          quantity: parseFloat(quantity),
          side,
        }),
      })
      if (!res.ok) {
        const err = await res.json() as { detail: string }
        setError(err.detail ?? 'Trade failed')
      } else {
        setTicker('')
        setQuantity('')
        setError(null)
        refetch()
      }
    } catch {
      setError('Network error')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: 8,
      padding: '6px 8px',
      borderBottom: '1px solid #30363d',
      backgroundColor: '#0d1117',
      flexShrink: 0,
    }}>
      <span style={{ color: '#8b949e', fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
        Trade
      </span>
      <input
        type="text"
        value={ticker}
        onChange={e => setTicker(e.target.value.toUpperCase())}
        placeholder="TICKER"
        maxLength={5}
        data-testid="trade-ticker"
        style={{ ...inputStyle, width: 72 }}
      />
      <input
        type="number"
        value={quantity}
        onChange={e => setQuantity(e.target.value)}
        placeholder="Qty"
        min="0"
        step="any"
        data-testid="trade-qty"
        style={{ ...inputStyle, width: 72 }}
      />
      <button
        onClick={() => handleTrade('buy')}
        disabled={!canSubmit}
        data-testid="buy-btn"
        style={btnStyle('#22c55e', !canSubmit)}
      >
        Buy
      </button>
      <button
        onClick={() => handleTrade('sell')}
        disabled={!canSubmit}
        data-testid="sell-btn"
        style={btnStyle('#ef4444', !canSubmit)}
      >
        Sell
      </button>
      {error && (
        <span data-testid="trade-error" style={{ color: '#ef4444', fontSize: 11, fontFamily: 'monospace' }}>
          {error}
        </span>
      )}
    </div>
  )
}
