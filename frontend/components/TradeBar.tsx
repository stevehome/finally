"use client";

import { useState } from "react";

interface TradeBarProps {
  onTrade: (ticker: string, quantity: number, side: "buy" | "sell") => void;
}

export default function TradeBar({ onTrade }: TradeBarProps) {
  const [ticker, setTicker] = useState("");
  const [quantity, setQuantity] = useState("");

  const handleTrade = (side: "buy" | "sell") => {
    const qty = parseFloat(quantity);
    if (!ticker.trim() || isNaN(qty) || qty <= 0) return;
    onTrade(ticker.trim().toUpperCase(), qty, side);
    setTicker("");
    setQuantity("");
  };

  return (
    <div className="flex items-center gap-2 px-3 py-2 bg-bg-secondary border-t border-border">
      <input
        type="text"
        placeholder="Ticker"
        value={ticker}
        onChange={(e) => setTicker(e.target.value)}
        className="w-20 px-2 py-1.5 text-xs bg-bg-primary border border-border rounded text-text-primary placeholder-text-secondary focus:outline-none focus:border-accent-blue"
      />
      <input
        type="number"
        placeholder="Qty"
        value={quantity}
        onChange={(e) => setQuantity(e.target.value)}
        className="w-20 px-2 py-1.5 text-xs bg-bg-primary border border-border rounded text-text-primary placeholder-text-secondary focus:outline-none focus:border-accent-blue"
      />
      <button
        data-testid="trade-buy"
        onClick={() => handleTrade("buy")}
        className="px-3 py-1.5 text-xs font-semibold bg-positive/20 text-positive border border-positive/40 rounded hover:bg-positive/30 transition-colors"
      >
        BUY
      </button>
      <button
        data-testid="trade-sell"
        onClick={() => handleTrade("sell")}
        className="px-3 py-1.5 text-xs font-semibold bg-negative/20 text-negative border border-negative/40 rounded hover:bg-negative/30 transition-colors"
      >
        SELL
      </button>
    </div>
  );
}
