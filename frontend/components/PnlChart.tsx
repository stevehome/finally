"use client";

import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip } from "recharts";

export interface PortfolioSnapshot {
  totalValue: number;
  recordedAt: string;
}

interface PnlChartProps {
  snapshots: PortfolioSnapshot[];
}

export default function PnlChart({ snapshots }: PnlChartProps) {
  const chartData = snapshots.map((s) => ({
    time: new Date(s.recordedAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    value: s.totalValue,
  }));

  const startValue = chartData.length > 0 ? chartData[0].value : 10000;
  const currentValue = chartData.length > 0 ? chartData[chartData.length - 1].value : 10000;
  const isUp = currentValue >= startValue;

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center px-3 py-2 border-b border-border">
        <h2 className="text-xs font-semibold text-text-secondary uppercase tracking-wider">P&L</h2>
        {chartData.length > 0 && (
          <span className={`ml-2 text-xs font-mono ${isUp ? "text-positive" : "text-negative"}`}>
            {isUp ? "+" : ""}${(currentValue - startValue).toFixed(2)}
          </span>
        )}
      </div>
      <div className="flex-1">
        {chartData.length === 0 ? (
          <div className="h-full flex items-center justify-center">
            <span className="text-text-secondary text-xs">Waiting for data...</span>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 8, right: 8, bottom: 4, left: 8 }}>
              <XAxis dataKey="time" tick={{ fontSize: 9, fill: "#8b949e" }} tickLine={false} axisLine={false} />
              <YAxis
                domain={["auto", "auto"]}
                tick={{ fontSize: 9, fill: "#8b949e" }}
                tickLine={false}
                axisLine={false}
                tickFormatter={(v: number) => `$${v.toFixed(0)}`}
                width={50}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#161b22",
                  border: "1px solid #30363d",
                  borderRadius: 4,
                  fontSize: 11,
                  fontFamily: "monospace",
                }}
                labelStyle={{ color: "#8b949e" }}
                itemStyle={{ color: "#e6edf3" }}
                formatter={(value) => [`$${Number(value).toFixed(2)}`, "Value"]}
              />
              <Line
                type="monotone"
                dataKey="value"
                stroke={isUp ? "#3fb950" : "#f85149"}
                strokeWidth={1.5}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
