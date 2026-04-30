"use client";

import { useEffect } from "react";

import { ErrorState } from "@/components/shared/ErrorState";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="min-h-screen bg-slate-50 p-4 md:p-8">
      <ErrorState
        title="Unexpected render error"
        description={error.message || "An unexpected UI error occurred."}
        retryLabel="Reload section"
        onRetry={reset}
      />
    </div>
  );
}
