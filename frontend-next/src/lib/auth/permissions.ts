import type { CurrentUser } from "@/lib/types/auth";

export function isPlatformOwner(user: CurrentUser | null) {
  return String(user?.role || "").toLowerCase() === "platform_owner";
}

export function isCompanyAdmin(user: CurrentUser | null) {
  return String(user?.role || "").toLowerCase() === "company_admin";
}

export function isSecurityEngineer(user: CurrentUser | null) {
  const roles = user?.roles || [];
  const hasEngineerRole = roles.some(role => {
    const r = String(role || "").toLowerCase();
    return r === "security_engineer" || r === "cybersecurity_engineer";
  });
  const singleRole = String(user?.role || "").toLowerCase();
  return hasEngineerRole || singleRole === "security_engineer" || singleRole === "cybersecurity_engineer";
}

export function isAdmin(user: CurrentUser | null) {
  const roles = user?.roles || [];
  const hasAdminRole = roles.some(role => String(role || "").toLowerCase() === "admin");
  const singleRole = String(user?.role || "").toLowerCase();
  return hasAdminRole || singleRole === "admin";
}

export function isUser(user: CurrentUser | null) {
  const roles = user?.roles || [];
  const hasUserRole = roles.some(role => String(role || "").toLowerCase() === "user");
  const singleRole = String(user?.role || "").toLowerCase();
  return hasUserRole || singleRole === "user";
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
