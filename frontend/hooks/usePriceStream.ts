"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import type { TickerData } from "@/components/WatchlistPanel";

interface PriceEvent {
  ticker: string;
  price: number;
  previous_price: number;
  timestamp: number;
  direction: "up" | "down" | "flat";
}

const MAX_SPARKLINE_POINTS = 60;

export interface PricePoint {
  time: number; // unix seconds
  price: number;
}

export type SSEStatus = "connected" | "reconnecting" | "disconnected";

export function usePriceStream() {
  const [tickers, setTickers] = useState<Map<string, TickerData>>(new Map());
  const [sseStatus, setSseStatus] = useState<SSEStatus>("disconnected");
  const sparklineRef = useRef<Map<string, number[]>>(new Map());
  const priceHistoryRef = useRef<Map<string, PricePoint[]>>(new Map());
  const flashTimeouts = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map());

  useEffect(() => {
    const eventSource = new EventSource("/api/stream/prices");

    eventSource.onopen = () => {
      setSseStatus("connected");
    };

    eventSource.onmessage = (event) => {
      try {
        const allTickers: Record<string, PriceEvent> = JSON.parse(event.data);

        setTickers((prev) => {
          const next = new Map(prev);

          for (const [ticker, data] of Object.entries(allTickers)) {
            const { price, previous_price, direction, timestamp } = data;

            // Update sparkline
            const sparkline = sparklineRef.current.get(ticker) ?? [];
            sparkline.push(price);
            if (sparkline.length > MAX_SPARKLINE_POINTS) sparkline.shift();
            sparklineRef.current.set(ticker, sparkline);

            // Update price history for main chart (timestamp is unix seconds)
            const history = priceHistoryRef.current.get(ticker) ?? [];
            const timeSec = Math.floor(timestamp);
            history.push({ time: timeSec, price });
            priceHistoryRef.current.set(ticker, history);

            const change = price - previous_price;
            const changePercent = previous_price !== 0 ? (change / previous_price) * 100 : 0;

            next.set(ticker, {
              ticker,
              price,
              previousPrice: previous_price,
              change,
              changePercent,
              direction,
              sparklineData: [...sparkline],
            });
          }

          return next;
        });
      } catch {
        // Ignore malformed events
      }
    };

    eventSource.onerror = () => {
      if (eventSource.readyState === EventSource.CONNECTING) {
        setSseStatus("reconnecting");
      } else {
        setSseStatus("disconnected");
      }
    };

    return () => {
      eventSource.close();
      flashTimeouts.current.forEach((t) => clearTimeout(t));
    };
  }, []);

  const tickerList = Array.from(tickers.values());

  const getPrice = useCallback(
    (ticker: string) => tickers.get(ticker)?.price ?? 0,
    [tickers]
  );

  const getPriceHistory = useCallback(
    (ticker: string): PricePoint[] => priceHistoryRef.current.get(ticker) ?? [],
    []
  );

  return { tickers: tickerList, sseStatus, getPrice, getPriceHistory };
}
