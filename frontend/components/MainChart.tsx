'use client'

import { useEffect, useRef } from 'react'
import { createChart, LineSeries, ColorType, CrosshairMode } from 'lightweight-charts'
import type { IChartApi, ISeriesApi, UTCTimestamp } from 'lightweight-charts'
import type { MutableRefObject } from 'react'
import type { SparkHistory } from '@/hooks/usePriceStream'
import type { PriceMap } from '@/types/market'

interface MainChartProps {
  ticker: string | null
  sparkHistory: MutableRefObject<SparkHistory>
  prices: PriceMap
}

export default function MainChart({ ticker, sparkHistory, prices }: MainChartProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const seriesRef = useRef<ISeriesApi<'Line'> | null>(null)
  const prevTickerRef = useRef<string | null>(null)

  // Create chart once on mount
  useEffect(() => {
    if (!containerRef.current) return
    const chart = createChart(containerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: '#0d1117' },
        textColor: '#8b949e',
      },
      grid: {
        vertLines: { color: '#21262d' },
        horzLines: { color: '#21262d' },
      },
      crosshair: { mode: CrosshairMode.Normal },
      rightPriceScale: { borderColor: '#30363d' },
      timeScale: { borderColor: '#30363d', timeVisible: true },
      autoSize: true,
    })
    const series = chart.addSeries(LineSeries, {
      color: '#209dd7',
      lineWidth: 2,
      priceLineVisible: false,
      lastValueVisible: true,
    })
    chartRef.current = chart
    seriesRef.current = series
    return () => {
      chart.remove()
      chartRef.current = null
      seriesRef.current = null
    }
  }, [])

  // When ticker changes: load deduplicated history from sparkHistory ref
  useEffect(() => {
    const series = seriesRef.current
    const chart = chartRef.current
    if (!series || !chart || !ticker) return
    if (ticker !== prevTickerRef.current) {
      const raw = sparkHistory.current[ticker] ?? []
      // Deduplicate by time (keep last value per second) and ensure strict ascending order
      const seen = new Map<number, number>()
      for (const p of raw) seen.set(Math.floor(p.time), p.value)
      const deduped = Array.from(seen.entries())
        .sort((a, b) => a[0] - b[0])
        .map(([time, value]) => ({ time: time as UTCTimestamp, value }))
      series.setData(deduped)
      if (deduped.length > 0) chart.timeScale().fitContent()
      prevTickerRef.current = ticker
    }
  }, [ticker, sparkHistory])

  // Append new live price point on each SSE tick
  useEffect(() => {
    const series = seriesRef.current
    if (!series || !ticker) return
    const update = prices[ticker]
    if (!update) return
    const t = Math.floor(update.timestamp) as UTCTimestamp
    try {
      series.update({ time: t, value: update.price })
    } catch {
      // lightweight-charts throws if time is not >= last point; silently skip
    }
  }, [prices, ticker])

  return (
    <div style={{ backgroundColor: '#0d1117', borderBottom: '1px solid #30363d', height: '100%', position: 'relative' }}>
      {/* Placeholder — shown only when no ticker selected */}
      {!ticker && (
        <div style={{
          position: 'absolute', inset: 0,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: '#8b949e', fontSize: 12,
        }}>
          Select a ticker to view chart
        </div>
      )}
      {/* Ticker label */}
      <div style={{
        padding: '6px 12px',
        color: '#e6edf3',
        fontSize: 12,
        fontFamily: 'monospace',
        height: 28,
        lineHeight: '16px',
        visibility: ticker ? 'visible' : 'hidden',
      }}>
        {ticker ?? ''}
      </div>
      {/* Chart container — always mounted so createChart runs on mount */}
      <div ref={containerRef} style={{ height: 'calc(100% - 28px)' }} />
    </div>
  )
}
