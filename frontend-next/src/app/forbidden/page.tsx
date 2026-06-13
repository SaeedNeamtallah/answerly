"use client";

import Link from "next/link";
import { LogOut } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/store/auth-store";

export default function ForbiddenPage() {
  const clearSession = useAuthStore((state) => state.clearSession);

  const handleSignOut = () => {
    clearSession();
    window.location.replace("/login");
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      <div className="max-w-xl space-y-6 rounded-3xl border border-slate-200 bg-white p-10 text-center shadow-sm">
        <p className="text-sm font-medium uppercase tracking-[0.2em] text-amber-600">403</p>
        <h1 className="text-3xl font-semibold tracking-tight text-slate-950">Access forbidden</h1>
        <p className="text-sm text-slate-600">
          Your current role does not have access to this area.
        </p>
        <div className="flex flex-col sm:flex-row justify-center gap-3">
          <Button asChild variant="outline">
            <Link href="/dashboard">Company workspace</Link>
          </Button>
          <Button asChild variant="outline">
            <Link href="/admin">Admin console</Link>
          </Button>
          <Button onClick={handleSignOut} className="gap-2">
            <LogOut className="size-4" />
            Sign out
          </Button>
        </div>
      </div>
    </div>
  );
}
