import { AdminBotIntegration } from "@/lib/types/admin";

import { EmptyState } from "@/components/shared/EmptyState";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { Card, CardContent } from "@/components/ui/card";

export function AdminErrorsFeed({ bots }: { bots: AdminBotIntegration[] }) {
  const errored = bots.filter((bot) => bot.last_error);

  if (errored.length === 0) {
    return (
      <EmptyState
        title="No bot errors"
        description="No bot integrations currently report a last_error value."
      />
    );
  }

  return (
    <div className="grid gap-3">
      {errored.map((bot) => (
        <Card key={bot.id} className="border-rose-200 bg-rose-50/70 shadow-sm">
          <CardContent className="flex items-start justify-between gap-4 p-4 text-sm text-rose-700">
            <div>
              <p className="font-medium">{bot.name}</p>
              <p className="mt-1">{bot.last_error}</p>
              <p className="mt-2 text-xs text-rose-700/70">Company {bot.owner_username || bot.owner_id} · Project #{bot.project_id}</p>
            </div>
            <StatusBadge status={bot.status} />
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
