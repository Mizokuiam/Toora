"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart3,
  Bot,
  CheckSquare,
  ClipboardList,
  Plug,
  Settings,
  HelpCircle,
  Search,
  ChevronUp,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Separator } from "@/components/ui/separator";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
  DropdownMenuItem,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";

const NAV_GROUPS = [
  {
    label: "Home",
    items: [
      { href: "/", label: "Dashboard", icon: BarChart3 },
    ],
  },
  {
    label: "Agent",
    items: [
      { href: "/config", label: "Agent Config", icon: Bot },
      { href: "/logs", label: "Action Log", icon: ClipboardList },
      { href: "/approvals", label: "Approvals", icon: CheckSquare },
    ],
  },
  {
    label: "Integrations",
    items: [
      { href: "/connections", label: "Connections", icon: Plug },
    ],
  },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed inset-y-0 left-0 z-50 flex w-56 flex-col border-r border-border bg-card">
      {/* Logo */}
      <div className="flex h-14 items-center gap-2.5 border-b border-border px-4">
        <div className="flex size-8 items-center justify-center rounded-lg bg-primary">
          <Bot className="size-4 text-primary-foreground" />
        </div>
        <span className="text-base font-semibold tracking-tight">Toora</span>
      </div>

      {/* Nav sections */}
      <nav className="flex-1 space-y-6 overflow-y-auto p-3">
        {NAV_GROUPS.map((group) => (
          <div key={group.label}>
            <p className="mb-2 px-3 text-xs font-medium text-muted-foreground">
              {group.label}
            </p>
            <div className="space-y-0.5">
              {group.items.map(({ href, label, icon: Icon }) => {
                const active = pathname === href;
                return (
                  <Link
                    key={href}
                    href={href}
                    className={cn(
                      "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                      active
                        ? "bg-sidebar-accent text-sidebar-accent-foreground"
                        : "text-muted-foreground hover:bg-sidebar-accent/50 hover:text-foreground"
                    )}
                  >
                    <Icon className="size-4 shrink-0" />
                    {label}
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      <Separator />

      {/* Quick links */}
      <div className="space-y-0.5 p-3">
        <Button
          variant="ghost"
          size="sm"
          className="w-full justify-start gap-3 text-muted-foreground"
          disabled
        >
          <Search className="size-4" />
          Search
        </Button>
        <Button
          variant="ghost"
          size="sm"
          className="w-full justify-start gap-3 text-muted-foreground"
          asChild
        >
          <Link href="/settings">
            <Settings className="size-4" />
            Settings
          </Link>
        </Button>
        <Button
          variant="ghost"
          size="sm"
          className="w-full justify-start gap-3 text-muted-foreground"
          asChild
        >
          <a
            href="https://github.com/Mizokuiam/Toora"
            target="_blank"
            rel="noopener noreferrer"
          >
            <HelpCircle className="size-4" />
            Get Help
          </a>
        </Button>
      </div>

      {/* User profile */}
      <div className="border-t border-border p-3">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              className="w-full justify-start gap-3 px-3 py-2 h-auto"
            >
              <Avatar className="size-8">
                <AvatarFallback className="bg-primary/10 text-primary text-xs">
                  Toora
                </AvatarFallback>
              </Avatar>
              <div className="flex flex-1 flex-col items-start text-left">
                <span className="text-sm font-medium">Toora</span>
                <span className="text-xs text-muted-foreground">Dashboard</span>
              </div>
              <ChevronUp className="size-4 -rotate-180" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent side="top" align="start" className="w-56">
            <DropdownMenuItem asChild>
              <Link href="/settings">Settings</Link>
            </DropdownMenuItem>
            <DropdownMenuItem asChild>
              <a
                href="https://github.com/Mizokuiam/Toora"
                target="_blank"
                rel="noopener noreferrer"
              >
                Get Help
              </a>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </aside>
  );
}
