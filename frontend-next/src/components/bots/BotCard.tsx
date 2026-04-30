import Link from "next/link";

import { BotIntegration } from "@/lib/types/bot";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { StatusBadge } from "@/components/shared/StatusBadge";

export function BotCard({ bot }: { bot: BotIntegration }) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between">
        <div>
          <CardTitle>{bot.name}</CardTitle>
          <p className="mt-1 text-sm text-slate-500">{bot.telegram_username || "Username pending"}</p>
        </div>
        <StatusBadge status={bot.status} />
      </CardHeader>
      <CardContent className="text-sm text-slate-600">
        {bot.fallback_message || "No fallback message configured."}
      </CardContent>
      <CardFooter className="justify-between">
        <span className="text-xs text-slate-500">Project #{bot.project_id}</span>
        <Button asChild size="sm">
          <Link href={`/telegram-bots/${bot.id}`}>Open</Link>
        </Button>
      </CardFooter>
    </Card>
  );
}
