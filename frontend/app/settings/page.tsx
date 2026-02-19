"use client";

import { useState } from "react";
import { MessageCircle, AlertTriangle } from "lucide-react";

export default function SettingsPage() {
  const [showClearDialog, setShowClearDialog] = useState<string | null>(null);

  const dangerous = [
    { id: "clear-logs", label: "Clear All Logs", description: "Permanently delete all action log entries." },
    { id: "disconnect-all", label: "Disconnect All Integrations", description: "Remove all saved credentials." },
    { id: "reset-agent", label: "Reset Agent", description: "Clear agent config and runs history." },
  ];

  const handleDangerous = async (id: string) => {
    // Placeholder — connect to backend danger-zone endpoints when needed
    console.warn("Danger zone action:", id);
    setShowClearDialog(null);
  };

  return (
    <div className="mx-auto max-w-2xl space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-zinc-100">Settings</h1>
        <p className="text-sm text-zinc-500">Global preferences and account management.</p>
      </div>

      {/* Communication Channel */}
      <section className="space-y-3">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-zinc-500">
          Communication Channel
        </h2>
        <div className="space-y-2">
          <div className="flex items-center justify-between rounded-lg border border-violet-500/40 bg-violet-600/10 px-4 py-3">
            <div className="flex items-center gap-3">
              <MessageCircle className="h-5 w-5 text-blue-400" />
              <div>
                <p className="text-sm font-medium text-zinc-200">Telegram</p>
                <p className="text-xs text-zinc-500">Active approval and notification channel</p>
              </div>
            </div>
            <span className="rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-xs text-emerald-400">
              Active
            </span>
          </div>
          {["Slack", "WhatsApp", "Email Digest"].map((ch) => (
            <div
              key={ch}
              className="flex items-center justify-between rounded-lg border border-zinc-800 bg-zinc-900 px-4 py-3 opacity-50"
            >
              <p className="text-sm text-zinc-400">{ch}</p>
              <span className="rounded-full bg-zinc-700 px-2.5 py-0.5 text-xs text-zinc-500">
                Coming soon
              </span>
            </div>
          ))}
        </div>
      </section>

      {/* Notification Preferences */}
      <section className="space-y-3">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-zinc-500">
          Notification Preferences
        </h2>
        <div className="space-y-2">
          {[
            { label: "Every action", desc: "Get notified for all tool executions" },
            { label: "Approvals only", desc: "Only notify when approval is required" },
            { label: "Errors only", desc: "Only notify on failures" },
          ].map((opt, i) => (
            <label
              key={opt.label}
              className="flex cursor-pointer items-center gap-3 rounded-lg border border-zinc-800 bg-zinc-900 px-4 py-3 has-[:checked]:border-violet-500/40 has-[:checked]:bg-violet-600/10"
            >
              <input type="radio" name="notif" defaultChecked={i === 1} className="accent-violet-500" />
              <div>
                <p className="text-sm font-medium text-zinc-200">{opt.label}</p>
                <p className="text-xs text-zinc-500">{opt.desc}</p>
              </div>
            </label>
          ))}
        </div>
      </section>

      {/* Danger Zone */}
      <section className="space-y-3">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-red-500">
          Danger Zone
        </h2>
        <div className="rounded-xl border border-red-900/50 bg-red-950/20 p-4 space-y-3">
          {dangerous.map((d) => (
            <div key={d.id} className="flex items-center justify-between gap-4">
              <div>
                <p className="text-sm font-medium text-zinc-200">{d.label}</p>
                <p className="text-xs text-zinc-500">{d.description}</p>
              </div>
              <button
                onClick={() => setShowClearDialog(d.id)}
                className="shrink-0 rounded-lg border border-red-800 px-3 py-1.5 text-xs text-red-400 hover:bg-red-500/10 transition-colors"
              >
                {d.label.split(" ")[0]}
              </button>
            </div>
          ))}
        </div>
      </section>

      {/* Confirmation Dialog */}
      {showClearDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
          <div className="w-full max-w-md rounded-xl border border-zinc-800 bg-zinc-950 p-6 space-y-4">
            <div className="flex items-center gap-3">
              <AlertTriangle className="h-5 w-5 text-red-400" />
              <h3 className="text-lg font-semibold text-zinc-100">Are you sure?</h3>
            </div>
            <p className="text-sm text-zinc-400">
              This action is irreversible. All associated data will be permanently deleted.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setShowClearDialog(null)}
                className="flex-1 rounded-lg border border-zinc-700 py-2 text-sm text-zinc-400 hover:bg-zinc-800"
              >
                Cancel
              </button>
              <button
                onClick={() => handleDangerous(showClearDialog)}
                className="flex-1 rounded-lg bg-red-700 py-2 text-sm font-medium text-white hover:bg-red-600"
              >
                Confirm
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
