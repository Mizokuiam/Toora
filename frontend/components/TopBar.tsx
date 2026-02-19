"use client";

import { useEffect, useState } from "react";
import { Activity, Circle } from "lucide-react";
import { getAgentStatus, type AgentStatus } from "@/lib/api";
import { useAgentWebSocket } from "@/lib/ws";
import { cn } from "@/lib/utils";

export function TopBar() {
  const [status, setStatus] = useState<AgentStatus["status"]>("idle");

  useEffect(() => {
    getAgentStatus()
      .then((s) => setStatus(s.status))
      .catch(() => {});
  }, []);

  useAgentWebSocket((msg) => {
    if (msg.type === "agent_status") {
      const data = msg.data as { status: AgentStatus["status"] };
      setStatus(data.status);
    }
  });

  const statusConfig = {
    running: { label: "Running", color: "text-emerald-400", pulse: true },
    idle: { label: "Idle", color: "text-zinc-500", pulse: false },
    waiting_for_approval: { label: "Waiting for Approval", color: "text-amber-400", pulse: true },
  }[status] ?? { label: "Unknown", color: "text-zinc-500", pulse: false };

  return (
    <header className="sticky top-0 z-40 flex h-16 items-center border-b border-zinc-800 bg-zinc-950/80 px-6 backdrop-blur">
      <div className="ml-auto flex items-center gap-3">
        <Activity className="h-4 w-4 text-zinc-500" />
        <span className={cn("text-sm font-medium", statusConfig.color)}>
          {statusConfig.label}
        </span>
        <div className="relative">
          <Circle
            className={cn(
              "h-2.5 w-2.5 fill-current",
              statusConfig.color,
              statusConfig.pulse && "animate-pulse"
            )}
          />
        </div>
      </div>
    </header>
  );
}
