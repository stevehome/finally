'use client'

import { useState, useRef, useEffect } from 'react'
import { useChat } from '@/hooks/useChat'
import ChatMessage from './ChatMessage'

interface ChatPanelProps {
  onPortfolioChange?: () => void
  onWatchlistChange?: () => void
}

export default function ChatPanel({ onPortfolioChange, onWatchlistChange }: ChatPanelProps) {
  const { messages, loading, sendMessage } = useChat({ onPortfolioChange, onWatchlistChange })
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  function handleSend() {
    const text = input.trim()
    if (!text || loading) return
    setInput('')
    sendMessage(text)
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      backgroundColor: '#0d1117',
      borderLeft: '1px solid #30363d',
    }}>
      {/* Header */}
      <div style={{
        padding: '4px 8px',
        fontSize: 10,
        color: '#8b949e',
        textTransform: 'uppercase',
        letterSpacing: '0.05em',
        borderBottom: '1px solid #21262d',
        flexShrink: 0,
      }}>
        AI Assistant
      </div>

      {/* Message history */}
      <div data-testid="chat-messages" style={{
        flex: 1,
        overflowY: 'auto',
        padding: '8px 12px',
      }}>
        {messages.length === 0 && !loading && (
          <div style={{ color: '#8b949e', fontSize: 11, textAlign: 'center', marginTop: 24 }}>
            Ask me about your portfolio or tell me to make a trade.
          </div>
        )}
        {messages.map((msg, i) => (
          <ChatMessage key={i} msg={msg} />
        ))}
        {loading && (
          <div style={{
            display: 'flex',
            alignItems: 'flex-start',
            marginBottom: 12,
          }}>
            <div style={{
              backgroundColor: '#161b22',
              border: '1px solid #30363d',
              borderRadius: 8,
              padding: '8px 12px',
              fontSize: 14,
              color: '#8b949e',
            }}>
              <span className="loading-dots">
                <span>.</span>
                <span>.</span>
                <span>.</span>
              </span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input bar */}
      <div style={{
        borderTop: '1px solid #30363d',
        padding: '8px',
        flexShrink: 0,
      }}>
        <div style={{ display: 'flex', gap: 6 }}>
          <textarea
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={loading}
            placeholder="Ask about portfolio or trade…"
            rows={2}
            style={{
              flex: 1,
              backgroundColor: '#161b22',
              border: '1px solid #30363d',
              borderRadius: 6,
              color: '#e6edf3',
              fontSize: 12,
              padding: '6px 8px',
              resize: 'none',
              fontFamily: 'inherit',
              outline: 'none',
              opacity: loading ? 0.5 : 1,
            }}
          />
          <button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            style={{
              backgroundColor: '#753991',
              color: '#fff',
              border: 'none',
              borderRadius: 6,
              padding: '0 12px',
              fontSize: 12,
              cursor: loading || !input.trim() ? 'not-allowed' : 'pointer',
              opacity: loading || !input.trim() ? 0.5 : 1,
              flexShrink: 0,
            }}
          >
            Send
          </button>
        </div>
      </div>
    </div>
  )
}
