"use client";

import { useState, useRef, useEffect } from "react";

export interface TickerData {
  ticker: string;
  price: number;
  previousPrice: number;
  change: number;
  changePercent: number;
  direction: "up" | "down" | "flat";
  sparklineData: number[];
}

interface WatchlistPanelProps {
  tickers: TickerData[];
  watchlist: string[];
  selectedTicker: string | null;
  onSelectTicker: (ticker: string) => void;
  onAddTicker: (ticker: string) => void;
  onRemoveTicker: (ticker: string) => void;
}

function Sparkline({ data }: { data: number[] }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || data.length < 2) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);

    const min = Math.min(...data);
    const max = Math.max(...data);
    const range = max - min || 1;

    const isUp = data[data.length - 1] >= data[0];
    ctx.strokeStyle = isUp ? "#3fb950" : "#f85149";
    ctx.lineWidth = 1;
    ctx.beginPath();

    data.forEach((val, i) => {
      const x = (i / (data.length - 1)) * w;
      const y = h - ((val - min) / range) * h;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });

    ctx.stroke();
  }, [data]);

  return <canvas ref={canvasRef} width={60} height={20} className="inline-block" />;
}

function TickerRow({
  data,
  isSelected,
  onSelect,
  onRemove,
}: {
  data: TickerData;
  isSelected: boolean;
  onSelect: () => void;
  onRemove: () => void;
}) {
  const [flashClass, setFlashClass] = useState("");
  const prevPriceRef = useRef(data.price);

  useEffect(() => {
    if (data.price !== prevPriceRef.current) {
      const cls = data.price > prevPriceRef.current ? "flash-green" : "flash-red";
      setFlashClass(cls);
      const timer = setTimeout(() => setFlashClass(""), 500);
      prevPriceRef.current = data.price;
      return () => clearTimeout(timer);
    }
  }, [data.price]);

  return (
    <tr
      data-testid={`ticker-row-${data.ticker}`}
      onClick={onSelect}
      className={`cursor-pointer border-b border-border/50 hover:bg-bg-tertiary transition-colors ${
        isSelected ? "bg-bg-tertiary" : ""
      } ${flashClass}`}
    >
      <td className="px-2 py-1.5">
        <div className="flex items-center gap-1">
          <span className="font-semibold text-text-primary">{data.ticker}</span>
          <button
            onClick={(e) => {
              e.stopPropagation();
              onRemove();
            }}
            className="opacity-0 group-hover:opacity-100 text-text-secondary hover:text-negative text-[10px] ml-auto"
            title="Remove"
          >
            x
          </button>
        </div>
      </td>
      <td className="px-2 py-1.5 text-right font-mono">
        <Sparkline data={data.sparklineData} />
      </td>
      <td
        className={`px-2 py-1.5 text-right font-mono ${
          data.direction === "up" ? "text-positive" : data.direction === "down" ? "text-negative" : "text-text-primary"
        }`}
      >
        {data.price.toFixed(2)}
      </td>
      <td
        className={`px-2 py-1.5 text-right font-mono ${
          data.changePercent >= 0 ? "text-positive" : "text-negative"
        }`}
      >
        {data.changePercent >= 0 ? "+" : ""}
        {data.changePercent.toFixed(2)}%
      </td>
    </tr>
  );
}

export default function WatchlistPanel({
  tickers,
  watchlist,
  selectedTicker,
  onSelectTicker,
  onAddTicker,
  onRemoveTicker,
}: WatchlistPanelProps) {
  const [newTicker, setNewTicker] = useState("");

  const handleAdd = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTicker.trim()) return;
    onAddTicker(newTicker.trim().toUpperCase());
    setNewTicker("");
  };

  // Show watchlist tickers, use price data if available
  const displayTickers = watchlist.map((symbol) => {
    const priceData = tickers.find((t) => t.ticker === symbol);
    return (
      priceData ?? {
        ticker: symbol,
        price: 0,
        previousPrice: 0,
        change: 0,
        changePercent: 0,
        direction: "flat" as const,
        sparklineData: [],
      }
    );
  });

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-3 py-2 border-b border-border">
        <h2 className="text-xs font-semibold text-text-secondary uppercase tracking-wider">Watchlist</h2>
        <span className="text-xs text-text-secondary">{watchlist.length}</span>
      </div>
      <div className="flex-1 overflow-y-auto">
        {displayTickers.length === 0 ? (
          <div className="p-4 text-center text-text-secondary text-xs">No tickers in watchlist</div>
        ) : (
          <table className="w-full text-xs">
            <tbody>
              {displayTickers.map((t) => (
                <TickerRow
                  key={t.ticker}
                  data={t}
                  isSelected={selectedTicker === t.ticker}
                  onSelect={() => onSelectTicker(t.ticker)}
                  onRemove={() => onRemoveTicker(t.ticker)}
                />
              ))}
            </tbody>
          </table>
        )}
      </div>
      <form onSubmit={handleAdd} className="px-2 py-1.5 border-t border-border flex gap-1">
        <input
          type="text"
          value={newTicker}
          onChange={(e) => setNewTicker(e.target.value)}
          placeholder="Add ticker..."
          className="flex-1 px-2 py-1 text-xs bg-bg-primary border border-border rounded text-text-primary placeholder-text-secondary focus:outline-none focus:border-accent-blue"
        />
        <button
          type="submit"
          className="px-2 py-1 text-xs bg-accent-blue/20 text-accent-blue border border-accent-blue/40 rounded hover:bg-accent-blue/30 transition-colors"
        >
          +
        </button>
      </form>
    </div>
  );
}
