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

  // When ticker changes: load accumulated history from sparkHistory ref
  useEffect(() => {
    const series = seriesRef.current
    const chart = chartRef.current
    if (!series || !chart || !ticker) return
    if (ticker !== prevTickerRef.current) {
      const history = sparkHistory.current[ticker] ?? []
      series.setData(
        history.map(p => ({ time: Math.floor(p.time) as UTCTimestamp, value: p.value }))
      )
      chart.timeScale().fitContent()
      prevTickerRef.current = ticker
    }
  }, [ticker, sparkHistory])

  // Append new live price point on each SSE tick
  useEffect(() => {
    const series = seriesRef.current
    if (!series || !ticker) return
    const update = prices[ticker]
    if (!update) return
    series.update({ time: Math.floor(update.timestamp) as UTCTimestamp, value: update.price })
  }, [prices, ticker])

  return (
    <div style={{ backgroundColor: '#0d1117', borderBottom: '1px solid #30363d', height: '100%' }}>
      {ticker ? (
        <>
          <div style={{
            padding: '6px 12px',
            color: '#e6edf3',
            fontSize: 12,
            fontFamily: 'monospace',
            height: 28,
            lineHeight: '16px',
          }}>
            {ticker}
          </div>
          <div ref={containerRef} style={{ height: 'calc(100% - 28px)' }} />
        </>
      ) : (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100%',
          color: '#8b949e',
          fontSize: 12,
        }}>
          Select a ticker to view chart
        </div>
      )}
    </div>
  )
}
