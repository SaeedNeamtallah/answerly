import { AdminBotIntegration } from "@/lib/types/admin";

import { DataTable } from "@/components/shared/DataTable";
import { StatusBadge } from "@/components/shared/StatusBadge";

export function AdminBotsTable({ bots }: { bots: AdminBotIntegration[] }) {
  return (
    <DataTable
      caption="Cross-company bot integrations"
      columns={["Bot", "Company", "Project", "Status", "Last Error"]}
      rows={bots.map((bot) => [
        bot.name,
        bot.owner_username || String(bot.owner_id),
        String(bot.project_id),
        <StatusBadge key={bot.id} status={bot.status} />,
        bot.last_error || "—",
      ])}
    />
  );
}
