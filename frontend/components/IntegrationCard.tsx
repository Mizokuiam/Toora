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
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";

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
    <Card>
      <CardContent className="p-5">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className="flex size-10 items-center justify-center rounded-lg bg-muted">
            {icon}
          </div>
          <div>
            <h3 className="font-semibold">{label}</h3>
            <p className="text-sm text-muted-foreground">{description}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Badge
            variant={connected ? "default" : "secondary"}
            className={cn(
              connected && "bg-emerald-500/10 text-emerald-400 border-emerald-500/20 hover:bg-emerald-500/10"
            )}
          >
            {connected ? "Connected" : "Not connected"}
          </Badge>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setExpanded((v) => !v)}
          >
            {expanded ? <ChevronUp className="size-4" /> : <ChevronDown className="size-4" />}
          </Button>
        </div>
      </div>

      {connected && integration?.connected_at && (
        <p className="mt-2 text-xs text-muted-foreground">
          Last connected {new Date(integration.connected_at).toLocaleString()}
        </p>
      )}

      {expanded && (
        <form
          className="mt-4 space-y-3 border-t border-border pt-4"
          onSubmit={(e) => {
            e.preventDefault();
            handleSave();
          }}
        >
          {fields.map((f) => (
            <div key={f.key}>
              <label className="mb-1 block text-xs font-medium text-muted-foreground">{f.label}</label>
              <Input
                type={f.type ?? "text"}
                value={values[f.key] ?? ""}
                onChange={(e) => setValues((v) => ({ ...v, [f.key]: e.target.value }))}
                placeholder={f.label}
                autoComplete={f.type === "password" ? "current-password" : "off"}
              />
              {f.hint && <p className="mt-1 text-xs text-muted-foreground">{f.hint}</p>}
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

          <div className="flex flex-wrap gap-2">
            <Button type="submit" disabled={saving} className="flex-1 min-w-24">
              {saving && <Loader2 className="size-3 animate-spin" />}
              Save
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={handleTest}
              disabled={testing || !connected}
            >
              {testing && <Loader2 className="size-3 animate-spin" />}
              Test
            </Button>
            {platform === "telegram" && connected && (
              <Button
                type="button"
                variant="outline"
                onClick={handleRegisterWebhook}
                disabled={registering}
                className="border-primary/50 text-primary"
              >
                {registering && <Loader2 className="size-3 animate-spin" />}
                Register Webhook
              </Button>
            )}
            {connected && (
              <Button
                type="button"
                variant="outline"
                onClick={handleDisconnect}
                className="border-destructive/50 text-destructive hover:bg-destructive/10"
              >
                Disconnect
              </Button>
            )}
          </div>
        </form>
      )}
      </CardContent>
    </Card>
  );
}
