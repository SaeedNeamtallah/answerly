import Link from "next/link";
import { type ReactNode } from "react";
import { ExternalLink, Building2, LayoutGrid, Bot, MessageSquareText } from "lucide-react";

import { AdminCompany } from "@/lib/types/admin";
import { cn } from "@/lib/utils/cn";

export function CompaniesTable({
  companies,
  renderActions,
}: {
  companies: AdminCompany[];
  renderActions?: (company: AdminCompany) => ReactNode;
}) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white shadow-sm overflow-hidden">
      <div className="border-b border-slate-200 bg-slate-50/50 px-5 py-4 flex items-center justify-between">
        <h3 className="font-semibold text-slate-900 flex items-center gap-2">
          <Building2 className="size-4 text-indigo-500" />
          Platform Companies
        </h3>
        <span className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium bg-slate-100 text-slate-600">
          {companies.length} Total
        </span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left text-slate-600">
          <thead className="text-xs text-slate-500 bg-slate-50/80 border-b border-slate-200 uppercase font-semibold">
            <tr>
              <th className="px-5 py-4">Company</th>
              <th className="px-5 py-4">Role</th>
              <th className="px-5 py-4">Metrics</th>
              <th className="px-5 py-4">Status</th>
              <th className="px-5 py-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 bg-white">
            {companies.map((company) => (
              <tr key={company.id} className="hover:bg-slate-50/50 transition-colors">
                <td className="px-5 py-4">
                  <div className="flex items-center gap-3">
                    <div className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-indigo-50 text-indigo-600">
                      <Building2 className="size-4" />
                    </div>
                    <div>
                      <p className="font-medium text-slate-900">{company.company_name || company.username}</p>
                      {company.company_name && (
                        <p className="text-xs text-slate-500 mt-0.5">{company.username}</p>
                      )}
                    </div>
                  </div>
                </td>
                <td className="px-5 py-4">
                  <span className={cn(
                    "inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium capitalize",
                    company.role === "platform_owner" ? "bg-purple-50 text-purple-700 ring-1 ring-inset ring-purple-200" :
                    "bg-slate-100 text-slate-700 ring-1 ring-inset ring-slate-200"
                  )}>
                    {company.role.replace(/_/g, " ")}
                  </span>
                </td>
                <td className="px-5 py-4">
                  <div className="flex items-center gap-4 text-xs font-medium text-slate-500">
                    <div className="flex items-center gap-1.5" title="Projects">
                      <LayoutGrid className="size-3.5 text-slate-400" />
                      {company.project_count || 0}
                    </div>
                    <div className="flex items-center gap-1.5" title="Bots">
                      <Bot className="size-3.5 text-slate-400" />
                      {company.bot_count || 0}
                    </div>
                    <div className="flex items-center gap-1.5" title="Conversations">
                      <MessageSquareText className="size-3.5 text-slate-400" />
                      {company.conversation_count || 0}
                    </div>
                  </div>
                </td>
                <td className="px-5 py-4">
                  <span className={cn(
                    "inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium capitalize",
                    company.status === "active" ? "bg-emerald-50 text-emerald-700 ring-1 ring-inset ring-emerald-200" :
                    "bg-slate-100 text-slate-700 ring-1 ring-inset ring-slate-200"
                  )}>
                    {company.status}
                  </span>
                </td>
                <td className="px-5 py-4 text-right">
                  <div className="flex items-center justify-end gap-2">
                    <Link
                      href={`/admin/companies/${company.id}`}
                      className="inline-flex items-center justify-center rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-600 shadow-sm hover:bg-slate-50 hover:text-slate-900 transition-colors"
                    >
                      <ExternalLink className="mr-1.5 size-3" />
                      Details
                    </Link>
                    {renderActions?.(company)}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {companies.length === 0 && (
          <div className="p-8 text-center text-sm text-slate-500">
            No companies found.
          </div>
        )}
      </div>
    </div>
  );
}
