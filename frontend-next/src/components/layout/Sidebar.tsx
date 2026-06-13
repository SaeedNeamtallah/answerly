"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Bot, Building2, FolderKanban, LayoutDashboard, MessageSquareText, Settings2, Shield, UserRound } from "lucide-react";

import { cn } from "@/lib/utils/cn";
import { useAuthStore } from "@/store/auth-store";

export interface NavItem {
  href: string;
  label: string;
  icon: typeof LayoutDashboard;
}

export const companyNav: NavItem[] = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/onboarding", label: "Onboarding", icon: Building2 },
  { href: "/knowledge-bases", label: "Knowledge Bases", icon: FolderKanban },
  { href: "/smart-chat", label: "Smart Chat", icon: MessageSquareText },
  { href: "/telegram-bots", label: "Telegram Bots", icon: Bot },
  { href: "/conversations", label: "Conversations", icon: MessageSquareText },
  { href: "/ai-settings", label: "AI Settings", icon: Settings2 },
  { href: "/account", label: "Account", icon: UserRound },
];

export const adminNav: NavItem[] = [
  { href: "/admin", label: "Overview", icon: Shield },
  { href: "/admin/companies", label: "Companies", icon: Building2 },
  { href: "/signup", label: "Create Account", icon: UserRound },
  { href: "/admin/conversations", label: "Conversations", icon: MessageSquareText },
  { href: "/admin/bots", label: "Bots", icon: Bot },
  { href: "/admin/errors", label: "Errors", icon: Shield },
  { href: "/admin/stats", label: "Stats", icon: LayoutDashboard },
];

export function Sidebar({ items }: { items: NavItem[] }) {
  const pathname = usePathname();
  const currentUser = useAuthStore((state) => state.currentUser);
  const workspaceLabel = currentUser?.company_name || "Workspace";

  return (
    <aside className="hidden w-72 shrink-0 border-r border-slate-200 bg-slate-950 text-slate-100 lg:flex lg:flex-col">
      <div className="border-b border-slate-800 px-6 py-6">
        <p className="text-xs uppercase tracking-[0.2em] text-slate-400">RAGMind</p>
        <h2 className="mt-2 text-xl font-semibold truncate" title={workspaceLabel}>
          {workspaceLabel}
        </h2>
      </div>
      <nav className="flex-1 space-y-1 p-4">
        {items.map((item) => {
          const Icon = item.icon;
          const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium transition",
                active ? "bg-indigo-500/20 text-white" : "text-slate-300 hover:bg-slate-900 hover:text-white",
              )}
            >
              <Icon className="size-4" />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
