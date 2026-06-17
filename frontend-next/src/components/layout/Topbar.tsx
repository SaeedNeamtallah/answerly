"use client";

import Link from "next/link";
import { Bell, LogOut, Search, Command } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { MobileNav } from "@/components/layout/MobileNav";
import { adminNav, companyNav, type NavItem } from "@/components/layout/Sidebar";
import { useAuthStore } from "@/store/auth-store";

export function Topbar({ variant }: { variant: "company" | "admin" }) {
  const user = useAuthStore((state) => state.currentUser);
  const clearSession = useAuthStore((state) => state.clearSession);
  const nav = variant === "admin" ? adminNav : companyNav;
  
  const initials = (user?.company_name || user?.username || "A").slice(0, 2).toUpperCase();
  const displayName = user?.company_name || user?.username || "Answerly";
  const roleName = variant === "admin" ? "Platform Admin" : "Admin";

  return (
    <header className="sticky top-0 z-20 bg-background/92 backdrop-blur pt-4 pb-2">
      <div className="flex items-center justify-between gap-4 px-4 md:px-6 xl:px-7">
        <div className="flex items-center gap-3 xl:hidden">
          <MobileNav items={nav as NavItem[]} />
        </div>
        {/* We leave the left side empty on desktop to let PageHeader align nicely, or we could add breadcrumbs */}
        <div className="hidden xl:flex flex-1" />
        
        <div className="flex flex-1 justify-end max-w-md">
          <div className="flex h-10 w-full items-center justify-between gap-3 rounded-full border border-slate-200 bg-white px-4 text-sm text-slate-400 shadow-sm transition-colors hover:border-slate-300">
            <div className="flex items-center gap-2">
              <Search className="size-4" aria-hidden="true" />
              <span className="truncate">Search anything...</span>
            </div>
            <div className="flex items-center gap-1 rounded bg-slate-100 px-1.5 py-0.5 text-xs font-medium text-slate-500">
              <Command className="size-3" />
              <span>K</span>
            </div>
          </div>
        </div>
        
        <div className="flex items-center gap-4 pl-2">
          <div className="relative">
            <Button variant="ghost" size="icon" className="rounded-full text-slate-600 hover:bg-slate-100" aria-label="Notifications">
              <Bell className="size-5" />
            </Button>
            <span className="absolute right-1 top-1 flex size-4 items-center justify-center rounded-full bg-blue-600 text-[10px] font-bold text-white ring-2 ring-white">
              7
            </span>
          </div>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button className="flex items-center gap-3 rounded-full p-1 pr-3 text-left transition-colors hover:bg-slate-100 outline-none">
                <div className="flex size-9 items-center justify-center rounded-full bg-slate-900 text-sm font-semibold text-white">
                  {initials}
                </div>
                <div className="hidden md:block">
                  <p className="text-sm font-semibold text-slate-900 leading-tight">{displayName}</p>
                  <p className="text-xs text-slate-500">{roleName}</p>
                </div>
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <DropdownMenuItem asChild>
                <Link href="/account">Account Settings</Link>
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                className="text-red-600 focus:text-red-600"
                onClick={() => {
                  clearSession();
                  window.location.replace("/login");
                }}
              >
                <LogOut className="mr-2 size-4" />
                Sign out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </header>
  );
}
