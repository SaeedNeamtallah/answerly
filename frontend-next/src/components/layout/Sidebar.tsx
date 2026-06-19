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
  { href: "/admin/observability", label: "Observability", icon: Activity },
  { href: "/admin/stats", label: "Stats", icon: LayoutDashboard },
  { href: "/admin/settings", label: "Platform Settings", icon: Settings2 },
];

export function Sidebar({ items, embedded = false }: { items: NavItem[]; embedded?: boolean }) {
  const pathname = usePathname();
  const user = useAuthStore((state) => state.currentUser);
  const platformMode = items.some((item) => item.href.startsWith("/admin"));

  const showSecurityNav = !platformMode && user && (user.role === "security_engineer" || user.role === "cybersecurity_engineer" || user.role === "admin" || user.role === "platform_owner");

  const finalItems = [...items];
  if (showSecurityNav && !finalItems.some(i => i.href === "/security")) {
    finalItems.push({ href: "/security", label: "Security Center", icon: Shield });
  }

  return (
    <aside
      className={cn(
        "w-64 shrink-0 bg-white border-r border-slate-200 text-slate-700 shadow-[4px_0_24px_rgba(0,0,0,0.02)]",
        embedded ? "flex min-h-full flex-col" : "hidden min-h-screen lg:flex lg:flex-col",
      )}
    >
      <div className="px-5 py-8">
        <Link href={platformMode ? "/admin" : "/dashboard"} className="flex items-center">
          <AnswerlyLogo variant="dark" className="h-8" />
        </Link>
      </div>
      <nav className="flex flex-1 flex-col gap-1.5 px-3">
        {finalItems.map((item) => {
          const Icon = item.icon;
          const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium transition-all duration-200",
                active
                  ? "bg-indigo-50 text-indigo-700 border border-indigo-100 shadow-sm"
                  : "border border-transparent text-slate-600 hover:bg-slate-50 hover:text-slate-900",
              )}
            >
              <Icon className={cn("size-[18px]", active ? "text-indigo-600" : "text-slate-400")} aria-hidden="true" />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>
      <div className="flex flex-col gap-3 p-4">
        <div className="rounded-xl border border-slate-200 bg-white p-3 shadow-sm transition-colors hover:border-slate-300 cursor-pointer">
          <div className="flex items-center gap-3">
            <div className="flex size-9 items-center justify-center rounded-lg bg-slate-50 text-sm font-semibold text-slate-700 ring-1 ring-slate-200">
              <Building2 className="size-4" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-slate-900">{user?.company_name || user?.username || "Acme Support Co."}</p>
              <p className="text-xs text-indigo-600 font-medium">{platformMode ? "Platform Owner" : "Enterprise Plan"}</p>
            </div>
            <ChevronDown className="size-4 text-slate-400" aria-hidden="true" />
          </div>
        </div>
      </div>
    </aside>
  );
}
