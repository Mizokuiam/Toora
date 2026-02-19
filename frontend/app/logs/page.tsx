"use client";

import { useEffect, useState } from "react";
import { getLogs, getLog, type ActionLog, type PaginatedLogs } from "@/lib/api";
import { ChevronLeft, ChevronRight, X } from "lucide-react";
import { formatDistanceToNow } from "date-fns";

const TOOLS = [
  "read_gmail",
  "send_email",
  "search_web",
  "read_webpage",
  "create_notion_task",
  "log_to_hubspot",
  "send_telegram_message",
];

const STATUS_BADGE: Record<string, string> = {
  approved: "bg-emerald-500/10 text-emerald-400",
  rejected: "bg-red-500/10 text-red-400",
  pending: "bg-amber-500/10 text-amber-400",
  expired: "bg-zinc-700 text-zinc-400",
};

export default function LogsPage() {
  const [data, setData] = useState<PaginatedLogs | null>(null);
  const [page, setPage] = useState(1);
  const [filterTool, setFilterTool] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [selectedLog, setSelectedLog] = useState<ActionLog | null>(null);

  const load = () => {
    getLogs({
      page,
      per_page: 25,
      tool: filterTool || undefined,
      status: filterStatus || undefined,
    })
      .then(setData)
      .catch(() => {});
  };

  useEffect(() => { load(); }, [page, filterTool, filterStatus]);

  const handleRowClick = async (id: number) => {
    const log = await getLog(id).catch(() => null);
    if (log) setSelectedLog(log);
  };

  const exportCsv = () => {
    if (!data) return;
    const rows = [
      ["ID", "Tool", "Timestamp", "Approval Status"],
      ...data.items.map((l) => [l.id, l.tool_used, l.timestamp, l.approval_status ?? "—"]),
    ];
    const csv = rows.map((r) => r.join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "toora_logs.csv";
    a.click();
    URL.revokeObjectURL(url);
  };

  const totalPages = data ? Math.ceil(data.total / data.per_page) : 1;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-100">Action Log</h1>
          <p className="text-sm text-zinc-500">{data?.total ?? 0} total entries</p>
        </div>
        <button
          onClick={exportCsv}
          className="rounded-lg border border-zinc-700 px-3 py-2 text-sm text-zinc-400 hover:bg-zinc-800 transition-colors"
        >
          Export CSV
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-3">
        <select
          value={filterTool}
          onChange={(e) => { setFilterTool(e.target.value); setPage(1); }}
          className="rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-300 focus:outline-none focus:border-violet-500"
        >
          <option value="">All tools</option>
          {TOOLS.map((t) => <option key={t} value={t}>{t}</option>)}
        </select>
        <select
          value={filterStatus}
          onChange={(e) => { setFilterStatus(e.target.value); setPage(1); }}
          className="rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-300 focus:outline-none focus:border-violet-500"
        >
          <option value="">All statuses</option>
          <option value="approved">Approved</option>
          <option value="rejected">Rejected</option>
          <option value="pending">Pending</option>
          <option value="expired">Expired</option>
        </select>
      </div>

      {/* Table */}
      <div className="rounded-xl border border-zinc-800 bg-zinc-900 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-zinc-800">
              <th className="px-4 py-3 text-left text-xs font-medium text-zinc-500">Tool</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-zinc-500">Time</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-zinc-500">Input</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-zinc-500">Approval</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800">
            {data?.items.map((log) => (
              <tr
                key={log.id}
                onClick={() => handleRowClick(log.id)}
                className="cursor-pointer hover:bg-zinc-800/50 transition-colors"
              >
                <td className="px-4 py-3 font-mono text-xs text-violet-400">{log.tool_used}</td>
                <td className="px-4 py-3 text-zinc-500">
                  {formatDistanceToNow(new Date(log.timestamp), { addSuffix: true })}
                </td>
                <td className="px-4 py-3 text-zinc-400 max-w-xs truncate">
                  {JSON.stringify(log.input_data).slice(0, 60)}…
                </td>
                <td className="px-4 py-3">
                  {log.approval_status ? (
                    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_BADGE[log.approval_status] ?? "bg-zinc-700 text-zinc-400"}`}>
                      {log.approval_status}
                    </span>
                  ) : (
                    <span className="text-zinc-600">—</span>
                  )}
                </td>
              </tr>
            )) ?? (
              <tr>
                <td colSpan={4} className="py-12 text-center text-zinc-600">No log entries found</td>
              </tr>
            )}
          </tbody>
        </table>

        {/* Pagination */}
        <div className="flex items-center justify-between border-t border-zinc-800 px-4 py-3">
          <span className="text-xs text-zinc-600">
            Page {page} of {totalPages}
          </span>
          <div className="flex gap-1">
            <button
              disabled={page <= 1}
              onClick={() => setPage((p) => p - 1)}
              className="rounded p-1 text-zinc-400 hover:bg-zinc-800 disabled:opacity-30"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <button
              disabled={page >= totalPages}
              onClick={() => setPage((p) => p + 1)}
              className="rounded p-1 text-zinc-400 hover:bg-zinc-800 disabled:opacity-30"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Slide-over detail */}
      {selectedLog && (
        <div className="fixed inset-0 z-50 flex" onClick={() => setSelectedLog(null)}>
          <div className="ml-auto h-full w-full max-w-lg overflow-y-auto bg-zinc-950 border-l border-zinc-800 p-6 space-y-4" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-zinc-100">Log #{selectedLog.id}</h2>
              <button onClick={() => setSelectedLog(null)} className="text-zinc-500 hover:text-zinc-300">
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="space-y-1">
              <p className="text-xs text-zinc-500">Tool</p>
              <p className="font-mono text-sm text-violet-400">{selectedLog.tool_used}</p>
            </div>
            <div className="space-y-1">
              <p className="text-xs text-zinc-500">Input</p>
              <pre className="rounded-lg bg-zinc-900 p-3 text-xs text-zinc-300 overflow-auto">
                {JSON.stringify(selectedLog.input_data, null, 2)}
              </pre>
            </div>
            <div className="space-y-1">
              <p className="text-xs text-zinc-500">Output</p>
              <pre className="rounded-lg bg-zinc-900 p-3 text-xs text-zinc-300 overflow-auto">
                {JSON.stringify(selectedLog.output_data, null, 2)}
              </pre>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
