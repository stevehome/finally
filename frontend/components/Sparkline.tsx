'use client'

import { useEffect, useRef } from 'react'
import {
  createChart,
  LineSeries,
  ColorType,
  CrosshairMode,
} from 'lightweight-charts'
import type { IChartApi, ISeriesApi, UTCTimestamp } from 'lightweight-charts'
import type { SparkPoint } from '@/hooks/usePriceStream'

interface SparklineProps {
  points: SparkPoint[]
  color?: string
  width?: number
  height?: number
}

export default function Sparkline({
  points,
  color = '#209dd7',
  width = 80,
  height = 32,
}: SparklineProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const seriesRef = useRef<ISeriesApi<'Line'> | null>(null)

  // Create chart once on mount
  useEffect(() => {
    if (!containerRef.current) return

    const chart = createChart(containerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: 'transparent' },
        textColor: 'transparent',
      },
      grid: {
        vertLines: { visible: false },
        horzLines: { visible: false },
      },
      leftPriceScale: { visible: false },
      rightPriceScale: { visible: false },
      timeScale: { visible: false },
      crosshair: { mode: CrosshairMode.Hidden },
      handleScroll: false,
      handleScale: false,
      width,
      height,
    })

    const series = chart.addSeries(LineSeries, {
      color,
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: false,
      crosshairMarkerVisible: false,
    })

    chartRef.current = chart
    seriesRef.current = series

    return () => {
      chart.remove()
      chartRef.current = null
      seriesRef.current = null
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // Update series data when points change
  useEffect(() => {
    const series = seriesRef.current
    if (!series || points.length === 0) return

    // Cast time to UTCTimestamp (lightweight-charts nominal type over number)
    const toChartPoint = (p: SparkPoint) => ({ time: p.time as UTCTimestamp, value: p.value })

    if (points.length === 1) {
      // Initial data — use setData
      series.setData(points.map(toChartPoint))
    } else {
      // Append latest point only — avoids re-rendering entire history on every tick
      series.update(toChartPoint(points[points.length - 1]))
    }
  }, [points])

  return <div ref={containerRef} style={{ width, height }} />
}
