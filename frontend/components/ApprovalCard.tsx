"use client";

import { useState } from "react";
import { approveAction, rejectAction, type Approval } from "@/lib/api";
import { Loader2, Check, X } from "lucide-react";
import { formatDistanceToNow } from "date-fns";

interface ApprovalCardProps {
  approval: Approval;
  onResolved: () => void;
}

export function ApprovalCard({ approval, onResolved }: ApprovalCardProps) {
  const [loading, setLoading] = useState<"approve" | "reject" | null>(null);

  const handle = async (action: "approve" | "reject") => {
    setLoading(action);
    try {
      if (action === "approve") await approveAction(approval.id);
      else await rejectAction(approval.id);
      onResolved();
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(null);
    }
  };

  const expires = new Date(approval.expires_at);
  const isExpiringSoon = expires.getTime() - Date.now() < 120_000;

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-5 space-y-3">
      <div className="flex items-start justify-between gap-3">
        <p className="font-medium text-zinc-100">{approval.action_description}</p>
        <span className="shrink-0 text-xs text-zinc-500">
          {formatDistanceToNow(new Date(approval.created_at), { addSuffix: true })}
        </span>
      </div>

      <pre className="rounded-lg bg-zinc-800 p-3 text-xs text-zinc-400 overflow-auto max-h-32">
        {JSON.stringify(approval.full_context, null, 2)}
      </pre>

      {isExpiringSoon && (
        <p className="text-xs text-amber-400">
          Expires {formatDistanceToNow(expires, { addSuffix: true })}
        </p>
      )}

      <div className="flex gap-2">
        <button
          onClick={() => handle("approve")}
          disabled={loading !== null}
          className="flex flex-1 items-center justify-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-500 disabled:opacity-50 transition-colors"
        >
          {loading === "approve" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4" />}
          Approve
        </button>
        <button
          onClick={() => handle("reject")}
          disabled={loading !== null}
          className="flex flex-1 items-center justify-center gap-2 rounded-lg bg-red-700 px-4 py-2 text-sm font-medium text-white hover:bg-red-600 disabled:opacity-50 transition-colors"
        >
          {loading === "reject" ? <Loader2 className="h-4 w-4 animate-spin" /> : <X className="h-4 w-4" />}
          Reject
        </button>
      </div>
    </div>
  );
}
