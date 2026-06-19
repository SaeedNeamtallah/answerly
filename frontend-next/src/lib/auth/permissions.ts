import type { CurrentUser } from "@/lib/types/auth";

export function isPlatformOwner(user: CurrentUser | null) {
  return String(user?.role || "").toLowerCase() === "platform_owner";
}

export function isCompanyAdmin(user: CurrentUser | null) {
  return String(user?.role || "").toLowerCase() === "company_admin";
}

export function isSecurityEngineer(user: CurrentUser | null) {
  const role = String(user?.role || "").toLowerCase();
  return role === "security_engineer" || role === "cybersecurity_engineer";
}

export function isAdmin(user: CurrentUser | null) {
  return String(user?.role || "").toLowerCase() === "admin";
}

export function isUser(user: CurrentUser | null) {
  return String(user?.role || "").toLowerCase() === "user";
}

export function canAccessAdmin(user: CurrentUser | null) {
  return isPlatformOwner(user);
}

export function canAccessSecurityCenter(user: CurrentUser | null) {
  return isPlatformOwner(user) || isAdmin(user) || isSecurityEngineer(user);
}

export function canAccessCompanyWorkspace(user: CurrentUser | null) {
  // Everyone with an active login can access the company workspace
  // They will just see their own scoped data.
  return !!user;
}
