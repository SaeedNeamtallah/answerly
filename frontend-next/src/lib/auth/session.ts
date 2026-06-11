"use client";

import { useEffect } from "react";

import { getMe } from "@/lib/api/auth";
import { redirectToDefaultRoute } from "@/lib/auth/redirects";
import { useAuthStore } from "@/store/auth-store";

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
  if (state.currentUser) {
    redirectToDefaultRoute(state.currentUser);
    return;
  }

  const user = await refreshCurrentUser();
  redirectToDefaultRoute(user);
}
