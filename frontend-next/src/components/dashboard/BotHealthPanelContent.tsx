"use client";

import { Pie, PieChart } from "recharts";

import { BotIntegration } from "@/lib/types/bot";

import { EmptyState } from "@/components/shared/EmptyState";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ChartContainer, ChartTooltip, ChartTooltipContent, type ChartConfig } from "@/components/ui/chart";

const chartConfig = {
  active: { label: "Active", color: "var(--chart-2)" },
  issue: { label: "With issues", color: "var(--chart-4)" },
  other: { label: "Other", color: "var(--chart-5)" },
} satisfies ChartConfig;

export function BotHealthPanelContent({ bots }: { bots: BotIntegration[] }) {
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

  const active = bots.filter((bot) => ["active", "online", "ready"].includes(String(bot.status).toLowerCase())).length;
  const issue = bots.filter((bot) => bot.last_error).length;
  const other = Math.max(bots.length - active - issue, 0);
  const chartData = [
    { name: "Active", value: active, fill: "var(--color-active)" },
    { name: "With issues", value: issue, fill: "var(--color-issue)" },
    { name: "Other", value: other, fill: "var(--color-other)" },
  ].filter((item) => item.value > 0);

  return (
    <Card className="shadow-sm">
      <CardHeader>
        <CardTitle>Bot health</CardTitle>
        <CardDescription>Real-time status from saved Telegram integrations.</CardDescription>
      </CardHeader>
      <CardContent className="grid gap-5 md:grid-cols-[220px_1fr]">
        <div className="relative">
          <ChartContainer config={chartConfig} className="mx-auto aspect-square max-h-52">
            <PieChart>
              <ChartTooltip content={<ChartTooltipContent hideLabel />} />
              <Pie data={chartData} dataKey="value" nameKey="name" innerRadius={58} outerRadius={82} />
            </PieChart>
          </ChartContainer>
          <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-2xl font-semibold">{bots.length}</span>
            <span className="text-xs text-muted-foreground">Total bots</span>
          </div>
        </div>
        <div className="flex flex-col gap-3">
          {bots.slice(0, 5).map((bot) => (
            <div key={bot.id} className="flex items-center justify-between gap-3 rounded-xl border border-border px-3 py-3">
              <div className="min-w-0">
                <p className="truncate font-medium text-foreground">{bot.name}</p>
                <p className="truncate text-sm text-muted-foreground">{bot.telegram_username || "Username pending"}</p>
              </div>
              <StatusBadge status={bot.last_error ? "attention" : bot.status} />
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
