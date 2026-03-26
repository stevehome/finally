"use client";

import { useEffect, useState, useCallback } from "react";
import type { Position } from "@/components/PortfolioHeatmap";
import type { PortfolioSnapshot } from "@/components/PnlChart";

interface PortfolioResponse {
  cash_balance: number;
  total_value: number;
  positions: Array<{
    ticker: string;
    quantity: number;
    avg_cost: number;
    current_price: number;
    unrealized_pnl: number;
    pnl_percent: number;
    market_value: number;
    weight: number;
  }>;
}

export function usePortfolio() {
  const [cashBalance, setCashBalance] = useState(10000);
  const [totalValue, setTotalValue] = useState(10000);
  const [positions, setPositions] = useState<Position[]>([]);
  const [snapshots, setSnapshots] = useState<PortfolioSnapshot[]>([]);

  const fetchPortfolio = useCallback(async () => {
    try {
      const res = await fetch("/api/portfolio");
      if (res.ok) {
        const data: PortfolioResponse = await res.json();
        setCashBalance(data.cash_balance);
        setTotalValue(data.total_value);
        setPositions(
          data.positions.map((p) => ({
            ticker: p.ticker,
            quantity: p.quantity,
            avgCost: p.avg_cost,
            currentPrice: p.current_price,
            unrealizedPnl: p.unrealized_pnl,
            pnlPercent: p.pnl_percent,
            marketValue: p.market_value,
            weight: p.weight,
          }))
        );
      }
    } catch {
      // API not available yet
    }
  }, []);

  const fetchHistory = useCallback(async () => {
    try {
      const res = await fetch("/api/portfolio/history");
      if (res.ok) {
        const data = await res.json();
        setSnapshots(
          data.map((s: { total_value: number; recorded_at: string }) => ({
            totalValue: s.total_value,
            recordedAt: s.recorded_at,
          }))
        );
      }
    } catch {
      // API not available yet
    }
  }, []);

  useEffect(() => {
    fetchPortfolio();
    fetchHistory();
    const interval = setInterval(() => {
      fetchPortfolio();
      fetchHistory();
    }, 5000);
    return () => clearInterval(interval);
  }, [fetchPortfolio, fetchHistory]);

  return { cashBalance, totalValue, positions, snapshots, refetch: fetchPortfolio };
}
