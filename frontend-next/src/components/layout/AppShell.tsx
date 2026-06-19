"use client";

import { ReactNode } from "react";
import { Shield } from "lucide-react";

import { RoleGuard } from "@/components/layout/RoleGuard";
import { Sidebar, adminNav, companyNav } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";
import { useAuthStore } from "@/store/auth-store";
import { canAccessSecurityCenter } from "@/lib/auth/permissions";

export function AppShell({
  variant,
  children,
}: {
  variant: "company" | "admin";
  children: ReactNode;
}) {
  const currentUser = useAuthStore((state) => state.currentUser);
  let items = variant === "admin" ? adminNav : companyNav;

  if (variant === "company" && canAccessSecurityCenter(currentUser)) {
    // Insert after Dashboard or at the end
    const hasSecurity = items.some(item => item.href === "/security");
    if (!hasSecurity) {
      items = [
        ...items,
        { href: "/security", label: "Security Center", icon: Shield },
      ];
    }
  }

  return (
    <RoleGuard variant={variant}>
      <div className="flex min-h-screen bg-background">
        <Sidebar items={items} />
        <div className="flex min-h-screen min-w-0 flex-1 flex-col">
          <Topbar variant={variant} />
          <main className="flex-1 px-4 py-5 md:px-6 xl:px-7">{children}</main>
        </div>
      </div>
    </RoleGuard>
  );
}
