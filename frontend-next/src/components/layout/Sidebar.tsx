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
import { AnswerlyLogo } from "@/components/shared/AnswerlyLogo";

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
  { href: "/admin", label: "Admin Overview", icon: Shield },
  { href: "/admin/companies", label: "Companies", icon: Building2 },
  { href: "/admin/conversations", label: "Global Conversations", icon: MessageSquareText },
  { href: "/admin/bots", label: "Bots", icon: Bot },
  { href: "/admin/errors", label: "Errors", icon: Shield },
  { href: "/admin/stats", label: "Stats", icon: LayoutDashboard },
  { href: "/admin/observability", label: "AI Settings", icon: Activity },
];

export function Sidebar({ items, embedded = false }: { items: NavItem[]; embedded?: boolean }) {
  const pathname = usePathname();
  const user = useAuthStore((state) => state.currentUser);
  const platformMode = items.some((item) => item.href.startsWith("/admin"));

  return (
    <aside
      className={cn(
        "w-64 shrink-0 bg-[#0B132B] text-slate-300 shadow-[4px_0_24px_rgba(0,0,0,0.05)]",
        embedded ? "flex min-h-full flex-col" : "hidden min-h-screen lg:flex lg:flex-col",
      )}
    >
      <div className="px-5 py-8">
        <Link href={platformMode ? "/admin" : "/dashboard"} className="flex items-center">
          <AnswerlyLogo variant="light" className="h-8" />
        </Link>
      </div>
      <nav className="flex flex-1 flex-col gap-1.5 px-3">
        {items.map((item) => {
          const Icon = item.icon;
          const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium transition-all duration-200",
                active
                  ? "bg-indigo-600/10 text-indigo-400 border border-indigo-500/20 shadow-[inset_0px_0px_12px_rgba(79,70,229,0.1)]"
                  : "border border-transparent text-slate-400 hover:bg-slate-800/50 hover:text-slate-200",
              )}
            >
              <Icon className={cn("size-[18px]", active ? "text-indigo-400" : "text-slate-500")} aria-hidden="true" />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>
      <div className="flex flex-col gap-3 p-4">
        <div className="rounded-xl border border-slate-800 bg-[#0f172a] p-3 shadow-md transition-colors hover:border-slate-700 cursor-pointer">
          <div className="flex items-center gap-3">
            <div className="flex size-9 items-center justify-center rounded-lg bg-slate-800 text-sm font-semibold text-slate-200 ring-1 ring-slate-700">
              <Building2 className="size-4" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-slate-200">{user?.company_name || user?.username || "Acme Support Co."}</p>
              <p className="text-xs text-indigo-400 font-medium">{platformMode ? "Platform Owner" : "Enterprise Plan"}</p>
            </div>
            <ChevronDown className="size-4 text-slate-500" aria-hidden="true" />
          </div>
        </div>
        <div className="rounded-xl border border-slate-800 bg-[#0f172a] p-4 text-xs shadow-md">
          <div className="mb-2 flex items-center justify-between text-slate-300 font-medium">
            <span>{platformMode ? "Platform usage" : "Monthly message usage"}</span>
          </div>
          <div className="mb-2 flex items-end justify-between font-semibold">
            <div className="text-sm">
              <span className="text-slate-200">42,680</span>
              <span className="text-slate-500"> / 100,000</span>
            </div>
            <span className="text-slate-400 text-xs font-medium">42%</span>
          </div>
          <div className="h-1.5 overflow-hidden rounded-full bg-slate-800">
            <div className="h-full w-[42%] rounded-full bg-indigo-500" />
          </div>
          <div className="mt-3 text-[11px] text-slate-500">
            Resets in 12 days
          </div>
        </div>
      </div>
    </aside>
  );
}
