"use client";

import { useEffect, useState } from "react";
import { getApprovals, type Approval } from "@/lib/api";
import { ApprovalCard } from "@/components/ApprovalCard";
import { useAgentWebSocket } from "@/lib/ws";
import { CheckCircle2, XCircle, Clock } from "lucide-react";
import { formatDistanceToNow } from "date-fns";

const RESOLVED_ICON: Record<string, React.ReactNode> = {
  approved: <CheckCircle2 className="h-4 w-4 text-emerald-400" />,
  rejected: <XCircle className="h-4 w-4 text-red-400" />,
  expired: <Clock className="h-4 w-4 text-zinc-500" />,
};

export default function ApprovalsPage() {
  const [pending, setPending] = useState<Approval[]>([]);
  const [resolved, setResolved] = useState<Approval[]>([]);

  const load = () => {
    getApprovals("pending").then(setPending).catch(() => {});
    getApprovals()
      .then((all) => setResolved(all.filter((a) => a.status !== "pending")))
      .catch(() => {});
  };

  useEffect(() => { load(); }, []);

  useAgentWebSocket((msg) => {
    if (msg.type === "approval_resolved") load();
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Approvals</h1>
        <p className="text-sm text-muted-foreground">
          Approve or reject agent actions. You can also respond from Telegram.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Pending */}
        <div className="space-y-4">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-zinc-500">
            Pending ({pending.length})
          </h2>
          {pending.length === 0 ? (
            <div className="flex h-32 items-center justify-center rounded-xl border border-zinc-800 text-sm text-zinc-600">
              No pending approvals
            </div>
          ) : (
            pending.map((a) => (
              <ApprovalCard key={a.id} approval={a} onResolved={load} />
            ))
          )}
        </div>

        {/* Resolved */}
        <div className="space-y-4">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-zinc-500">
            Resolved ({resolved.length})
          </h2>
          <div className="space-y-2 rounded-xl border border-zinc-800 bg-zinc-900 overflow-hidden">
            {resolved.length === 0 ? (
              <div className="flex h-32 items-center justify-center text-sm text-zinc-600">
                No resolved approvals yet
              </div>
            ) : (
              resolved.map((a) => (
                <div
                  key={a.id}
                  className="flex items-start gap-3 border-b border-zinc-800 last:border-0 px-4 py-3"
                >
                  <div className="mt-0.5">{RESOLVED_ICON[a.status] ?? null}</div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-zinc-300 truncate">{a.action_description}</p>
                    <p className="text-xs text-zinc-600">
                      {a.resolved_at
                        ? formatDistanceToNow(new Date(a.resolved_at), { addSuffix: true })
                        : a.status}
                    </p>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
