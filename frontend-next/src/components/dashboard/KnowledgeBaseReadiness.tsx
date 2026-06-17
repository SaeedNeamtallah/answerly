import Link from "next/link";
import { ArrowRight, Info, FileText, Package, AlertCircle } from "lucide-react";

import { BotIntegration } from "@/lib/types/bot";
import { Project } from "@/lib/types/project";
import { EmptyState } from "@/components/shared/EmptyState";

export function KnowledgeBaseReadiness({ projects, bots }: { projects: Project[]; bots: BotIntegration[] }) {
  if (projects.length === 0) {
    return (
      <EmptyState
        title="Create your first knowledge base"
        description="Projects from the backend are presented here as customer-facing knowledge bases."
        actionLabel="Create knowledge base"
        actionHref="/knowledge-bases"
      />
    );
  }

  const bgColors = [
    "bg-blue-100 text-blue-600",
    "bg-purple-100 text-purple-600",
    "bg-emerald-100 text-emerald-600",
    "bg-orange-100 text-orange-600",
    "bg-pink-100 text-pink-600",
    "bg-teal-100 text-teal-600",
  ];

  return (
    <div className="flex flex-col rounded-2xl border border-slate-100 bg-white shadow-[0_2px_10px_rgba(0,0,0,0.02)]">
      <div className="flex items-center justify-between p-6 pb-4">
        <h3 className="text-lg font-semibold text-slate-900">Knowledge Base Readiness</h3>
        <Link href="/knowledge-bases" className="flex items-center text-sm font-medium text-blue-600 hover:text-blue-700">
          View all <ArrowRight className="ml-1 size-4" />
        </Link>
      </div>
      
      <div className="w-full overflow-x-auto px-6 pb-6">
        <table className="w-full min-w-[700px] text-left text-sm">
          <thead>
            <tr className="border-b border-slate-100 text-slate-500">
              <th className="pb-3 font-medium w-[250px]">Knowledge Base</th>
              <th className="pb-3 font-medium text-center">Linked Bots</th>
              <th className="pb-3 font-medium text-right">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-50">
            {projects.slice(0, 5).map((project, idx) => {
              const linkedBots = bots.filter((bot) => bot.project_id === project.id).length;
              const status = linkedBots > 0 ? "Ready" : "Needs Bot";
              const statusColor = linkedBots > 0 ? "text-emerald-500" : "text-orange-500";
              const bg = bgColors[idx % bgColors.length];
              const initials = project.name.substring(0, 1).toUpperCase();

              return (
                <tr key={project.id} className="group transition-colors hover:bg-slate-50/50">
                  <td className="py-3">
                    <Link href={`/knowledge-bases/${project.id}`} className="flex items-center gap-3 group-hover:opacity-80">
                      <div className={`flex size-9 shrink-0 items-center justify-center rounded-lg text-xs font-semibold ${bg}`}>
                        {initials}
                      </div>
                      <div className="flex flex-col">
                        <span className="font-semibold text-slate-900 truncate max-w-[150px]" title={project.name}>{project.name}</span>
                        <span className="text-xs text-slate-500">{project.created_at ? new Date(project.created_at).toLocaleDateString() : 'New'}</span>
                      </div>
                    </Link>
                  </td>
                  <td className="py-3 text-center">
                    <span className="inline-flex items-center justify-center rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-700">
                      {linkedBots}
                    </span>
                  </td>
                  <td className="py-3 text-right">
                    <div className="flex items-center justify-end gap-1.5">
                      <div className={`size-1.5 rounded-full ${statusColor === "text-emerald-500" ? "bg-emerald-500" : "bg-orange-500"}`} />
                      <span className={`text-xs font-semibold ${statusColor}`}>{status}</span>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
