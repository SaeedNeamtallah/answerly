"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  Bot,
  Building2,
  ChevronDown,
  FolderKanban,
  LayoutDashboard,
  MessageCircle,
  MessageSquareText,
  Rocket,
  Settings2,
  Shield,
  UserRound,
} from "lucide-react";

import { cn } from "@/lib/utils/cn";
import { useAuthStore } from "@/store/auth-store";

export interface NavItem {
  href: string;
  label: string;
  icon: typeof LayoutDashboard;
}

export const companyNav: NavItem[] = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/onboarding", label: "Onboarding", icon: Rocket },
  { href: "/knowledge-bases", label: "Knowledge Bases", icon: FolderKanban },
  { href: "/smart-chat", label: "Smart Chat", icon: MessageCircle },
  { href: "/telegram-bots", label: "Telegram Bots", icon: Bot },
  { href: "/conversations", label: "Conversations", icon: MessageSquareText },
  { href: "/ai-settings", label: "AI Settings", icon: Settings2 },
  { href: "/account", label: "Account", icon: UserRound },
];

export const adminNav: NavItem[] = [
  { href: "/admin", label: "Overview", icon: Shield },
  { href: "/admin/companies", label: "Companies", icon: Building2 },
  { href: "/admin/conversations", label: "Conversations", icon: MessageSquareText },
  { href: "/admin/bots", label: "Bots", icon: Bot },
  { href: "/admin/errors", label: "Errors", icon: Shield },
  { href: "/admin/stats", label: "Stats", icon: LayoutDashboard },
  { href: "/admin/observability", label: "Observability", icon: Activity },
];

export function Sidebar({ items, embedded = false }: { items: NavItem[]; embedded?: boolean }) {
  const pathname = usePathname();
  const user = useAuthStore((state) => state.currentUser);
  const platformMode = items.some((item) => item.href.startsWith("/admin"));

  return (
    <aside
      className={cn(
        "w-72 shrink-0 border-r border-white/10 bg-[#020a18] text-white",
        embedded ? "flex min-h-full flex-col" : "hidden min-h-screen lg:flex lg:flex-col",
      )}
    >
      <div className="px-5 py-6">
        <div className="flex items-center gap-3">
          <div className="grid size-10 grid-cols-3 gap-1 rounded-xl bg-primary/15 p-2 ring-1 ring-primary/25">
            {Array.from({ length: 9 }).map((_, index) => (
              <span key={index} className="rounded-full bg-primary" />
            ))}
          </div>
          <div>
            <p className="text-xl font-semibold leading-none">RAGMind</p>
            <p className="mt-1 text-xs text-white/50">{platformMode ? "Platform console" : "Company workspace"}</p>
          </div>
        </div>
      </div>
      <nav className="flex flex-1 flex-col gap-1 px-3">
        {items.map((item) => {
          const Icon = item.icon;
          const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-xl border px-3 py-2.5 text-sm font-medium transition",
                active
                  ? "border-primary/60 bg-primary/20 text-white shadow-[0_0_0_1px_rgba(255,255,255,0.04)]"
                  : "border-transparent text-white/72 hover:bg-white/8 hover:text-white",
              )}
            >
              <Icon className="size-4" aria-hidden="true" />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>
      <div className="flex flex-col gap-3 p-3">
        <div className="rounded-xl border border-white/10 bg-white/[0.04] p-3">
          <div className="flex items-center gap-3">
            <div className="flex size-9 items-center justify-center rounded-lg bg-white/10 text-sm font-semibold">
              {(user?.company_name || user?.username || "R").slice(0, 2).toUpperCase()}
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium">{user?.company_name || user?.username || "RAGMind"}</p>
              <p className="text-xs text-white/50">{platformMode ? "Platform owner" : "Enterprise plan"}</p>
            </div>
            <ChevronDown className="size-4 text-white/50" aria-hidden="true" />
          </div>
        </div>
        <div className="rounded-xl border border-white/10 bg-white/[0.04] p-3 text-xs text-white/70">
          <div className="mb-2 flex items-center justify-between text-white">
            <span>{platformMode ? "Platform usage" : "Workspace usage"}</span>
            <span>Live</span>
          </div>
          <div className="h-1.5 overflow-hidden rounded-full bg-white/10">
            <div className="h-full w-2/5 rounded-full bg-primary" />
          </div>
        </div>
      </div>
    </aside>
  );
}
