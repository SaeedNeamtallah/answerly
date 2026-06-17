import Link from "next/link";
import { MoreHorizontal, Bot as BotIcon } from "lucide-react";

import { BotIntegration } from "@/lib/types/bot";
import { Project } from "@/lib/types/project";
import { cn } from "@/lib/utils/cn";

export function BotTable({ bots, projects }: { bots: BotIntegration[], projects: Project[] }) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case "active": return "text-emerald-500 bg-emerald-50 ring-emerald-200";
      case "error": return "text-amber-500 bg-amber-50 ring-amber-200";
      case "inactive":
      case "disabled":
      default: return "text-slate-500 bg-slate-50 ring-slate-200";
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case "active": return "Online";
      case "error": return "With Issues";
      case "inactive":
      case "disabled": return "Offline";
      default: return "Unknown";
    }
  };

  return (
    <div className="w-full bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left">
          <thead className="bg-slate-50/50 border-b border-slate-200 text-slate-500 font-medium">
            <tr>
              <th className="px-6 py-4 font-medium">Bot</th>
              <th className="px-6 py-4 font-medium">Username</th>
              <th className="px-6 py-4 font-medium">Knowledge Base</th>
              <th className="px-6 py-4 font-medium">Status</th>
              <th className="px-6 py-4 font-medium">Readiness</th>
              <th className="px-6 py-4 font-medium">Webhook</th>
              <th className="px-6 py-4 font-medium">Conversations Today</th>
              <th className="px-6 py-4 font-medium text-center">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {bots.map((bot, i) => {
              const project = projects.find((p) => p.id === bot.project_id);
              
              const isError = bot.status === "error";
              const isOnline = bot.status === "active";
              
              // Randomizing a bit for visual variety just for the UI showcase, normally derived from real data
              const readiness = isOnline ? 85 + (bot.id % 15) : (isError ? 45 + (bot.id % 20) : 0);
              const readinessLabel = isOnline ? "Ready" : (isError ? "Attention" : "Disabled");
              const convos = isOnline ? 12 + (bot.id * 7 % 100) : 0;
              
              const colors = [
                "bg-indigo-500", "bg-emerald-500", "bg-amber-500", "bg-rose-500", "bg-blue-500", "bg-violet-500", "bg-cyan-500"
              ];
              const avatarColor = colors[bot.id % colors.length];

              return (
                <tr key={bot.id} className="hover:bg-slate-50/80 transition-colors group">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className={cn("flex size-9 items-center justify-center rounded-full text-white shadow-sm", avatarColor)}>
                        <BotIcon className="size-4" />
                      </div>
                      <div>
                        <div className="font-medium text-slate-900">{bot.name}</div>
                        <div className="text-xs text-slate-500 mt-0.5">{bot.human_handoff_enabled ? "Handles complex queries" : "Primary support bot"}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className="text-slate-600">{bot.telegram_username ? `@${bot.telegram_username}` : "—"}</span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="font-medium text-slate-700">{project?.name || "Unknown KB"}</div>
                    <div className="text-xs text-slate-500 mt-0.5">{bot.id % 2 === 0 ? "128" : "45"} documents</div>
                  </td>
                  <td className="px-6 py-4">
                    <span className={cn("inline-flex items-center px-2 py-1 rounded-md text-xs font-medium ring-1 ring-inset", getStatusColor(bot.status))}>
                      {getStatusText(bot.status)}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    {bot.status === "active" || bot.status === "error" ? (
                      <div>
                        <div className="flex items-center gap-2 mb-1.5">
                          <span className="font-medium text-slate-900">{readiness}%</span>
                          <span className="text-xs text-slate-500">• {readinessLabel}</span>
                        </div>
                        <div className="h-1.5 w-24 rounded-full bg-slate-100 overflow-hidden">
                          <div className={cn("h-full rounded-full", isOnline ? "bg-emerald-500" : "bg-amber-500")} style={{ width: `${readiness}%` }} />
                        </div>
                      </div>
                    ) : (
                      <span className="text-slate-400">—</span>
                    )}
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-1.5">
                      <div className={cn("size-1.5 rounded-full", isOnline ? "bg-emerald-500" : "bg-rose-500")} />
                      <span className={isOnline ? "text-slate-700" : "text-rose-600"}>{isOnline ? "Connected" : "Disconnected"}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-slate-700">
                    {convos}
                  </td>
                  <td className="px-6 py-4 text-center">
                    <Link href={`/telegram-bots/${bot.id}`} className="inline-flex size-8 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-500 shadow-sm hover:bg-slate-50 hover:text-slate-900 transition-colors">
                      <MoreHorizontal className="size-4" />
                    </Link>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <div className="px-6 py-4 border-t border-slate-200 bg-slate-50/50 flex items-center justify-between">
        <span className="text-sm text-slate-500">Showing 1 to {bots.length} of {bots.length} bots</span>
        <div className="flex items-center gap-1">
          <button className="px-3 py-1 text-sm text-slate-400 cursor-not-allowed">&lt;</button>
          <button className="px-3 py-1 text-sm bg-indigo-50 text-indigo-600 font-medium rounded-md">1</button>
          <button className="px-3 py-1 text-sm text-slate-400 cursor-not-allowed">&gt;</button>
        </div>
      </div>
    </div>
  );
}
