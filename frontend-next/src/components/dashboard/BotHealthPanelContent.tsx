"use client";

import { Pie, PieChart, Cell } from "recharts";
import { Info, Activity, ChevronDown, ArrowRight } from "lucide-react";
import Link from "next/link";

import { BotIntegration } from "@/lib/types/bot";
import { EmptyState } from "@/components/shared/EmptyState";
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";

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

  const totalBots = bots.length;
  const active = bots.filter((bot) => ["active", "online", "ready"].includes(String(bot.status).toLowerCase())).length;
  const issue = bots.filter((bot) => bot.last_error).length;
  const other = Math.max(totalBots - active - issue, 0);

  const chartData = [
    { name: "Healthy", value: active, fill: "#10b981", percent: totalBots ? `${Math.round((active/totalBots)*100)}%` : "0%" },
    { name: "Degraded", value: issue, fill: "#f59e0b", percent: totalBots ? `${Math.round((issue/totalBots)*100)}%` : "0%" },
    { name: "Other", value: other, fill: "#6366f1", percent: totalBots ? `${Math.round((other/totalBots)*100)}%` : "0%" },
  ];

  const errorBots = bots.filter(b => b.last_error).slice(0, 3);

  return (
    <div className="flex flex-col rounded-2xl border border-slate-100 bg-white shadow-[0_2px_10px_rgba(0,0,0,0.02)]">
      <div className="flex items-center justify-between p-6 pb-2">
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2">
            <h3 className="text-lg font-semibold text-slate-900">Bot Health</h3>
            <Info className="size-4 text-slate-400" />
          </div>
          <p className="text-sm text-slate-500">Real-time status of your bots</p>
        </div>
        <Link href="/telegram-bots" className="flex items-center gap-2 rounded-xl border border-slate-200 px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50">
          All Bots
          <ChevronDown className="size-4 text-slate-400" />
        </Link>
      </div>

      <div className="grid gap-6 p-6 md:grid-cols-[200px_1.5fr_1fr] items-center">
        {/* Chart */}
        <div className="relative">
          <ChartContainer config={{}} className="mx-auto aspect-square max-h-48">
            <PieChart>
              <Pie 
                data={chartData} 
                dataKey="value" 
                nameKey="name" 
                innerRadius={60} 
                outerRadius={80}
                strokeWidth={0}
                paddingAngle={2}
              >
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.fill} />
                ))}
              </Pie>
            </PieChart>
          </ChartContainer>
          <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-3xl font-bold text-slate-900">{totalBots}</span>
            <span className="text-xs font-medium text-slate-500">Total Bots</span>
          </div>
        </div>

        {/* Legend */}
        <div className="flex flex-col gap-4 px-4">
          {chartData.map((item) => (
            <div key={item.name} className="flex items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="size-2 rounded-full" style={{ backgroundColor: item.fill }} />
                <span className="text-sm font-medium text-slate-700">{item.name}</span>
              </div>
              <div className="flex items-center gap-4 text-sm">
                <span className="font-semibold text-slate-900">{item.value}</span>
                <span className="w-12 text-right text-slate-500">{item.percent}</span>
              </div>
            </div>
          ))}
        </div>

        {/* Bots with Issues */}
        <div className="flex flex-col rounded-xl bg-slate-50/50 p-4 relative">
          <Activity className="absolute top-4 right-4 size-5 text-emerald-500 opacity-50" />
          <h4 className="mb-4 text-sm font-semibold text-slate-900">Bots with Issues</h4>
          {errorBots.length > 0 ? (
            <div className="flex flex-col gap-3">
              {errorBots.map((bot) => (
                <div key={bot.id} className="flex items-center justify-between">
                  <Link href={`/telegram-bots/${bot.id}`} className="text-sm font-medium text-slate-700 hover:text-blue-600 truncate max-w-[120px]" title={bot.name}>
                    {bot.name}
                  </Link>
                  <span className="rounded-md px-2 py-0.5 text-xs font-medium bg-red-100 text-red-600 truncate max-w-[80px]" title={bot.last_error || "Error"}>
                    {bot.last_error}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex flex-1 flex-col items-center justify-center text-center text-sm text-slate-500">
              No issues detected.
            </div>
          )}
          <Link href="/admin/errors" className="mt-5 flex items-center text-sm font-medium text-blue-600 hover:text-blue-700">
            View all errors <ArrowRight className="ml-1 size-4" />
          </Link>
        </div>
      </div>
    </div>
  );
}
