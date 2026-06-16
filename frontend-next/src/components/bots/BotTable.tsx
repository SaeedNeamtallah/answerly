import Link from "next/link";
import { ExternalLink } from "lucide-react";

import { BotIntegration } from "@/lib/types/bot";

import { DataTable } from "@/components/shared/DataTable";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export function BotTable({ bots }: { bots: BotIntegration[] }) {
  return (
    <DataTable
      caption="Telegram bot inventory"
      columns={["Bot", "Project", "Sources", "Handoff", "Status", "Open"]}
      rows={bots.map((bot) => [
        `${bot.name}${bot.telegram_username ? ` (${bot.telegram_username})` : ""}`,
        String(bot.project_id),
        <Badge key={`sources-${bot.id}`} variant="outline" className="rounded-md">
          {bot.show_sources_to_customer ? "Customer-visible" : "Internal"}
        </Badge>,
        <Badge key={`handoff-${bot.id}`} variant="outline" className="rounded-md">
          {bot.human_handoff_enabled ? "Enabled" : "Off"}
        </Badge>,
        <StatusBadge key={bot.id} status={bot.status} />,
        <Button key={`bot-${bot.id}`} asChild size="sm" variant="outline">
          <Link href={`/telegram-bots/${bot.id}`}>
            <ExternalLink className="size-3.5" />
            Details
          </Link>
        </Button>,
      ])}
    />
  );
}
