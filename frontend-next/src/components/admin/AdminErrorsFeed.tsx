import { AdminBotIntegration } from "@/lib/types/admin";

import { EmptyState } from "@/components/shared/EmptyState";
import { ShieldAlert, AlertCircle, Building2, Hash } from "lucide-react";
import { cn } from "@/lib/utils/cn";

export function AdminErrorsFeed({ bots }: { bots: AdminBotIntegration[] }) {
  const errored = bots.filter((bot) => bot.last_error);

  if (errored.length === 0) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white p-8 text-center shadow-sm">
        <div className="mx-auto flex size-12 items-center justify-center rounded-full bg-emerald-50 text-emerald-600 mb-4">
          <ShieldAlert className="size-6" />
        </div>
        <h3 className="text-sm font-medium text-slate-900">No active bot errors</h3>
        <p className="mt-1 text-sm text-slate-500">All bot integrations are operating nominally.</p>
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-slate-200 bg-white shadow-sm overflow-hidden">
      <div className="border-b border-slate-200 bg-slate-50/50 px-5 py-4 flex items-center justify-between">
        <h3 className="font-semibold text-slate-900 flex items-center gap-2">
          <AlertCircle className="size-4 text-rose-500" />
          Bot Error Feed
        </h3>
        <span className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium ring-1 ring-inset bg-rose-50 text-rose-700 ring-rose-200">
          {errored.length} Errors
        </span>
      </div>
      <div className="p-5 space-y-4 max-h-[500px] overflow-y-auto custom-scrollbar">
        {errored.map((bot) => (
          <div key={bot.id} className="rounded-xl border border-rose-200 bg-rose-50/50 p-4">
            <div className="flex items-start justify-between gap-4">
              <div className="space-y-1 min-w-0">
                <div className="flex items-center gap-2">
                  <h4 className="font-medium text-rose-900 truncate">{bot.name}</h4>
                  <span className={cn(
                    "inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-medium capitalize",
                    bot.status === "active" ? "bg-emerald-100 text-emerald-700" :
                    bot.status === "inactive" ? "bg-slate-200 text-slate-700" :
                    "bg-rose-100 text-rose-700"
                  )}>
                    {bot.status}
                  </span>
                </div>
                <p className="text-sm text-rose-700/90 leading-relaxed whitespace-pre-wrap">{bot.last_error}</p>
                <div className="flex items-center gap-4 mt-3 text-xs text-rose-600/70 font-medium">
                  <span className="flex items-center gap-1.5">
                    <Building2 className="size-3.5" />
                    Company: {bot.owner_username || bot.owner_id}
                  </span>
                  <span className="flex items-center gap-1.5">
                    <Hash className="size-3.5" />
                    Project: {bot.project_id}
                  </span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
