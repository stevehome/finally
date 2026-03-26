"use client";

import { ResponsiveContainer, Treemap } from "recharts";

export interface Position {
  ticker: string;
  quantity: number;
  avgCost: number;
  currentPrice: number;
  unrealizedPnl: number;
  pnlPercent: number;
  marketValue: number;
  weight: number;
}

interface PortfolioHeatmapProps {
  positions: Position[];
}

interface TreemapContentProps {
  x: number;
  y: number;
  width: number;
  height: number;
  name: string;
  pnlPercent: number;
}

function CustomContent({ x, y, width, height, name, pnlPercent }: TreemapContentProps) {
  const isProfit = pnlPercent >= 0;
  const intensity = Math.min(Math.abs(pnlPercent) / 5, 1);
  const fill = isProfit
    ? `rgba(63, 185, 80, ${0.15 + intensity * 0.45})`
    : `rgba(248, 81, 73, ${0.15 + intensity * 0.45})`;

  if (width < 20 || height < 20) return null;

  return (
    <g>
      <rect x={x} y={y} width={width} height={height} fill={fill} stroke="#30363d" strokeWidth={1} />
      {width > 40 && height > 30 && (
        <>
          <text x={x + width / 2} y={y + height / 2 - 6} textAnchor="middle" fill="#e6edf3" fontSize={11} fontWeight="bold" fontFamily="monospace">
            {name}
          </text>
          <text
            x={x + width / 2}
            y={y + height / 2 + 10}
            textAnchor="middle"
            fill={isProfit ? "#3fb950" : "#f85149"}
            fontSize={10}
            fontFamily="monospace"
          >
            {isProfit ? "+" : ""}{pnlPercent.toFixed(1)}%
          </text>
        </>
      )}
    </g>
  );
}

export default function PortfolioHeatmap({ positions }: PortfolioHeatmapProps) {
  const treemapData = positions.map((p) => ({
    name: p.ticker,
    size: Math.max(p.marketValue, 1),
    pnlPercent: p.pnlPercent,
  }));

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center px-3 py-2 border-b border-border">
        <h2 className="text-xs font-semibold text-text-secondary uppercase tracking-wider">Portfolio Heatmap</h2>
      </div>
      <div className="flex-1">
        {positions.length === 0 ? (
          <div className="h-full flex items-center justify-center">
            <span className="text-text-secondary text-xs">No positions yet</span>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <Treemap
              data={treemapData}
              dataKey="size"
              stroke="#30363d"
              content={<CustomContent x={0} y={0} width={0} height={0} name="" pnlPercent={0} />}
            />
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
