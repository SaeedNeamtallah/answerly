import Link from "next/link";
import { ArrowRight, Send } from "lucide-react";

import { Conversation } from "@/lib/types/conversation";
import { formatRelativeDate } from "@/lib/utils/dates";
import { EmptyState } from "@/components/shared/EmptyState";

export function RecentConversations({ conversations }: { conversations: Conversation[] }) {
  if (conversations.length === 0) {
    return (
      <EmptyState
        title="No conversations yet"
        description="Customer chats will appear here once your Telegram bot starts receiving messages."
      />
    );
  }

  const bgColors = [
    "bg-purple-100 text-purple-600",
    "bg-orange-100 text-orange-600",
    "bg-emerald-100 text-emerald-600",
    "bg-pink-100 text-pink-600",
    "bg-blue-100 text-blue-600",
  ];

  return (
    <div className="flex flex-col rounded-2xl border border-slate-100 bg-white shadow-[0_2px_10px_rgba(0,0,0,0.02)]">
      <div className="flex items-center justify-between p-6 pb-4">
        <h3 className="text-lg font-semibold text-slate-900">Recent Conversations</h3>
        <Link href="/conversations" className="flex items-center text-sm font-medium text-blue-600 hover:text-blue-700">
          View all <ArrowRight className="ml-1 size-4" />
        </Link>
      </div>
      
      <div className="w-full overflow-x-auto px-6 pb-6">
        <table className="w-full min-w-[600px] text-left text-sm">
          <thead>
            <tr className="border-b border-slate-100 text-slate-500">
              <th className="pb-3 font-medium">Customer</th>
              <th className="pb-3 font-medium">Bot</th>
              <th className="pb-3 font-medium">Last Activity</th>
              <th className="pb-3 font-medium text-right">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-50">
            {conversations.slice(0, 5).map((convo, idx) => {
              const bg = bgColors[idx % bgColors.length];
              const initials = (convo.customer_label || "U").substring(0, 2).toUpperCase();
              const isNeedsHuman = convo.needs_human;
              const statusDisplay = isNeedsHuman ? "Needs Human" : convo.status;
              let toneClass = "bg-slate-100 text-slate-600";
              if (statusDisplay === "Needs Human") toneClass = "bg-orange-50 text-orange-600";
              else if (statusDisplay === "open") toneClass = "bg-emerald-50 text-emerald-600";
              
              return (
                <tr key={convo.id} className="group transition-colors hover:bg-slate-50/50">
                  <td className="py-3">
                    <Link href={`/conversations/${convo.id}`} className="flex items-center gap-3 group-hover:opacity-80">
                      <div className={`flex size-9 shrink-0 items-center justify-center rounded-full text-xs font-semibold ${bg}`}>
                        {initials}
                      </div>
                      <div className="flex flex-col">
                        <span className="font-semibold text-slate-900 truncate max-w-[150px]">{convo.customer_label}</span>
                        <span className="text-xs text-slate-500 truncate max-w-[150px]">Customer #{convo.id.toString().substring(0, 6)}</span>
                      </div>
                    </Link>
                  </td>
                  <td className="py-3">
                    <div className="flex size-7 items-center justify-center rounded-full bg-blue-100 text-blue-600">
                      <Send className="size-3.5 -ml-0.5" />
                    </div>
                  </td>
                  <td className="py-3 text-slate-500">
                    {formatRelativeDate(convo.last_message_at)}
                  </td>
                  <td className="py-3 text-right">
                    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold capitalize ${toneClass}`}>
                      {statusDisplay}
                    </span>
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
