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
      <div className="flex h-32 items-center justify-center rounded-lg border border-dashed text-sm text-muted-foreground">
        Waiting for agent activity…
      </div>
    );
  }

  return (
    <div className="max-h-64 space-y-1 overflow-y-auto rounded-lg border bg-muted/20 p-3">
      {items.map((item) => (
        <div key={item.id} className="flex items-start gap-3 text-sm">
          <span className="mt-0.5 shrink-0 rounded bg-primary/10 px-1.5 py-0.5 text-xs font-mono text-primary">
            {item.type}
          </span>
          <span className="flex-1 text-muted-foreground">{item.text}</span>
          <span className="shrink-0 text-xs text-muted-foreground/70">
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
