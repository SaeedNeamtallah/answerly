import Link from "next/link";
import { MoreHorizontal, MessageSquare } from "lucide-react";

import { WhatsAppIntegration } from "@/lib/api/whatsappIntegrations";
import { Project } from "@/lib/types/project";
import { cn } from "@/lib/utils/cn";

export function WhatsAppBotTable({ bots, projects }: { bots: WhatsAppIntegration[], projects: Project[] }) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case "active":
      case "connected": return "text-emerald-500 bg-emerald-50 ring-emerald-200";
      case "error":
      case "expired": return "text-rose-500 bg-rose-50 ring-rose-200";
      case "pending":
      case "initializing":
      case "qr_ready": return "text-indigo-500 bg-indigo-50 ring-indigo-200";
      case "disconnected":
      case "inactive":
      case "disabled":
      default: return "text-slate-500 bg-slate-50 ring-slate-200";
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case "active":
      case "connected": return "Online";
      case "error": return "With Issues";
      case "expired": return "QR Expired";
      case "pending": return "Setup Pending";
      case "initializing": return "Connecting";
      case "qr_ready": return "Scan QR";
      case "disconnected": return "Offline";
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
              <th className="px-6 py-4 font-medium">WhatsApp Bot</th>
              <th className="px-6 py-4 font-medium">Phone Number</th>
              <th className="px-6 py-4 font-medium">Knowledge Base</th>
              <th className="px-6 py-4 font-medium">Status</th>
              <th className="px-6 py-4 font-medium text-center">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {bots.map((bot) => {
              const project = projects.find((p) => p.id === bot.project_id);
              
              const colors = [
                "bg-emerald-500", "bg-teal-500", "bg-green-500"
              ];
              const avatarColor = colors[bot.id % colors.length];

              return (
                <tr key={bot.id} className="hover:bg-slate-50/80 transition-colors group">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className={cn("flex size-9 items-center justify-center rounded-full text-white shadow-sm", avatarColor)}>
                        <MessageSquare className="size-4" />
                      </div>
                      <div>
                        <div className="font-medium text-slate-900">{bot.name}</div>
                        <div className="text-xs text-slate-500 mt-0.5">{bot.human_handoff_enabled ? "Human handoff enabled" : "Automated only"}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className="text-slate-600 font-medium">
                      {bot.phone_number ? bot.phone_number : "Not linked"}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="font-medium text-slate-700">{project?.name || "Unknown KB"}</div>
                  </td>
                  <td className="px-6 py-4">
                    <span className={cn("inline-flex items-center px-2 py-1 rounded-md text-xs font-medium ring-1 ring-inset", getStatusColor(bot.status))}>
                      {getStatusText(bot.status)}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <Link href={`/whatsapp-bots/${bot.id}`} className="inline-flex size-8 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-500 shadow-sm hover:bg-slate-50 hover:text-slate-900 transition-colors">
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
