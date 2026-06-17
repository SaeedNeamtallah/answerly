import Link from "next/link";
import { ChevronRight, MessageCircle, UserRoundCheck, Bot } from "lucide-react";

import { Conversation } from "@/lib/types/conversation";
import { EmptyState } from "@/components/shared/EmptyState";
import { formatRelativeDate } from "@/lib/utils/dates";
import { cn } from "@/lib/utils/cn";

export function ConversationList({ conversations }: { conversations: Conversation[] }) {
  if (conversations.length === 0) {
    return <EmptyState title="No conversations" description="Customer conversations will appear here." />;
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "open": return "bg-indigo-50 text-indigo-700 ring-indigo-200";
      case "resolved": return "bg-emerald-50 text-emerald-700 ring-emerald-200";
      case "escalated": return "bg-amber-50 text-amber-700 ring-amber-200";
      default: return "bg-slate-50 text-slate-700 ring-slate-200";
    }
  };

  return (
    <div className="grid gap-3">
      {conversations.map((conversation, index) => {
        const colors = [
          "bg-blue-500", "bg-purple-500", "bg-indigo-500", "bg-emerald-500", "bg-rose-500", "bg-cyan-500", "bg-amber-500"
        ];
        const avatarColor = colors[conversation.id % colors.length];

        return (
          <Link
            key={conversation.id}
            href={`/conversations/${conversation.id}`}
            className="group block rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition-all hover:border-indigo-300 hover:shadow-md hover:-translate-y-0.5"
          >
            <div className="flex items-center justify-between gap-4">
              <div className="flex min-w-0 items-center gap-4">
                <div className="relative">
                  <span className={cn("flex size-12 shrink-0 items-center justify-center rounded-full text-white shadow-sm", avatarColor)}>
                    <span className="font-semibold text-lg">{conversation.customer_label.charAt(0).toUpperCase()}</span>
                  </span>
                  {conversation.status === "open" && (
                    <span className="absolute bottom-0 right-0 size-3.5 rounded-full border-2 border-white bg-emerald-500" />
                  )}
                </div>
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="truncate font-semibold text-slate-900 text-base">{conversation.customer_label}</p>
                    {conversation.needs_human && (
                      <span className="inline-flex items-center gap-1 rounded-full bg-rose-50 px-2 py-0.5 text-xs font-medium text-rose-600 ring-1 ring-inset ring-rose-200">
                        <UserRoundCheck className="size-3" />
                        Human requested
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-3 mt-1.5">
                    <p className="flex items-center gap-1.5 text-sm text-slate-500">
                      <Bot className="size-3.5" />
                      <span className="truncate">{conversation.bot_name || `Bot #${conversation.bot_integration_id}`}</span>
                    </p>
                    <span className="text-slate-300">•</span>
                    <p className="text-sm text-slate-500">
                      {formatRelativeDate(conversation.last_message_at)}
                    </p>
                  </div>
                </div>
              </div>
              <div className="flex shrink-0 items-center gap-4">
                <span className={cn("inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium ring-1 ring-inset capitalize", getStatusColor(conversation.status))}>
                  {conversation.status}
                </span>
                <div className="flex size-8 items-center justify-center rounded-full bg-slate-50 text-slate-400 group-hover:bg-indigo-50 group-hover:text-indigo-600 transition-colors">
                  <ChevronRight className="size-4 transition-transform group-hover:translate-x-0.5" />
                </div>
              </div>
            </div>
          </Link>
        );
      })}
    </div>
  );
}
