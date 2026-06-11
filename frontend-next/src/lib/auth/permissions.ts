import type { CurrentUser } from "@/lib/types/auth";

export function isPlatformOwner(user: CurrentUser | null) {
  return String(user?.role || "").toLowerCase() === "platform_owner";
}

export function isCompanyAdmin(user: CurrentUser | null) {
  return String(user?.role || "").toLowerCase() === "company_admin";
}

export function canAccessAdmin(user: CurrentUser | null) {
  return isPlatformOwner(user);
}

export function canAccessCompanyWorkspace(user: CurrentUser | null) {
  return isCompanyAdmin(user) || isPlatformOwner(user);
}
