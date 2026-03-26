"use client";

import { useEffect, useState, useCallback } from "react";

interface WatchlistItem {
  ticker: string;
}

export function useWatchlist() {
  const [watchlist, setWatchlist] = useState<string[]>([]);

  const fetchWatchlist = useCallback(async () => {
    try {
      const res = await fetch("/api/watchlist");
      if (res.ok) {
        const data = await res.json();
        setWatchlist(data.map((item: WatchlistItem) => item.ticker));
      }
    } catch {
      // API not available yet
    }
  }, []);

  useEffect(() => {
    fetchWatchlist();
  }, [fetchWatchlist]);

  const addTicker = useCallback(async (ticker: string) => {
    try {
      const res = await fetch("/api/watchlist", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ticker: ticker.toUpperCase() }),
      });
      if (res.ok) {
        setWatchlist((prev) =>
          prev.includes(ticker.toUpperCase()) ? prev : [...prev, ticker.toUpperCase()]
        );
      }
    } catch {
      // API not available
    }
  }, []);

  const removeTicker = useCallback(async (ticker: string) => {
    try {
      const res = await fetch(`/api/watchlist/${ticker.toUpperCase()}`, {
        method: "DELETE",
      });
      if (res.ok) {
        setWatchlist((prev) => prev.filter((t) => t !== ticker.toUpperCase()));
      }
    } catch {
      // API not available
    }
  }, []);

  return { watchlist, addTicker, removeTicker, refetch: fetchWatchlist };
}
