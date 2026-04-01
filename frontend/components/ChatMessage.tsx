'use client'

import type { ChatMessage as ChatMsg } from '@/hooks/useChat'

export default function ChatMessage({ msg }: { msg: ChatMsg }) {
  const isUser = msg.role === 'user'
  return (
    <div data-testid="chat-message" style={{
      marginBottom: 12,
      display: 'flex',
      flexDirection: 'column',
      alignItems: isUser ? 'flex-end' : 'flex-start',
    }}>
      <div style={{
        maxWidth: '85%',
        backgroundColor: isUser ? '#1f2937' : '#161b22',
        color: '#e6edf3',
        borderRadius: 8,
        padding: '8px 12px',
        fontSize: 12,
        lineHeight: 1.5,
        border: '1px solid #30363d',
      }}>
        {msg.content}
      </div>
      {msg.actions && (
        <div style={{ marginTop: 4, maxWidth: '85%', fontSize: 11 }}>
          {msg.actions.trades_executed.map((t, i) => (
            <div key={i} style={{ color: '#22c55e', fontFamily: 'monospace' }}>
              Executed: {t.side.toUpperCase()} {t.quantity} {t.ticker}
              {t.price != null ? ` @ $${t.price.toFixed(2)}` : ''}
            </div>
          ))}
          {msg.actions.trades_failed.map((t, i) => (
            <div key={i} style={{ color: '#ef4444', fontFamily: 'monospace' }}>
              Failed: {t.side.toUpperCase()} {t.ticker} — {t.error}
            </div>
          ))}
          {msg.actions.watchlist_changes.map((w, i) => (
            <div key={i} style={{ color: '#ecad0a', fontFamily: 'monospace' }}>
              Watchlist: {w.action === 'add' ? 'Added' : 'Removed'} {w.ticker}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
