import Link from "next/link";

import { BotIntegration } from "@/lib/types/bot";

import { EmptyState } from "@/components/shared/EmptyState";
import { StatusBadge } from "@/components/shared/StatusBadge";

export function LinkedBotsPanel({ bots }: { bots: BotIntegration[] }) {
  if (bots.length === 0) {
    return (
      <EmptyState
        title="No linked bots"
        description="Connect a Telegram bot when this knowledge base is ready."
        actionLabel="Manage bots"
        actionHref="/telegram-bots"
      />
    );
  }

  return (
    <div className="space-y-3">
      {bots.map((bot) => (
        <Link
          key={bot.id}
          href={`/telegram-bots/${bot.id}`}
          className="flex items-center justify-between rounded-2xl border border-slate-200 bg-white px-4 py-4 shadow-sm"
        >
          <div>
            <p className="font-medium text-slate-900">{bot.name}</p>
            <p className="text-sm text-slate-500">{bot.telegram_username || "Telegram username pending"}</p>
          </div>
          <StatusBadge status={bot.status} />
        </Link>
      ))}
    </div>
  );
}
