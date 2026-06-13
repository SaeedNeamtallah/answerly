import type { CurrentUser } from "@/lib/types/auth";

import { canAccessAdmin } from "@/lib/auth/permissions";

export function getDefaultRouteForUser(user: CurrentUser | null) {
  if (canAccessAdmin(user)) {
    return "/admin";
  }
  if (String(user?.role || "").toLowerCase() === "employee") {
    return "/conversations";
  }

  return "/dashboard";
}

export function redirectToDefaultRoute(user: CurrentUser | null) {
  if (typeof window === "undefined") {
    return;
  }

  window.location.replace(getDefaultRouteForUser(user));
}
