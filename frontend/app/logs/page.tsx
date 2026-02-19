"use client";

import { useEffect, useState } from "react";
import { getLogs, getLog, type ActionLog, type PaginatedLogs } from "@/lib/api";
import { ChevronLeft, ChevronRight, X } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

const TOOLS = [
  "read_gmail",
  "send_email",
  "search_web",
  "read_webpage",
  "create_notion_task",
  "log_to_hubspot",
  "send_telegram_message",
  "read_calendar",
  "create_calendar_event",
];

const STATUS_BADGE: Record<string, string> = {
  approved: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
  rejected: "bg-red-500/10 text-red-400 border-red-500/20",
  pending: "bg-amber-500/10 text-amber-400 border-amber-500/20",
  expired: "bg-muted text-muted-foreground",
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

  useEffect(() => {
    load();
  }, [page, filterTool, filterStatus]);

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
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Action Log</h1>
          <p className="text-sm text-muted-foreground">{data?.total ?? 0} total entries</p>
        </div>
        <Button variant="outline" onClick={exportCsv}>
          Export CSV
        </Button>
      </div>

      <Card>
        <CardHeader>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            <select
              value={filterTool}
              onChange={(e) => {
                setFilterTool(e.target.value);
                setPage(1);
              }}
              className="h-9 rounded-md border border-input bg-background px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            >
              <option value="">All tools</option>
              {TOOLS.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
            <select
              value={filterStatus}
              onChange={(e) => {
                setFilterStatus(e.target.value);
                setPage(1);
              }}
              className="h-9 rounded-md border border-input bg-background px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            >
              <option value="">All statuses</option>
              <option value="approved">Approved</option>
              <option value="rejected">Rejected</option>
              <option value="pending">Pending</option>
              <option value="expired">Expired</option>
            </select>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Tool</TableHead>
                <TableHead>Time</TableHead>
                <TableHead>Input</TableHead>
                <TableHead>Approval</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data?.items.map((log) => (
                <TableRow
                  key={log.id}
                  onClick={() => handleRowClick(log.id)}
                  className="cursor-pointer"
                >
                  <TableCell className="font-mono text-xs text-primary">
                    {log.tool_used}
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {formatDistanceToNow(new Date(log.timestamp), { addSuffix: true })}
                  </TableCell>
                  <TableCell className="max-w-xs truncate text-muted-foreground">
                    {JSON.stringify(log.input_data).slice(0, 60)}…
                  </TableCell>
                  <TableCell>
                    {log.approval_status ? (
                      <Badge
                        variant="secondary"
                        className={
                          STATUS_BADGE[log.approval_status] ?? "bg-muted text-muted-foreground"
                        }
                      >
                        {log.approval_status}
                      </Badge>
                    ) : (
                      <span className="text-muted-foreground">—</span>
                    )}
                  </TableCell>
                </TableRow>
              )) ?? (
                <TableRow>
                  <TableCell colSpan={4} className="py-12 text-center text-muted-foreground">
                    No log entries found
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>

          <div className="flex items-center justify-between border-t border-border px-4 py-3">
            <span className="text-sm text-muted-foreground">
              Page {page} of {totalPages}
            </span>
            <div className="flex gap-1">
              <Button
                variant="ghost"
                size="icon"
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
              >
                <ChevronLeft className="size-4" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => p + 1)}
              >
                <ChevronRight className="size-4" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {selectedLog && (
        <div
          className="fixed inset-0 z-50 flex"
          onClick={() => setSelectedLog(null)}
        >
          <div
            className="ml-auto flex h-full w-full max-w-lg flex-col overflow-y-auto border-l border-border bg-background p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">Log #{selectedLog.id}</h2>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setSelectedLog(null)}
              >
                <X className="size-5" />
              </Button>
            </div>
            <div className="mt-4 space-y-4">
              <div>
                <p className="text-xs font-medium text-muted-foreground">Tool</p>
                <p className="font-mono text-sm text-primary">{selectedLog.tool_used}</p>
              </div>
              <div>
                <p className="text-xs font-medium text-muted-foreground">Input</p>
                <pre className="mt-1 overflow-auto rounded-lg border bg-muted/30 p-3 text-xs">
                  {JSON.stringify(selectedLog.input_data, null, 2)}
                </pre>
              </div>
              <div>
                <p className="text-xs font-medium text-muted-foreground">Output</p>
                <pre className="mt-1 overflow-auto rounded-lg border bg-muted/30 p-3 text-xs">
                  {JSON.stringify(selectedLog.output_data, null, 2)}
                </pre>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
