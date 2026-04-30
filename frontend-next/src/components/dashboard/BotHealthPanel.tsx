import { BotIntegration } from "@/lib/types/bot";

import { EmptyState } from "@/components/shared/EmptyState";
import { StatusBadge } from "@/components/shared/StatusBadge";

export function BotHealthPanel({ bots }: { bots: BotIntegration[] }) {
  if (bots.length === 0) {
    return (
      <EmptyState
        title="No Telegram bots"
        description="Create an integration when your first knowledge base is ready."
        actionLabel="Create bot"
        actionHref="/telegram-bots"
      />
    );
  }

  return (
    <div className="space-y-3 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <h3 className="text-lg font-semibold text-slate-950">Bot health</h3>
      {bots.slice(0, 5).map((bot) => (
        <div key={bot.id} className="flex items-center justify-between rounded-xl border border-slate-200 px-3 py-3">
          <div>
            <p className="font-medium text-slate-900">{bot.name}</p>
            <p className="text-sm text-slate-500">{bot.telegram_username || "Username pending"}</p>
          </div>
          <StatusBadge status={bot.status} />
        </div>
      ))}
    </div>
  );
}
