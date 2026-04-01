'use client'

import { useState } from 'react'

export type TradeResult = {
  ticker: string
  side: string
  quantity: number
  price: number | null
  error: string | null
}

export type WatchlistResult = {
  ticker: string
  action: 'add' | 'remove'
  applied: boolean
}

export type ChatActions = {
  trades_executed: TradeResult[]
  trades_failed: TradeResult[]
  watchlist_changes: WatchlistResult[]
}

export type ChatMessage = {
  role: 'user' | 'assistant'
  content: string
  actions?: ChatActions
}

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [loading, setLoading] = useState(false)

  async function sendMessage(text: string) {
    setMessages(prev => [...prev, { role: 'user', content: text }])
    setLoading(true)
    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text }),
      })
      const data = await res.json() as { message: string; actions: ChatActions }
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.message,
        actions: data.actions,
      }])
    } catch {
      // keep loading cleared; don't crash the UI
    } finally {
      setLoading(false)
    }
  }

  return { messages, loading, sendMessage }
}
