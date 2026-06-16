import Link from "next/link";
import { Bot, ExternalLink } from "lucide-react";

import { BotIntegration } from "@/lib/types/bot";

import { Card, CardContent } from "@/components/ui/card";
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
    <div className="grid gap-3 md:grid-cols-2">
      {bots.map((bot) => (
        <Card key={bot.id} className="border-border/80 bg-card shadow-sm">
          <CardContent className="flex items-center justify-between gap-4 p-4">
            <div className="flex min-w-0 items-center gap-3">
              <span className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary">
                <Bot className="size-4" />
              </span>
              <div className="min-w-0">
                <p className="truncate font-medium text-foreground">{bot.name}</p>
                <p className="truncate text-sm text-muted-foreground">{bot.telegram_username || "Telegram username pending"}</p>
              </div>
            </div>
            <div className="flex shrink-0 items-center gap-2">
              <StatusBadge status={bot.status} />
              <Link href={`/telegram-bots/${bot.id}`} className="text-muted-foreground hover:text-foreground">
                <ExternalLink className="size-4" />
              </Link>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
