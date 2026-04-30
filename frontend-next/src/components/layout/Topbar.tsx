"use client";

import Link from "next/link";
import { LogOut } from "lucide-react";

import { Button } from "@/components/ui/button";
import { MobileNav } from "@/components/layout/MobileNav";
import { adminNav, companyNav, type NavItem } from "@/components/layout/Sidebar";
import { useAuthStore } from "@/store/auth-store";

export function Topbar({ variant }: { variant: "company" | "admin" }) {
  const user = useAuthStore((state) => state.currentUser);
  const clearSession = useAuthStore((state) => state.clearSession);
  const nav = variant === "admin" ? adminNav : companyNav;

  return (
    <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/90 backdrop-blur">
      <div className="flex items-center justify-between gap-4 px-4 py-4 md:px-6">
        <div className="flex items-center gap-3">
          <MobileNav items={nav as NavItem[]} />
          <div>
            <p className="text-sm font-medium text-slate-500">
              {variant === "admin" ? "Platform Console" : "Company Workspace"}
            </p>
            <h2 className="text-lg font-semibold text-slate-950">{user?.company_name || user?.username || "RAGMind"}</h2>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="ghost" asChild>
            <Link href="/account">Account</Link>
          </Button>
          <Button
            variant="outline"
            onClick={() => {
              clearSession();
              window.location.replace("/login");
            }}
          >
            <LogOut className="size-4" />
            Sign out
          </Button>
        </div>
      </div>
    </header>
  );
}
