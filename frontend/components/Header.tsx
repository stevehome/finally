"use client";

interface HeaderProps {
  totalValue: number;
  cashBalance: number;
  sseStatus: "connected" | "reconnecting" | "disconnected";
}

export default function Header({ totalValue, cashBalance, sseStatus }: HeaderProps) {
  const statusColor = {
    connected: "bg-positive",
    reconnecting: "bg-accent-yellow",
    disconnected: "bg-negative",
  }[sseStatus];

  return (
    <header className="flex items-center justify-between px-4 py-2 bg-bg-secondary border-b border-border">
      <div className="flex items-center gap-3">
        <h1 className="text-lg font-bold text-accent-yellow tracking-wide">FinAlly</h1>
        <span className="text-xs text-text-secondary">AI Trading Workstation</span>
      </div>
      <div className="flex items-center gap-6">
        <div className="text-right">
          <div className="text-xs text-text-secondary">Portfolio Value</div>
          <div className="text-sm font-bold">${totalValue.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
        </div>
        <div className="text-right">
          <div className="text-xs text-text-secondary">Cash</div>
          <div className="text-sm font-bold" data-testid="cash-balance">
            ${cashBalance.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
        </div>
        <div className="flex items-center gap-1.5" data-testid="sse-status">
          <div className={`w-2 h-2 rounded-full ${statusColor}`} />
          <span className="text-xs text-text-secondary capitalize">{sseStatus}</span>
        </div>
      </div>
    </header>
  );
}
