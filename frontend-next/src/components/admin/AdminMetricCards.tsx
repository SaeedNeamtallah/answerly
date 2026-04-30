import { Building2, Bot, MessageSquareText, BarChart3 } from "lucide-react";

import { AdminOverview } from "@/lib/types/admin";
import { formatNumber } from "@/lib/utils/formatters";

import { MetricCard } from "@/components/shared/MetricCard";

export function AdminMetricCards({ overview }: { overview: AdminOverview }) {
  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      <MetricCard title="Companies" value={formatNumber(overview.companies)} icon={<Building2 className="size-4 text-indigo-600" />} />
      <MetricCard title="Projects" value={formatNumber(overview.projects)} icon={<BarChart3 className="size-4 text-indigo-600" />} />
      <MetricCard title="Bots" value={formatNumber(overview.bot_integrations)} icon={<Bot className="size-4 text-indigo-600" />} />
      <MetricCard title="Conversations" value={formatNumber(overview.conversations)} icon={<MessageSquareText className="size-4 text-indigo-600" />} />
    </div>
  );
}
