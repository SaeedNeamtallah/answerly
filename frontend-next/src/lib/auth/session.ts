"use client";

import { useEffect } from "react";

import { getMe } from "@/lib/api/auth";
import { redirectToDefaultRoute } from "@/lib/auth/redirects";
import { useAuthStore, clearAuthSession } from "@/store/auth-store";

export function isTokenExpired(token: string | null): boolean {
  if (!token) return true;
  try {
    const parts = token.split(".");
    if (parts.length !== 3) return true;

    const base64 = parts[1].replace(/-/g, "+").replace(/_/g, "/");
    const payloadJson = typeof window !== "undefined" && typeof window.atob === "function"
      ? window.atob(base64)
      : Buffer.from(base64, "base64").toString("binary");

    const payload = JSON.parse(payloadJson);

    if (payload.exp && typeof payload.exp === "number") {
      return payload.exp * 1000 < Date.now();
    }
    return false;
  } catch {
    return true;
  }
}

export function useHydrateAuthSession() {
  useEffect(() => {
    useAuthStore.getState().hydrateFromStorage();
  }, []);
}

export async function refreshCurrentUser() {
  const user = await getMe();
  useAuthStore.getState().setCurrentUser(user);
  return user;
}

export async function handleAuthenticatedRedirect() {
  const state = useAuthStore.getState();
  
  if (isTokenExpired(state.accessToken)) {
    clearAuthSession();
    return;
  }

  if (state.currentUser) {
    redirectToDefaultRoute(state.currentUser);
    return;
  }

  const user = await refreshCurrentUser();
  redirectToDefaultRoute(user);
}
