"use client";

import { useState, useCallback } from "react";
import Header from "@/components/Header";
import WatchlistPanel from "@/components/WatchlistPanel";
import MainChart from "@/components/MainChart";
import PortfolioHeatmap from "@/components/PortfolioHeatmap";
import PnlChart from "@/components/PnlChart";
import PositionsTable from "@/components/PositionsTable";
import TradeBar from "@/components/TradeBar";
import ChatPanel from "@/components/ChatPanel";
import { usePriceStream } from "@/hooks/usePriceStream";
import { useWatchlist } from "@/hooks/useWatchlist";
import { usePortfolio } from "@/hooks/usePortfolio";
import { useChat } from "@/hooks/useChat";

export default function Home() {
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null);
  const { tickers, sseStatus, getPriceHistory } = usePriceStream();
  const { watchlist, addTicker, removeTicker, refetch: refetchWatchlist } = useWatchlist();
  const { cashBalance, totalValue, positions, snapshots, refetch: refetchPortfolio } = usePortfolio();

  const handleTradeOrChatAction = useCallback(() => {
    refetchPortfolio();
    refetchWatchlist();
  }, [refetchPortfolio, refetchWatchlist]);

  const { messages, isLoading, sendMessage } = useChat(handleTradeOrChatAction);

  const handleTrade = async (ticker: string, quantity: number, side: "buy" | "sell") => {
    try {
      const res = await fetch("/api/portfolio/trade", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ticker, quantity, side }),
      });
      if (!res.ok) {
        const err = await res.json();
        console.error("Trade failed:", err);
      } else {
        refetchPortfolio();
      }
    } catch (e) {
      console.error("Trade error:", e);
    }
  };

  return (
    <div className="h-full flex flex-col bg-bg-primary">
      <Header totalValue={totalValue} cashBalance={cashBalance} sseStatus={sseStatus} />

      <div className="flex-1 flex overflow-hidden">
        {/* Left: Watchlist + Trade */}
        <div className="w-72 border-r border-border flex flex-col">
          <WatchlistPanel
            tickers={tickers}
            watchlist={watchlist}
            selectedTicker={selectedTicker}
            onSelectTicker={setSelectedTicker}
            onAddTicker={addTicker}
            onRemoveTicker={removeTicker}
          />
          <TradeBar onTrade={handleTrade} />
        </div>

        {/* Center: Charts + Positions */}
        <div className="flex-1 flex flex-col overflow-hidden">
          <div className="flex-1 flex overflow-hidden">
            <div className="flex-[2] border-r border-border">
              <MainChart ticker={selectedTicker} priceHistory={selectedTicker ? getPriceHistory(selectedTicker) : []} />
            </div>
            <div className="flex-1">
              <PortfolioHeatmap positions={positions} />
            </div>
          </div>
          <div className="h-48 flex border-t border-border overflow-hidden">
            <div className="w-72 border-r border-border">
              <PnlChart snapshots={snapshots} />
            </div>
            <div className="flex-1">
              <PositionsTable positions={positions} />
            </div>
          </div>
        </div>

        {/* Right: Chat */}
        <div className="w-80 border-l border-border">
          <ChatPanel
            messages={messages}
            onSendMessage={sendMessage}
            isLoading={isLoading}
          />
        </div>
      </div>
    </div>
  );
}
