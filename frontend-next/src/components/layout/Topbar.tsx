"use client";

import Link from "next/link";
import { Bell, LogOut, Search } from "lucide-react";

import { Button } from "@/components/ui/button";
import { MobileNav } from "@/components/layout/MobileNav";
import { adminNav, companyNav, type NavItem } from "@/components/layout/Sidebar";
import { useAuthStore } from "@/store/auth-store";

export function Topbar({ variant }: { variant: "company" | "admin" }) {
  const user = useAuthStore((state) => state.currentUser);
  const clearSession = useAuthStore((state) => state.clearSession);
  const nav = variant === "admin" ? adminNav : companyNav;

  return (
    <header className="sticky top-0 z-20 border-b border-border bg-background/92 backdrop-blur">
      <div className="flex items-center justify-between gap-4 px-4 py-3 md:px-6 xl:px-7">
        <div className="flex items-center gap-3">
          <MobileNav items={nav as NavItem[]} />
          <div>
            <p className="text-xs font-medium text-muted-foreground">
              {variant === "admin" ? "Platform Console" : "Company Workspace"}
            </p>
            <h2 className="text-lg font-semibold text-foreground">{user?.company_name || user?.username || "Answerly"}</h2>
          </div>
        </div>
        <div className="hidden min-w-0 flex-1 justify-center px-6 xl:flex">
          <div className="flex h-10 w-full max-w-lg items-center gap-3 rounded-xl border border-border bg-card px-3 text-sm text-muted-foreground shadow-sm">
            <Search className="size-4" aria-hidden="true" />
            <span className="truncate">Use page filters and table search for backend-bound data</span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="icon" aria-label="Notifications">
            <Bell />
          </Button>
          <Button variant="ghost" asChild>
            <Link href="/account">
              <span className="hidden sm:inline">Account</span>
              <span className="sm:hidden">Me</span>
            </Link>
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              clearSession();
              window.location.replace("/login");
            }}
          >
            <LogOut data-icon="inline-start" />
            Sign out
          </Button>
        </div>
      </div>
    </header>
  );
}
