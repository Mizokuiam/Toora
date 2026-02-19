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
import { Mail, ListTodo, Clock, CheckSquare, Play, Loader2 } from "lucide-react";
import { formatDistanceToNow } from "date-fns";

function StatCard({
  label,
  value,
  icon: Icon,
}: {
  label: string;
  value: number | string;
  icon: React.ElementType;
}) {
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-5">
      <div className="flex items-center justify-between">
        <p className="text-sm text-zinc-500">{label}</p>
        <Icon className="h-4 w-4 text-zinc-600" />
      </div>
      <p className="mt-2 text-3xl font-bold text-zinc-100">{value}</p>
    </div>
  );
}

const STATUS_BADGE: Record<string, string> = {
  completed: "bg-emerald-500/10 text-emerald-400",
  running: "bg-blue-500/10 text-blue-400",
  failed: "bg-red-500/10 text-red-400",
  approved: "bg-emerald-500/10 text-emerald-400",
  rejected: "bg-red-500/10 text-red-400",
  pending: "bg-amber-500/10 text-amber-400",
  expired: "bg-zinc-700 text-zinc-400",
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
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-100">Dashboard</h1>
          <p className="text-sm text-zinc-500">Today's overview</p>
        </div>
        <div className="flex flex-col gap-2 sm:flex-row sm:items-end">
          <input
            type="text"
            placeholder="Or give a custom instruction (e.g. Summarize urgent emails only)"
            value={customInput}
            onChange={(e) => setCustomInput(e.target.value)}
            className="flex-1 rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-600 focus:border-violet-500 focus:outline-none"
          />
          <button
            onClick={handleRun}
            disabled={running || agentStatus?.status === "running"}
            className="flex items-center justify-center gap-2 rounded-lg bg-violet-600 px-4 py-2 text-sm font-medium text-white hover:bg-violet-500 disabled:opacity-50 transition-colors"
          >
            {running ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
            Run Agent Now
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard label="Emails Processed" value={stats?.emails_processed ?? "—"} icon={Mail} />
        <StatCard label="Tasks Created" value={stats?.tasks_created ?? "—"} icon={ListTodo} />
        <StatCard label="Pending Approvals" value={stats?.approvals_pending ?? "—"} icon={CheckSquare} />
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
        <div>
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wider text-zinc-500">
            Live Activity
          </h2>
          <LiveFeed />
        </div>

        {/* Recent Actions */}
        <div>
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wider text-zinc-500">
            Recent Actions
          </h2>
          <div className="rounded-xl border border-zinc-800 bg-zinc-900 overflow-hidden">
            {recentLogs.length === 0 ? (
              <div className="flex h-32 items-center justify-center text-sm text-zinc-600">
                No actions yet
              </div>
            ) : (
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-zinc-800">
                    <th className="px-4 py-3 text-left text-xs font-medium text-zinc-500">Tool</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-zinc-500">Time</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-zinc-500">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-800">
                  {recentLogs.map((log) => (
                    <tr key={log.id} className="hover:bg-zinc-800/50 transition-colors">
                      <td className="px-4 py-3 font-mono text-xs text-violet-400">{log.tool_used}</td>
                      <td className="px-4 py-3 text-zinc-500">
                        {formatDistanceToNow(new Date(log.timestamp), { addSuffix: true })}
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                            STATUS_BADGE[log.approval_status ?? "completed"] ?? "bg-zinc-700 text-zinc-400"
                          }`}
                        >
                          {log.approval_status ?? "done"}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
