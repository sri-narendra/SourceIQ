"use client";

import { useCallback, useState } from "react";

import { chatApi } from "@/services/api-endpoints";
import type { IChatResponse } from "@/types";

export function useChat(workspaceId: string) {
  const [messages, setMessages] = useState<
    { role: "user" | "assistant"; content: string }[]
  >([]);
  const [loading, setLoading] = useState(false);

  const send = useCallback(
    async (message: string) => {
      if (!workspaceId) return;
      setMessages((m) => [...m, { role: "user", content: message }]);
      setLoading(true);
      try {
        const res: IChatResponse = await chatApi.ask({
          workspaceId,
          message,
        });
        setMessages((m) => [...m, { role: "assistant", content: res.answer }]);
      } finally {
        setLoading(false);
      }
    },
    [workspaceId]
  );

  return { messages, loading, send };
}