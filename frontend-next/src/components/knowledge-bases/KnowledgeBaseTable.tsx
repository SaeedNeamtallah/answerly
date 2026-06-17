import Link from "next/link";
import { ExternalLink, MessageSquareText, Upload, Link as LinkIcon, Trash2 } from "lucide-react";

import { Project } from "@/lib/types/project";
import { BotIntegration } from "@/lib/types/bot";
import { formatRelativeDate } from "@/lib/utils/dates";
import { cn } from "@/lib/utils/cn";

export function KnowledgeBaseTable({ projects, bots = [] }: { projects: Project[], bots?: BotIntegration[] }) {
  return (
    <div className="w-full bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left">
          <thead className="bg-slate-50/50 border-b border-slate-200 text-slate-500 font-medium">
            <tr>
              <th className="px-6 py-4 font-medium">
                Knowledge Base 
              </th>
              <th className="px-6 py-4 font-medium">Last Updated</th>
              <th className="px-6 py-4 font-medium">Linked Bots</th>
              <th className="px-6 py-4 font-medium">Status</th>
              <th className="px-6 py-4 font-medium text-center">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {projects.map((project, index) => {
              const colors = [
                "bg-indigo-500", "bg-purple-500", "bg-amber-500", "bg-rose-500", "bg-cyan-500"
              ];
              const iconColor = colors[index % colors.length];

              const linkedBots = bots.filter((b) => b.project_id === project.id);
              const statusLabel = linkedBots.length > 0 ? "Ready" : "Needs Bot";
              const statusColor = linkedBots.length > 0 ? "text-emerald-600 bg-emerald-50 ring-emerald-200" : "text-amber-600 bg-amber-50 ring-amber-200";

              return (
                <tr key={project.id} className="hover:bg-slate-50/80 transition-colors group">
                  <td className="px-6 py-4">
                    <div className="flex items-start gap-4">
                      <div className={cn("flex size-10 items-center justify-center rounded-xl text-white shadow-sm shrink-0", iconColor)}>
                        {index % 2 === 0 ? (
                          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/></svg>
                        ) : (
                          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect width="18" height="18" x="3" y="3" rx="2"/><path d="M7 7h.01"/><path d="M17 7h.01"/><path d="M7 17h.01"/><path d="M17 17h.01"/></svg>
                        )}
                      </div>
                      <div className="min-w-0">
                        <div className="font-semibold text-slate-900 truncate">{project.name}</div>
                        <div className="text-xs text-slate-500 mt-1 line-clamp-1 max-w-[200px]">{project.description || "Company policies, procedures, and docs"}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-slate-900 font-medium">{formatRelativeDate(project.updated_at || project.created_at)}</div>
                  </td>
                  <td className="px-6 py-4">
                    {linkedBots.length > 0 ? (
                      <div className="flex items-center -space-x-2">
                        {linkedBots.slice(0, 3).map((bot, i) => (
                          <div key={bot.id} className="size-8 rounded-full border-2 border-white bg-indigo-100 text-indigo-600 flex items-center justify-center shadow-sm z-10" style={{ zIndex: 10 - i }} title={bot.name}>
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 8V4H8"/><rect width="16" height="12" x="4" y="8" rx="2"/><path d="M2 14h2"/><path d="M20 14h2"/><path d="M15 13v2"/><path d="M9 13v2"/></svg>
                          </div>
                        ))}
                        {linkedBots.length > 3 && (
                          <div className="size-8 rounded-full border-2 border-white bg-slate-100 text-slate-600 flex items-center justify-center text-xs font-medium shadow-sm z-0">
                            +{linkedBots.length - 3}
                          </div>
                        )}
                      </div>
                    ) : (
                      <span className="text-slate-400">—</span>
                    )}
                  </td>
                  <td className="px-6 py-4">
                    <span className={cn("inline-flex items-center px-2 py-1 rounded-md text-xs font-medium ring-1 ring-inset", statusColor)}>
                      {statusLabel}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <div className="flex items-center justify-center gap-1.5">
                      <Link href={`/knowledge-bases/${project.id}`} className="inline-flex h-8 px-3 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-700 shadow-sm hover:bg-slate-50 transition-colors text-sm font-medium" title="Open Knowledge Base">
                        Open
                      </Link>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <div className="px-6 py-4 border-t border-slate-200 bg-slate-50/50 flex items-center justify-between">
        <span className="text-sm text-slate-500">Showing 1 to {projects.length} of {projects.length} knowledge bases</span>
        <div className="flex items-center gap-1">
          <button className="px-3 py-1 text-sm text-slate-400 cursor-not-allowed">&lt;</button>
          <button className="px-3 py-1 text-sm bg-indigo-50 text-indigo-600 font-medium rounded-md">1</button>
          <button className="px-3 py-1 text-sm text-slate-400 cursor-not-allowed">&gt;</button>
        </div>
      </div>
    </div>
  );
}
