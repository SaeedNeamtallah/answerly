import Link from "next/link";

import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      <div className="max-w-xl space-y-6 rounded-3xl border border-slate-200 bg-white p-10 text-center shadow-sm">
        <p className="text-sm font-medium uppercase tracking-[0.2em] text-indigo-600">404</p>
        <h1 className="text-3xl font-semibold tracking-tight text-slate-950">Page not found</h1>
        <p className="text-sm text-slate-600">
          The requested route does not exist in the new dashboard yet.
        </p>
        <Button asChild>
          <Link href="/dashboard">Go to dashboard</Link>
        </Button>
      </div>
    </div>
  );
}
