"use client";

import { useEffect, useRef } from "react";
import { createChart, LineSeries, type IChartApi, type ISeriesApi, type LineData, type Time } from "lightweight-charts";
import type { PricePoint } from "@/hooks/usePriceStream";

interface MainChartProps {
  ticker: string | null;
  priceHistory: PricePoint[];
}

export default function MainChart({ ticker, priceHistory }: MainChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<"Line"> | null>(null);

  // Create chart on mount
  useEffect(() => {
    if (!containerRef.current) return;

    const chart = createChart(containerRef.current, {
      layout: {
        background: { color: "#0d1117" },
        textColor: "#8b949e",
        fontFamily: "monospace",
      },
      grid: {
        vertLines: { color: "#1a1a2e" },
        horzLines: { color: "#1a1a2e" },
      },
      crosshair: {
        vertLine: { color: "#30363d" },
        horzLine: { color: "#30363d" },
      },
      rightPriceScale: {
        borderColor: "#30363d",
      },
      timeScale: {
        borderColor: "#30363d",
        timeVisible: true,
        secondsVisible: true,
      },
    });

    const series = chart.addSeries(LineSeries, {
      color: "#209dd7",
      lineWidth: 2,
      priceLineVisible: true,
      priceLineColor: "#209dd7",
    });

    chartRef.current = chart;
    seriesRef.current = series;

    const resizeObserver = new ResizeObserver(() => {
      if (containerRef.current) {
        chart.applyOptions({
          width: containerRef.current.clientWidth,
          height: containerRef.current.clientHeight,
        });
      }
    });
    resizeObserver.observe(containerRef.current);

    return () => {
      resizeObserver.disconnect();
      chart.remove();
      chartRef.current = null;
      seriesRef.current = null;
    };
  }, []);

  // Update data when ticker or history changes
  useEffect(() => {
    if (!seriesRef.current) return;

    if (!ticker || priceHistory.length === 0) {
      seriesRef.current.setData([]);
      return;
    }

    // Deduplicate by time (lightweight-charts requires strictly increasing times)
    const seen = new Map<number, number>();
    for (const p of priceHistory) {
      seen.set(p.time, p.price);
    }
    const lineData: LineData<Time>[] = Array.from(seen.entries())
      .sort(([a], [b]) => a - b)
      .map(([time, value]) => ({ time: time as Time, value }));

    seriesRef.current.setData(lineData);
    chartRef.current?.timeScale().fitContent();
  }, [ticker, priceHistory]);

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center px-3 py-2 border-b border-border">
        <h2 className="text-xs font-semibold text-text-secondary uppercase tracking-wider">
          {ticker ? `${ticker}` : "Select a ticker"}
        </h2>
        {ticker && priceHistory.length > 0 && (
          <span className="ml-2 text-xs text-text-secondary">
            {priceHistory.length} pts
          </span>
        )}
      </div>
      <div className="flex-1 relative" ref={containerRef}>
        {!ticker && (
          <div className="absolute inset-0 flex items-center justify-center text-text-secondary text-sm z-10">
            Click a ticker in the watchlist
          </div>
        )}
      </div>
    </div>
  );
}
