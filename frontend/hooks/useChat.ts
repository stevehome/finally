"use client";

import { useState, useCallback } from "react";
import type { ChatMessage } from "@/components/ChatPanel";

export function useChat(onTradeExecuted?: () => void) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const sendMessage = useCallback(
    async (content: string) => {
      const userMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: "user",
        content,
      };
      setMessages((prev) => [...prev, userMsg]);
      setIsLoading(true);

      try {
        const res = await fetch("/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: content }),
        });

        if (res.ok) {
          const data = await res.json();
          const assistantMsg: ChatMessage = {
            id: crypto.randomUUID(),
            role: "assistant",
            content: data.message,
            actions: {
              trades: data.trades,
              watchlistChanges: data.watchlist_changes,
            },
          };
          setMessages((prev) => [...prev, assistantMsg]);

          if (data.trades?.length > 0 || data.watchlist_changes?.length > 0) {
            onTradeExecuted?.();
          }
        } else {
          const err = await res.json().catch(() => ({ detail: "Unknown error" }));
          setMessages((prev) => [
            ...prev,
            {
              id: crypto.randomUUID(),
              role: "assistant",
              content: `Error: ${err.detail || "Failed to get response"}`,
            },
          ]);
        }
      } catch {
        setMessages((prev) => [
          ...prev,
          {
            id: crypto.randomUUID(),
            role: "assistant",
            content: "Error: Could not connect to the server.",
          },
        ]);
      } finally {
        setIsLoading(false);
      }
    },
    [onTradeExecuted]
  );

  return { messages, isLoading, sendMessage };
}
