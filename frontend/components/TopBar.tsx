"use client";

import { useEffect, useState } from "react";
import { Activity, Circle, Search } from "lucide-react";
import { getAgentStatus, type AgentStatus } from "@/lib/api";
import { useAgentWebSocket } from "@/lib/ws";
import { cn } from "@/lib/utils";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

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
    idle: { label: "Idle", color: "text-muted-foreground", pulse: false },
    waiting_for_approval: { label: "Waiting for Approval", color: "text-amber-400", pulse: true },
  }[status] ?? { label: "Unknown", color: "text-muted-foreground", pulse: false };

  return (
    <header className="sticky top-0 z-40 flex h-14 items-center gap-4 border-b border-border bg-background/95 px-6 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex flex-1 items-center gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
          <Input
            placeholder="Search..."
            className="pl-9 h-9 bg-muted/50 border-0"
          />
        </div>
      </div>
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 rounded-lg border border-border bg-muted/30 px-3 py-1.5">
          <Activity className="size-4 text-muted-foreground" />
          <span className={cn("text-sm font-medium", statusConfig.color)}>
            {statusConfig.label}
          </span>
          <Circle
            className={cn(
              "size-2 fill-current",
              statusConfig.color,
              statusConfig.pulse && "animate-pulse"
            )}
          />
        </div>
      </div>
    </header>
  );
}
