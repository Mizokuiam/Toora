"use client";

import { useState } from "react";
import {
  saveCredentials,
  testConnection,
  disconnectIntegration,
  registerTelegramWebhook,
  type Integration,
} from "@/lib/api";
import { cn } from "@/lib/utils";
import { ChevronDown, ChevronUp, Loader2 } from "lucide-react";

interface Field {
  key: string;
  label: string;
  type?: "text" | "password";
  hint?: string;
}

interface IntegrationCardProps {
  platform: string;
  label: string;
  description: string;
  icon: React.ReactNode;
  fields: Field[];
  integration?: Integration;
  onSaved: () => void;
}

export function IntegrationCard({
  platform,
  label,
  description,
  icon,
  fields,
  integration,
  onSaved,
}: IntegrationCardProps) {
  const [expanded, setExpanded] = useState(false);
  const [values, setValues] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);
  const [registering, setRegistering] = useState(false);
  const [registerResult, setRegisterResult] = useState<string | null>(null);
  const [registerSuccess, setRegisterSuccess] = useState(false);

  const connected = integration?.status === "connected";

  const handleSave = async () => {
    setSaving(true);
    try {
      await saveCredentials(platform, values);
      onSaved();
      setExpanded(false);
    } catch (e) {
      console.error(e);
    } finally {
      setSaving(false);
    }
  };

  const handleTest = async () => {
    setTesting(true);
    setTestResult(null);
    setRegisterResult(null);
    try {
      const r = await testConnection(platform);
      setTestResult(r);
    } catch {
      setTestResult({ success: false, message: "Connection test failed." });
    } finally {
      setTesting(false);
    }
  };

  const handleDisconnect = async () => {
    await disconnectIntegration(platform);
    onSaved();
  };

  const handleRegisterWebhook = async () => {
    if (platform !== "telegram" || !connected) return;
    setRegistering(true);
    setRegisterResult(null);
    setRegisterSuccess(false);
    setTestResult(null);
    try {
      const r = await registerTelegramWebhook();
      if ("message" in r) {
        setRegisterResult(r.message);
        setRegisterSuccess(true);
      } else {
        setRegisterResult(r.error ?? "Unknown error");
        setRegisterSuccess(false);
      }
    } catch (e) {
      setRegisterResult((e as Error).message);
      setRegisterSuccess(false);
    } finally {
      setRegistering(false);
    }
  };

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-5">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-zinc-800">
            {icon}
          </div>
          <div>
            <h3 className="font-semibold text-zinc-100">{label}</h3>
            <p className="text-sm text-zinc-500">{description}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span
            className={cn(
              "rounded-full px-2.5 py-0.5 text-xs font-medium",
              connected
                ? "bg-emerald-500/10 text-emerald-400"
                : "bg-zinc-700 text-zinc-400"
            )}
          >
            {connected ? "Connected" : "Not connected"}
          </span>
          <button
            onClick={() => setExpanded((v) => !v)}
            className="rounded-lg p-1.5 text-zinc-500 hover:bg-zinc-800 hover:text-zinc-300 transition-colors"
          >
            {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </button>
        </div>
      </div>

      {connected && integration?.connected_at && (
        <p className="mt-2 text-xs text-zinc-600">
          Last connected {new Date(integration.connected_at).toLocaleString()}
        </p>
      )}

      {expanded && (
        <form
          className="mt-4 space-y-3 border-t border-zinc-800 pt-4"
          onSubmit={(e) => {
            e.preventDefault();
            handleSave();
          }}
        >
          {fields.map((f) => (
            <div key={f.key}>
              <label className="block text-xs font-medium text-zinc-400 mb-1">{f.label}</label>
              <input
                type={f.type ?? "text"}
                value={values[f.key] ?? ""}
                onChange={(e) => setValues((v) => ({ ...v, [f.key]: e.target.value }))}
                className="w-full rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-600 focus:border-violet-500 focus:outline-none"
                placeholder={f.label}
                autoComplete={f.type === "password" ? "current-password" : "off"}
              />
              {f.hint && <p className="mt-1 text-xs text-zinc-600">{f.hint}</p>}
            </div>
          ))}

          {(testResult || registerResult) && (
            <p
              className={cn(
                "rounded-lg px-3 py-2 text-sm",
                testResult
                  ? testResult.success
                    ? "bg-emerald-500/10 text-emerald-400"
                    : "bg-red-500/10 text-red-400"
                  : registerSuccess
                    ? "bg-emerald-500/10 text-emerald-400"
                    : "bg-red-500/10 text-red-400"
              )}
            >
              {testResult?.message ?? registerResult}
            </p>
          )}

          <div className="flex gap-2">
            <button
              type="submit"
              disabled={saving}
              className="flex-1 flex items-center justify-center gap-2 rounded-lg bg-violet-600 px-4 py-2 text-sm font-medium text-white hover:bg-violet-500 disabled:opacity-50 transition-colors"
            >
              {saving && <Loader2 className="h-3 w-3 animate-spin" />}
              Save
            </button>
            <button
              type="button"
              onClick={handleTest}
              disabled={testing || !connected}
              className="flex items-center gap-2 rounded-lg border border-zinc-700 px-4 py-2 text-sm text-zinc-300 hover:bg-zinc-800 disabled:opacity-50 transition-colors"
            >
              {testing && <Loader2 className="h-3 w-3 animate-spin" />}
              Test
            </button>
            {platform === "telegram" && connected && (
              <button
                type="button"
                onClick={handleRegisterWebhook}
                disabled={registering}
                className="flex items-center gap-2 rounded-lg border border-violet-700 px-4 py-2 text-sm text-violet-400 hover:bg-violet-500/10 disabled:opacity-50 transition-colors"
              >
                {registering && <Loader2 className="h-3 w-3 animate-spin" />}
                Register Webhook
              </button>
            )}
            {connected && (
              <button
                type="button"
                onClick={handleDisconnect}
                className="rounded-lg border border-red-900 px-4 py-2 text-sm text-red-400 hover:bg-red-500/10 transition-colors"
              >
                Disconnect
              </button>
            )}
          </div>
        </form>
      )}
    </div>
  );
}
