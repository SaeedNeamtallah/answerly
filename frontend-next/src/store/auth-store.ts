"use client";

import { create } from "zustand";

import type { CurrentUser, ProductRole } from "@/lib/types/auth";

const STORAGE_KEY = "ragmind-next-auth";

export interface AuthSessionState {
  accessToken: string | null;
  currentUser: CurrentUser | null;
  role: ProductRole | null;
  isHydrated: boolean;
  setAccessToken: (token: string | null) => void;
  setCurrentUser: (user: CurrentUser | null) => void;
  markHydrated: () => void;
  clearSession: () => void;
  hydrateFromStorage: () => void;
}

interface PersistedAuthSession {
  accessToken: string | null;
  currentUser: CurrentUser | null;
}

function getPersistedSession(): PersistedAuthSession | null {
  if (typeof window === "undefined") {
    return null;
  }

  const raw = window.localStorage.getItem(STORAGE_KEY);
  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw) as PersistedAuthSession;
  } catch {
    window.localStorage.removeItem(STORAGE_KEY);
    return null;
  }
}

function persistSession(session: PersistedAuthSession) {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
}

function clearPersistedSession() {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.removeItem(STORAGE_KEY);
}

export const useAuthStore = create<AuthSessionState>((set, get) => ({
  accessToken: null,
  currentUser: null,
  role: null,
  isHydrated: false,
  setAccessToken: (token) => {
    const currentUser = token === get().accessToken ? get().currentUser : null;
    persistSession({ accessToken: token, currentUser });
    set({ accessToken: token, currentUser, role: currentUser?.role ?? null });
  },
  setCurrentUser: (user) => {
    const accessToken = get().accessToken;
    persistSession({ accessToken, currentUser: user });
    set({ currentUser: user, role: user?.role ?? null });
  },
  markHydrated: () => set({ isHydrated: true }),
  clearSession: () => {
    clearPersistedSession();
    set({ accessToken: null, currentUser: null, role: null, isHydrated: true });
  },
  hydrateFromStorage: () => {
    const persisted = getPersistedSession();
    set({
      accessToken: persisted?.accessToken ?? null,
      currentUser: persisted?.currentUser ?? null,
      role: persisted?.currentUser?.role ?? null,
      isHydrated: true,
    });
  },
}));

export function readAccessToken() {
  return useAuthStore.getState().accessToken;
}

export function clearAuthSession() {
  useAuthStore.getState().clearSession();
}
