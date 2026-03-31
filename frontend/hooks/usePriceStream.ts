'use client'

import { useState, useEffect, useRef } from 'react'
import type { PriceMap, PriceUpdate } from '@/types/market'

/** Price history buffer — keyed by ticker, ordered array of {time, value} for sparklines. */
export type SparkPoint = { time: number; value: number }
export type SparkHistory = Record<string, SparkPoint[]>

export function usePriceStream() {
  const [prices, setPrices] = useState<PriceMap>({})
  const [connected, setConnected] = useState(false)
  const sparkRef = useRef<SparkHistory>({})

  useEffect(() => {
    const es = new EventSource('/api/stream/prices')

    es.onopen = () => setConnected(true)
    es.onerror = () => setConnected(false)

    es.onmessage = (event: MessageEvent) => {
      const data = JSON.parse(event.data) as PriceMap
      setPrices(prev => ({ ...prev, ...data }))

      // Accumulate sparkline history (kept in ref to avoid re-renders)
      for (const update of Object.values(data) as PriceUpdate[]) {
        const points = sparkRef.current[update.ticker] ?? []
        points.push({ time: Math.floor(update.timestamp), value: update.price })
        // Cap history at 120 points (~60 seconds at 500ms cadence)
        if (points.length > 120) points.shift()
        sparkRef.current[update.ticker] = points
      }
    }

    return () => {
      es.close()
    }
  }, [])

  return { prices, connected, sparkHistory: sparkRef }
}
