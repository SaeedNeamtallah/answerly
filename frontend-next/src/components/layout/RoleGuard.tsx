"use client";

import { useEffect } from "react";

import { LoadingState } from "@/components/shared/LoadingState";
import { canAccessAdmin, canAccessCompanyWorkspace } from "@/lib/auth/permissions";
import { getDefaultRouteForUser } from "@/lib/auth/redirects";
import { refreshCurrentUser, isTokenExpired } from "@/lib/auth/session";
import { useAuthStore, clearAuthSession } from "@/store/auth-store";

export function RoleGuard({
  variant,
  children,
}: {
  variant: "company" | "admin";
  children: React.ReactNode;
}) {
  const accessToken = useAuthStore((state) => state.accessToken);
  const currentUser = useAuthStore((state) => state.currentUser);
  const isHydrated = useAuthStore((state) => state.isHydrated);

  useEffect(() => {
    if (!isHydrated) {
      return;
    }

    if (!accessToken) {
      window.location.replace("/login");
      return;
    }

    if (isTokenExpired(accessToken)) {
      clearAuthSession();
      window.location.replace("/login?reason=expired");
      return;
    }

    if (!currentUser) {
      refreshCurrentUser().catch(() => {
        clearAuthSession();
        window.location.replace("/login?reason=expired");
      });
      return;
    }

    const allowed = variant === "admin" ? canAccessAdmin(currentUser) : canAccessCompanyWorkspace(currentUser);
    if (!allowed) {
      if (variant === "company") {
        window.location.replace(getDefaultRouteForUser(currentUser));
      } else {
        window.location.replace("/forbidden");
      }
    }
  }, [accessToken, currentUser, isHydrated, variant]);

  if (!isHydrated || !accessToken || !currentUser || isTokenExpired(accessToken)) {
    return <LoadingState label="Preparing workspace..." />;
  }

  if (variant === "admin" && !canAccessAdmin(currentUser)) {
    return <LoadingState label="Checking permissions..." />;
  }

  if (variant === "company" && !canAccessCompanyWorkspace(currentUser)) {
    return <LoadingState label="Checking permissions..." />;
  }

  return <>{children}</>;
}
