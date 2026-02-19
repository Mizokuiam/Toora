"use client";

import { useEffect, useState } from "react";
import { listIntegrations, type Integration } from "@/lib/api";
import { IntegrationCard } from "@/components/IntegrationCard";
import { Mail, MessageCircle, Building2, FileText, Calendar } from "lucide-react";

const PLATFORMS = [
  {
    platform: "gmail",
    label: "Gmail",
    description: "Read and send emails via IMAP/SMTP",
    icon: <Mail className="h-5 w-5 text-red-400" />,
    fields: [
      { key: "email", label: "Gmail Address", type: "text" as const },
      {
        key: "app_password",
        label: "App Password",
        type: "password" as const,
        hint: "Generate at myaccount.google.com → Security → App Passwords",
      },
    ],
  },
  {
    platform: "telegram",
    label: "Telegram",
    description: "Receive approvals and send notifications",
    icon: <MessageCircle className="h-5 w-5 text-blue-400" />,
    fields: [
      {
        key: "bot_token",
        label: "Bot Token",
        type: "password" as const,
        hint: "Get from @BotFather on Telegram",
      },
      {
        key: "chat_id",
        label: "Chat ID",
        type: "text" as const,
        hint: "Send /start to your bot then check getUpdates",
      },
    ],
  },
  {
    platform: "google_calendar",
    label: "Google Calendar",
    description: "Read events and create calendar entries",
    icon: <Calendar className="h-5 w-5 text-blue-500" />,
    fields: [
      {
        key: "client_id",
        label: "OAuth Client ID",
        type: "text" as const,
        hint: "From Google Cloud Console → APIs & Services → Credentials",
      },
      {
        key: "client_secret",
        label: "OAuth Client Secret",
        type: "password" as const,
      },
      {
        key: "refresh_token",
        label: "Refresh Token",
        type: "password" as const,
        hint: "Get from OAuth Playground with Calendar scope",
      },
    ],
  },
  {
    platform: "hubspot",
    label: "HubSpot",
    description: "Log contacts and activity notes",
    icon: <Building2 className="h-5 w-5 text-orange-400" />,
    fields: [
      {
        key: "private_app_token",
        label: "Private App Token",
        type: "password" as const,
        hint: "Create a Private App at app.hubspot.com → Settings → Integrations",
      },
    ],
  },
  {
    platform: "notion",
    label: "Notion",
    description: "Create tasks in your Notion workspace",
    icon: <FileText className="h-5 w-5 text-zinc-300" />,
    fields: [
      {
        key: "api_key",
        label: "Notion API Key",
        type: "password" as const,
        hint: "Create at notion.so/my-integrations",
      },
      {
        key: "database_id",
        label: "Database ID",
        type: "text" as const,
        hint: "From the Notion database URL: notion.so/...?v=XXXXX → use the 32-char ID before ?v=",
      },
    ],
  },
];

export default function ConnectionsPage() {
  const [integrations, setIntegrations] = useState<Integration[]>([]);

  const load = () => {
    listIntegrations().then(setIntegrations).catch(() => {});
  };

  useEffect(() => {
    load();
  }, []);

  const getIntegration = (platform: string) =>
    integrations.find((i) => i.platform === platform);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-zinc-100">Connections</h1>
        <p className="text-sm text-zinc-500">
          Manage your integration credentials. All data is encrypted at rest.
        </p>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        {PLATFORMS.map((p) => (
          <IntegrationCard
            key={p.platform}
            {...p}
            integration={getIntegration(p.platform)}
            onSaved={load}
          />
        ))}
      </div>
    </div>
  );
}
