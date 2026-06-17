import { Building2, Bot, MessageSquareText, BarChart3 } from "lucide-react";

import { AdminOverview } from "@/lib/types/admin";
import { formatNumber } from "@/lib/utils/formatters";

export function AdminMetricCards({ overview }: { overview: AdminOverview }) {
  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm hover:shadow-md transition-shadow relative overflow-hidden">
        <div className="absolute right-0 top-0 p-4 opacity-5 pointer-events-none">
          <Building2 className="size-16" />
        </div>
        <div className="flex items-center gap-3 text-slate-500 mb-2">
          <div className="rounded-lg bg-indigo-50 p-2 text-indigo-600">
            <Building2 className="size-4" />
          </div>
          <h3 className="text-sm font-medium">Companies</h3>
        </div>
        <div className="text-3xl font-bold text-slate-900">{formatNumber(overview.companies)}</div>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm hover:shadow-md transition-shadow relative overflow-hidden">
        <div className="absolute right-0 top-0 p-4 opacity-5 pointer-events-none">
          <BarChart3 className="size-16" />
        </div>
        <div className="flex items-center gap-3 text-slate-500 mb-2">
          <div className="rounded-lg bg-slate-100 p-2 text-slate-600">
            <BarChart3 className="size-4" />
          </div>
          <h3 className="text-sm font-medium">Projects</h3>
        </div>
        <div className="text-3xl font-bold text-slate-900">{formatNumber(overview.projects)}</div>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm hover:shadow-md transition-shadow relative overflow-hidden">
        <div className="absolute right-0 top-0 p-4 opacity-5 pointer-events-none">
          <Bot className="size-16" />
        </div>
        <div className="flex items-center gap-3 text-slate-500 mb-2">
          <div className="rounded-lg bg-emerald-50 p-2 text-emerald-600">
            <Bot className="size-4" />
          </div>
          <h3 className="text-sm font-medium">Bots</h3>
        </div>
        <div className="text-3xl font-bold text-slate-900">{formatNumber(overview.bot_integrations)}</div>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm hover:shadow-md transition-shadow relative overflow-hidden">
        <div className="absolute right-0 top-0 p-4 opacity-5 pointer-events-none">
          <MessageSquareText className="size-16" />
        </div>
        <div className="flex items-center gap-3 text-slate-500 mb-2">
          <div className="rounded-lg bg-amber-50 p-2 text-amber-600">
            <MessageSquareText className="size-4" />
          </div>
          <h3 className="text-sm font-medium">Conversations</h3>
        </div>
        <div className="text-3xl font-bold text-slate-900">{formatNumber(overview.conversations)}</div>
      </div>
    </div>
  );
}
