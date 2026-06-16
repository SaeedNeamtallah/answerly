import { ReactNode } from "react";

import { RoleGuard } from "@/components/layout/RoleGuard";
import { Sidebar, adminNav, companyNav } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";

export function AppShell({
  variant,
  children,
}: {
  variant: "company" | "admin";
  children: ReactNode;
}) {
  const items = variant === "admin" ? adminNav : companyNav;

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
