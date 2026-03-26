"use client";

import type { Position } from "./PortfolioHeatmap";

interface PositionsTableProps {
  positions: Position[];
}

export default function PositionsTable({ positions }: PositionsTableProps) {
  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center px-3 py-2 border-b border-border">
        <h2 className="text-xs font-semibold text-text-secondary uppercase tracking-wider">Positions</h2>
      </div>
      <div className="flex-1 overflow-y-auto">
        {positions.length === 0 ? (
          <div className="p-4 text-center text-text-secondary text-xs">No open positions</div>
        ) : (
          <table className="w-full text-xs">
            <thead>
              <tr className="text-text-secondary border-b border-border">
                <th className="text-left px-3 py-1.5 font-medium">Ticker</th>
                <th className="text-right px-3 py-1.5 font-medium">Qty</th>
                <th className="text-right px-3 py-1.5 font-medium">Avg Cost</th>
                <th className="text-right px-3 py-1.5 font-medium">Price</th>
                <th className="text-right px-3 py-1.5 font-medium">P&L</th>
                <th className="text-right px-3 py-1.5 font-medium">%</th>
              </tr>
            </thead>
            <tbody>
              {positions.map((p) => (
                <tr key={p.ticker} className="border-b border-border/50">
                  <td className="px-3 py-2 font-semibold">{p.ticker}</td>
                  <td className="px-3 py-2 text-right font-mono">{p.quantity}</td>
                  <td className="px-3 py-2 text-right font-mono">${p.avgCost.toFixed(2)}</td>
                  <td className="px-3 py-2 text-right font-mono">${p.currentPrice.toFixed(2)}</td>
                  <td className={`px-3 py-2 text-right font-mono ${p.unrealizedPnl >= 0 ? "text-positive" : "text-negative"}`}>
                    ${p.unrealizedPnl.toFixed(2)}
                  </td>
                  <td className={`px-3 py-2 text-right font-mono ${p.pnlPercent >= 0 ? "text-positive" : "text-negative"}`}>
                    {p.pnlPercent >= 0 ? "+" : ""}{p.pnlPercent.toFixed(1)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
