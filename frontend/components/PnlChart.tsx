'use client'

import { useEffect, useRef } from 'react'
import { createChart, AreaSeries, ColorType } from 'lightweight-charts'
import type { IChartApi, ISeriesApi, UTCTimestamp } from 'lightweight-charts'
import type { PortfolioSnapshot } from '@/hooks/usePortfolioHistory'

interface PnlChartProps {
  snapshots: PortfolioSnapshot[]
}

export default function PnlChart({ snapshots }: PnlChartProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const seriesRef = useRef<ISeriesApi<'Area'> | null>(null)

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
      rightPriceScale: { borderColor: '#30363d' },
      timeScale: { borderColor: '#30363d', timeVisible: true },
      autoSize: true,
    })
    const series = chart.addSeries(AreaSeries, {
      lineColor: '#209dd7',
      topColor: 'rgba(32, 157, 215, 0.3)',
      bottomColor: 'rgba(32, 157, 215, 0.0)',
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

  useEffect(() => {
    const series = seriesRef.current
    const chart = chartRef.current
    if (!series || !chart) return
    const data = snapshots.map(s => ({
      time: Math.floor(new Date(s.recorded_at).getTime() / 1000) as UTCTimestamp,
      value: s.total_value,
    }))
    series.setData(data)
    if (data.length > 0) chart.timeScale().fitContent()
  }, [snapshots])

  return (
    <div style={{ position: 'relative', height: '100%', backgroundColor: '#0d1117' }}>
      <div ref={containerRef} style={{ height: '100%' }} />
      {snapshots.length === 0 && (
        <div style={{
          position: 'absolute',
          inset: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#8b949e',
          fontSize: 11,
          pointerEvents: 'none',
        }}>
          Trade to start tracking P&amp;L
        </div>
      )}
    </div>
  )
}
