"use client";

import { useState } from "react";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  actions?: {
    trades?: Array<{ ticker: string; side: string; quantity: number }>;
    watchlistChanges?: Array<{ ticker: string; action: string }>;
  };
}

interface ChatPanelProps {
  messages: ChatMessage[];
  onSendMessage: (message: string) => void;
  isLoading: boolean;
}

export default function ChatPanel({ messages, onSendMessage, isLoading }: ChatPanelProps) {
  const [input, setInput] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    onSendMessage(input.trim());
    setInput("");
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center px-3 py-2 border-b border-border">
        <h2 className="text-xs font-semibold text-text-secondary uppercase tracking-wider">AI Assistant</h2>
      </div>
      <div className="flex-1 overflow-y-auto p-3 space-y-3" data-testid="chat-messages">
        {messages.length === 0 ? (
          <div className="text-text-secondary text-xs text-center mt-4">
            Ask me about your portfolio, market analysis, or to execute trades.
          </div>
        ) : (
          messages.map((msg) => (
            <div key={msg.id} className={`text-xs ${msg.role === "user" ? "text-right" : ""}`}>
              <div
                className={`inline-block max-w-[90%] px-3 py-2 rounded-lg ${
                  msg.role === "user"
                    ? "bg-accent-blue/20 text-text-primary"
                    : "bg-bg-tertiary text-text-primary"
                }`}
              >
                {msg.content}
              </div>
              {msg.actions?.trades && msg.actions.trades.length > 0 && (
                <div className="mt-1 text-[10px] text-accent-yellow">
                  {msg.actions.trades.map((t, i) => (
                    <div key={i}>Executed: {t.side.toUpperCase()} {t.quantity} {t.ticker}</div>
                  ))}
                </div>
              )}
            </div>
          ))
        )}
        {isLoading && (
          <div className="text-xs text-text-secondary animate-pulse">Thinking...</div>
        )}
      </div>
      <form onSubmit={handleSubmit} className="p-2 border-t border-border">
        <div className="flex gap-2">
          <input
            data-testid="chat-input"
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask FinAlly..."
            className="flex-1 px-3 py-1.5 text-xs bg-bg-primary border border-border rounded text-text-primary placeholder-text-secondary focus:outline-none focus:border-accent-blue"
          />
          <button
            type="submit"
            disabled={isLoading}
            className="px-3 py-1.5 text-xs font-semibold bg-accent-purple text-white rounded hover:bg-accent-purple/80 transition-colors disabled:opacity-50"
          >
            Send
          </button>
        </div>
      </form>
    </div>
  );
}
