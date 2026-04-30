import Link from "next/link";

import { BotIntegration } from "@/lib/types/bot";

import { DataTable } from "@/components/shared/DataTable";
import { StatusBadge } from "@/components/shared/StatusBadge";

export function BotTable({ bots }: { bots: BotIntegration[] }) {
  return (
    <DataTable
      columns={["Bot", "Project", "Status", "Open"]}
      rows={bots.map((bot) => [
        `${bot.name}${bot.telegram_username ? ` (${bot.telegram_username})` : ""}`,
        String(bot.project_id),
        <StatusBadge key={bot.id} status={bot.status} />,
        <Link key={`bot-${bot.id}`} href={`/telegram-bots/${bot.id}`} className="text-indigo-600">
          Details
        </Link>,
      ])}
    />
  );
}
