"use client";

import { useEffect, useState } from "react";
import {
  getAgentConfig,
  updateAgentConfig,
  type AgentConfig,
} from "@/lib/api";
import { Loader2, Save } from "lucide-react";

const TOOLS: { key: string; label: string; description: string }[] = [
  { key: "read_gmail", label: "Read Gmail", description: "Read unread emails from inbox" },
  { key: "send_email", label: "Send Email", description: "Draft and send emails (always requires approval)" },
  { key: "search_web", label: "Search Web", description: "DuckDuckGo search queries" },
  { key: "read_webpage", label: "Read Webpage", description: "Extract clean text from a URL" },
  { key: "create_notion_task", label: "Create Notion Task", description: "Create tasks in Notion database" },
  { key: "log_to_hubspot", label: "Log to HubSpot", description: "Create contacts and log activity notes" },
  { key: "send_telegram_message", label: "Send Telegram Message", description: "Send messages to your Telegram" },
];

const APPROVAL_ACTIONS = [
  { key: "send_email", label: "Sending emails" },
  { key: "create_notion_task", label: "Creating Notion tasks" },
  { key: "log_to_hubspot", label: "Logging to HubSpot" },
];

const SCHEDULES = [
  { value: "manual", label: "Manual only" },
  { value: "30min", label: "Every 30 minutes" },
  { value: "1hour", label: "Every hour" },
  { value: "4hours", label: "Every 4 hours" },
];

export default function ConfigPage() {
  const [config, setConfig] = useState<AgentConfig | null>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    getAgentConfig().then(setConfig).catch(() => {});
  }, []);

  const handleSave = async () => {
    if (!config) return;
    setSaving(true);
    try {
      const updated = await updateAgentConfig(config);
      setConfig(updated);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } finally {
      setSaving(false);
    }
  };

  if (!config) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-zinc-500" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-zinc-100">Agent Configuration</h1>
        <p className="text-sm text-zinc-500">Customise how Toora behaves for your business.</p>
      </div>

      {/* System Prompt */}
      <section className="space-y-3">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-zinc-500">System Prompt</h2>
        <textarea
          className="w-full rounded-lg border border-zinc-700 bg-zinc-900 px-4 py-3 text-sm text-zinc-100 placeholder:text-zinc-600 focus:border-violet-500 focus:outline-none min-h-32 resize-none"
          placeholder="Describe your business and give the agent custom instructions…"
          value={config.system_prompt ?? ""}
          onChange={(e) => setConfig({ ...config, system_prompt: e.target.value })}
        />
      </section>

      {/* Schedule */}
      <section className="space-y-3">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-zinc-500">Run Schedule</h2>
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
          {SCHEDULES.map((s) => (
            <button
              key={s.value}
              onClick={() => setConfig({ ...config, schedule: s.value })}
              className={`rounded-lg border px-3 py-2 text-sm transition-colors ${
                config.schedule === s.value
                  ? "border-violet-500 bg-violet-600/20 text-violet-400"
                  : "border-zinc-700 bg-zinc-900 text-zinc-400 hover:border-zinc-600"
              }`}
            >
              {s.label}
            </button>
          ))}
        </div>
      </section>

      {/* Tool Toggles */}
      <section className="space-y-3">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-zinc-500">Enabled Tools</h2>
        <div className="space-y-2">
          {TOOLS.map((t) => (
            <div
              key={t.key}
              className="flex items-center justify-between rounded-lg border border-zinc-800 bg-zinc-900 px-4 py-3"
            >
              <div>
                <p className="text-sm font-medium text-zinc-200">{t.label}</p>
                <p className="text-xs text-zinc-500">{t.description}</p>
              </div>
              <button
                role="switch"
                aria-checked={config.enabled_tools[t.key] ?? false}
                onClick={() =>
                  setConfig({
                    ...config,
                    enabled_tools: {
                      ...config.enabled_tools,
                      [t.key]: !(config.enabled_tools[t.key] ?? false),
                    },
                  })
                }
                className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors ${
                  config.enabled_tools[t.key] ? "bg-violet-600" : "bg-zinc-700"
                }`}
              >
                <span
                  className={`inline-block h-5 w-5 transform rounded-full bg-white shadow transition-transform ${
                    config.enabled_tools[t.key] ? "translate-x-5" : "translate-x-0"
                  }`}
                />
              </button>
            </div>
          ))}
        </div>
      </section>

      {/* Approval Rules */}
      <section className="space-y-3">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-zinc-500">Approval Rules</h2>
        <p className="text-xs text-zinc-600">
          Require Telegram approval before the agent executes these actions.
        </p>
        <div className="space-y-2">
          {APPROVAL_ACTIONS.map((a) => (
            <div
              key={a.key}
              className="flex items-center justify-between rounded-lg border border-zinc-800 bg-zinc-900 px-4 py-3"
            >
              <p className="text-sm text-zinc-200">{a.label}</p>
              <button
                role="switch"
                aria-checked={config.approval_rules[a.key] ?? false}
                onClick={() =>
                  setConfig({
                    ...config,
                    approval_rules: {
                      ...config.approval_rules,
                      [a.key]: !(config.approval_rules[a.key] ?? false),
                    },
                  })
                }
                className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors ${
                  config.approval_rules[a.key] ? "bg-violet-600" : "bg-zinc-700"
                }`}
              >
                <span
                  className={`inline-block h-5 w-5 transform rounded-full bg-white shadow transition-transform ${
                    config.approval_rules[a.key] ? "translate-x-5" : "translate-x-0"
                  }`}
                />
              </button>
            </div>
          ))}
        </div>
      </section>

      <button
        onClick={handleSave}
        disabled={saving}
        className="flex w-full items-center justify-center gap-2 rounded-lg bg-violet-600 px-4 py-3 text-sm font-medium text-white hover:bg-violet-500 disabled:opacity-50 transition-colors"
      >
        {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
        {saved ? "Saved!" : "Save Configuration"}
      </button>
    </div>
  );
}
