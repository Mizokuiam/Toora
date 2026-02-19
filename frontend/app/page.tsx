"use client";

import { useEffect, useState } from "react";
import {
  getTodayStats,
  getAgentStatus,
  getLogs,
  runAgent,
  type TodayStats,
  type AgentStatus,
  type ActionLog,
} from "@/lib/api";
import { LiveFeed } from "@/components/LiveFeed";
import { Mail, ListTodo, Clock, CheckSquare, Play, Loader2, TrendingUp } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { cn } from "@/lib/utils";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

function StatCard({
  label,
  value,
  description,
  icon: Icon,
  trend,
}: {
  label: string;
  value: number | string;
  description?: string;
  icon: React.ElementType;
  trend?: { value: string; up: boolean };
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {label}
        </CardTitle>
        <Icon className="size-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {(description || trend) && (
          <div className="mt-1 flex items-center gap-2 text-xs text-muted-foreground">
            {trend && (
              <span
                className={cn(
                  "flex items-center gap-0.5 font-medium",
                  trend.up ? "text-emerald-500" : "text-amber-500"
                )}
              >
                <TrendingUp className={cn("size-3", !trend.up && "rotate-180")} />
                {trend.value}
              </span>
            )}
            {description && <span>{description}</span>}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

const STATUS_BADGE: Record<string, string> = {
  completed: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
  running: "bg-blue-500/10 text-blue-400 border-blue-500/20",
  failed: "bg-red-500/10 text-red-400 border-red-500/20",
  approved: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
  rejected: "bg-red-500/10 text-red-400 border-red-500/20",
  pending: "bg-amber-500/10 text-amber-400 border-amber-500/20",
  expired: "bg-muted text-muted-foreground",
};

export default function DashboardPage() {
  const [stats, setStats] = useState<TodayStats | null>(null);
  const [agentStatus, setAgentStatus] = useState<AgentStatus | null>(null);
  const [recentLogs, setRecentLogs] = useState<ActionLog[]>([]);
  const [running, setRunning] = useState(false);
  const [customInput, setCustomInput] = useState("");

  const load = () => {
    getTodayStats().then(setStats).catch(() => {});
    getAgentStatus().then(setAgentStatus).catch(() => {});
    getLogs({ page: 1, per_page: 5 })
      .then((r) => setRecentLogs(r.items))
      .catch(() => {});
  };

  useEffect(() => {
    load();
    const iv = setInterval(load, 15_000);
    return () => clearInterval(iv);
  }, []);

  const handleRun = async () => {
    setRunning(true);
    try {
      await runAgent(customInput.trim() || undefined);
      setCustomInput("");
      setTimeout(load, 2000);
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-sm text-muted-foreground">Today&apos;s overview</p>
        </div>
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
          <Input
            placeholder="Or give a custom instruction..."
            value={customInput}
            onChange={(e) => setCustomInput(e.target.value)}
            className="sm:w-80"
          />
          <Button
            onClick={handleRun}
            disabled={running || agentStatus?.status === "running"}
          >
            {running ? <Loader2 className="size-4 animate-spin" /> : <Play className="size-4" />}
            Run Agent Now
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Emails Processed"
          value={stats?.emails_processed ?? "—"}
          description="Today"
          icon={Mail}
        />
        <StatCard
          label="Tasks Created"
          value={stats?.tasks_created ?? "—"}
          description="Today"
          icon={ListTodo}
        />
        <StatCard
          label="Pending Approvals"
          value={stats?.approvals_pending ?? "—"}
          description="Awaiting action"
          icon={CheckSquare}
        />
        <StatCard
          label="Last Run"
          value={
            stats?.last_run_at
              ? formatDistanceToNow(new Date(stats.last_run_at), { addSuffix: true })
              : "Never"
          }
          icon={Clock}
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Live Feed */}
        <Card>
          <CardHeader>
            <CardTitle>Live Activity</CardTitle>
            <CardDescription>Real-time agent updates</CardDescription>
          </CardHeader>
          <CardContent>
            <LiveFeed />
          </CardContent>
        </Card>

        {/* Recent Actions */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Actions</CardTitle>
            <CardDescription>Latest tool usage</CardDescription>
          </CardHeader>
          <CardContent>
            {recentLogs.length === 0 ? (
              <div className="flex h-32 items-center justify-center rounded-lg border border-dashed text-sm text-muted-foreground">
                No actions yet
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Tool</TableHead>
                    <TableHead>Time</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {recentLogs.map((log) => (
                    <TableRow key={log.id}>
                      <TableCell className="font-mono text-xs text-primary">
                        {log.tool_used}
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        {formatDistanceToNow(new Date(log.timestamp), { addSuffix: true })}
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant="secondary"
                          className={cn(
                            "font-normal border",
                            STATUS_BADGE[log.approval_status ?? "completed"] ??
                              "bg-muted text-muted-foreground"
                          )}
                        >
                          {log.approval_status ?? "done"}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
