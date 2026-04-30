import { AdminBotIntegration } from "@/lib/types/admin";

import { EmptyState } from "@/components/shared/EmptyState";

export function AdminErrorsFeed({ bots }: { bots: AdminBotIntegration[] }) {
  const errored = bots.filter((bot) => bot.last_error);

  if (errored.length === 0) {
    return (
      <EmptyState
        title="No aggregated admin errors"
        description="Unified admin error feed endpoint is not available yet. This page falls back to bot last_error values."
      />
    );
  }

  return (
    <div className="space-y-3">
      {errored.map((bot) => (
        <div key={bot.id} className="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
          <p className="font-medium">{bot.name}</p>
          <p className="mt-1">{bot.last_error}</p>
        </div>
      ))}
    </div>
  );
}
