import Link from "next/link";
import { Bot, ExternalLink, MessageSquareWarning, ShieldCheck } from "lucide-react";

import { BotIntegration } from "@/lib/types/bot";
import { formatRelativeDate } from "@/lib/utils/dates";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { StatusBadge } from "@/components/shared/StatusBadge";

export function BotCard({ bot }: { bot: BotIntegration }) {
  return (
    <Card className="border-border/80 bg-card shadow-sm transition-shadow hover:shadow-md">
      <CardHeader className="flex flex-row items-start justify-between gap-4">
        <div className="flex min-w-0 gap-3">
          <span className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary">
            <Bot className="size-4" />
          </span>
          <div className="min-w-0">
            <CardTitle className="truncate">{bot.name}</CardTitle>
            <p className="mt-1 truncate text-sm text-muted-foreground">{bot.telegram_username || "Username pending"}</p>
          </div>
        </div>
        <StatusBadge status={bot.status} />
      </CardHeader>
      <CardContent className="space-y-3 text-sm text-muted-foreground">
        <p className="line-clamp-2 min-h-10">{bot.fallback_message || "No fallback message configured."}</p>
        <div className="flex flex-wrap gap-2">
          <Badge variant="outline" className="rounded-md">
            <ShieldCheck className="size-3" />
            {bot.show_sources_to_customer ? "Sources visible" : "Sources internal"}
          </Badge>
          <Badge variant="outline" className="rounded-md">
            <MessageSquareWarning className="size-3" />
            {bot.human_handoff_enabled ? "Handoff enabled" : "Handoff off"}
          </Badge>
        </div>
      </CardContent>
      <CardFooter className="justify-between">
        <span className="text-xs text-muted-foreground">Updated {formatRelativeDate(bot.updated_at || bot.created_at)}</span>
        <Button asChild size="sm" variant="outline">
          <Link href={`/telegram-bots/${bot.id}`}>
            <ExternalLink className="size-3.5" />
            Open
          </Link>
        </Button>
      </CardFooter>
    </Card>
  );
}
