import Link from "next/link";

import { Button } from "@/components/ui/button";

export default function ForbiddenPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      <div className="max-w-xl space-y-6 rounded-3xl border border-slate-200 bg-white p-10 text-center shadow-sm">
        <p className="text-sm font-medium uppercase tracking-[0.2em] text-amber-600">403</p>
        <h1 className="text-3xl font-semibold tracking-tight text-slate-950">Access forbidden</h1>
        <p className="text-sm text-slate-600">
          Your current role does not have access to this area.
        </p>
        <div className="flex justify-center gap-3">
          <Button asChild variant="outline">
            <Link href="/dashboard">Company workspace</Link>
          </Button>
          <Button asChild>
            <Link href="/admin">Admin console</Link>
          </Button>
        </div>
      </div>
    </div>
  );
}
