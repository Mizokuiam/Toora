"use client";

import { useEffect, useRef, useState } from "react";
import { useAgentWebSocket, type WsMessage } from "@/lib/ws";
import { formatDistanceToNow } from "date-fns";

interface FeedItem {
  id: number;
  type: string;
  text: string;
  time: Date;
}

let _id = 0;

export function LiveFeed() {
  const [items, setItems] = useState<FeedItem[]>([]);
  const bottomRef = useRef<HTMLDivElement>(null);

  useAgentWebSocket((msg: WsMessage) => {
    const text = summariseMessage(msg);
    if (!text) return;
    setItems((prev) => [
      { id: _id++, type: msg.type, text, time: new Date() },
      ...prev.slice(0, 49),
    ]);
  });

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [items]);

  if (items.length === 0) {
    return (
      <div className="flex h-32 items-center justify-center rounded-lg border border-zinc-800 text-sm text-zinc-600">
        Waiting for agent activity…
      </div>
    );
  }

  return (
    <div className="space-y-1 rounded-lg border border-zinc-800 bg-zinc-900 p-3 max-h-64 overflow-y-auto">
      {items.map((item) => (
        <div key={item.id} className="flex items-start gap-3 text-sm">
          <span className="mt-0.5 shrink-0 rounded bg-violet-600/20 px-1.5 py-0.5 text-xs text-violet-400 font-mono">
            {item.type}
          </span>
          <span className="flex-1 text-zinc-300">{item.text}</span>
          <span className="shrink-0 text-xs text-zinc-600">
            {formatDistanceToNow(item.time, { addSuffix: true })}
          </span>
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  );
}

function summariseMessage(msg: WsMessage): string {
  const d = msg.data as Record<string, unknown> | undefined;
  switch (msg.type) {
    case "tool_call":
      return `Tool called: ${d?.tool ?? "unknown"}`;
    case "tool_result":
      return `Tool finished: ${d?.tool ?? "unknown"}`;
    case "agent_status":
      return `Agent status → ${d?.status ?? "unknown"}`;
    case "approval_resolved":
      return `Approval #${d?.id} ${d?.status}`;
    default:
      return JSON.stringify(msg).slice(0, 100);
  }
}
